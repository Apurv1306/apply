import os, threading, time, json
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64

# Android permissions & storage
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

# Import your face recognition backend
from face_backend.face_recognition import FaceAppBackend

class FaceAppHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for face recognition API"""
    
    def __init__(self, face_backend, *args, **kwargs):
        self.face_backend = face_backend
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"FaceApp Backend is running on Android!")
            
        elif parsed_path.path == '/get_last_recognized':
            result = self.face_backend.get_last_recognized_info()
            self.send_json_response(result)
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error_response("Invalid JSON data")
            return
            
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/process_frame':
            if 'image' not in data:
                self.send_error_response("No image data provided")
                return
            frame_data_b64 = data['image'].split(',')[1] if ',' in data['image'] else data['image']
            result = self.face_backend.process_frame(frame_data_b64)
            self.send_json_response(result)
            
        elif parsed_path.path == '/register_user':
            name = data.get('name')
            emp_id = data.get('emp_id')  
            email = data.get('email')
            if not all([name, emp_id, email]):
                self.send_error_response("Missing name, employee ID, or email")
                return
            if "@" not in email:
                self.send_error_response("Invalid email format")
                return
            self.face_backend.register_user_email(emp_id, email)
            result = self.face_backend.start_capture_samples(name, emp_id, updating=False, sample_count=10)
            self.send_json_response(result)
            
        elif parsed_path.path == '/send_otp':
            emp_id = data.get('emp_id')
            email = data.get('email')
            name = data.get('name')
            if not all([emp_id, email]):
                self.send_error_response("Missing employee ID or email")
                return
            result = self.face_backend.send_otp_flow(emp_id, email, name)
            self.send_json_response(result)
            
        elif parsed_path.path == '/verify_otp':
            emp_id = data.get('emp_id')
            otp = data.get('otp')
            if not all([emp_id, otp]):
                self.send_error_response("Missing employee ID or OTP")
                return
            result = self.face_backend.verify_otp(emp_id, otp)
            self.send_json_response(result)
            
        elif parsed_path.path == '/get_user_email':
            emp_id = data.get('emp_id')
            if not emp_id:
                self.send_error_response("Missing employee ID")
                return
            result = self.face_backend.get_user_email(emp_id)
            self.send_json_response(result)
            
        elif parsed_path.path == '/start_update_capture':
            name = data.get('name')
            emp_id = data.get('emp_id')
            result = self.face_backend.start_capture_samples(name, emp_id, updating=True, sample_count=5)
            self.send_json_response(result)
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json_response(self, data):
        """Send JSON response"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response)
        
    def send_error_response(self, message):
        """Send error response"""
        self.send_json_response({"status": "error", "message": message})

class FaceAppUI(App):
    def build(self):
        if ANDROID:
            self.request_android_permissions()
            self.setup_android_storage()

        # Initialize face recognition backend
        self.face_backend = FaceAppBackend()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.status_label = Label(text='Server: Stopped', size_hint_y=0.3)
        layout.add_widget(self.status_label)
        
        self.ip_label = Label(text='Start server to see IP', size_hint_y=0.3)
        layout.add_widget(self.ip_label)

        btn_layout = BoxLayout(size_hint_y=0.4, spacing=10)
        self.start_btn = Button(text='Start Server')
        self.stop_btn = Button(text='Stop Server', disabled=True)
        self.start_btn.bind(on_press=self.start_server)
        self.stop_btn.bind(on_press=self.stop_server)
        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.stop_btn)
        layout.add_widget(btn_layout)

        return layout

    def request_android_permissions(self):
        request_permissions([
            Permission.CAMERA,
            Permission.INTERNET, 
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.ACCESS_NETWORK_STATE,
            Permission.ACCESS_WIFI_STATE
        ])

    def setup_android_storage(self):
        base = primary_external_storage_path()
        app_dir = os.path.join(base, "FaceApp")
        known = os.path.join(app_dir, "known_faces")
        Path(known).mkdir(parents=True, exist_ok=True)
        self.face_backend.known_faces_dir = known

    def start_server(self, _):
        def create_handler(*args, **kwargs):
            return FaceAppHTTPHandler(self.face_backend, *args, **kwargs)
        
        self.server = HTTPServer(('0.0.0.0', 5000), create_handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.status_label.text = 'Server: Running ✓'
        self.ip_label.text = 'Access: http://<PHONE_IP>:5000'

    def stop_server(self, _):
        if hasattr(self, 'server'):
            self.server.shutdown()
            self.server.server_close()
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.status_label.text = 'Server: Stopped'
        self.ip_label.text = 'Start server to see IP'

if __name__ == '__main__':
    FaceAppUI().run()

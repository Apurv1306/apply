cat > app/main.py <<'EOF'
import os, threading
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

# Android permissions & storage
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

# Import your Flask backend
from face_backend.app import app as flask_app, face_app_backend

class FaceAppUI(App):
    def build(self):
        if ANDROID:
            self.request_android_permissions()
            self.setup_android_storage()

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.status_label = Label(text='Server: Stopped', size_hint_y=0.2)
        layout.add_widget(self.status_label)
        self.ip_label = Label(text='Start to see IP', size_hint_y=0.2)
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
        face_app_backend.known_faces_dir = known

    def start_server(self, _):
        self.server_thread = threading.Thread(target=self.run_flask, daemon=True)
        self.server_thread.start()
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.status_label.text = 'Server: Starting…'
        Clock.schedule_once(self.update_status, 2)

    def stop_server(self, _):
        import requests
        try:
            requests.post('http://127.0.0.1:5000/shutdown', timeout=2)
        except:
            pass
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.status_label.text = 'Server: Stopped'
        self.ip_label.text = 'Start to see IP'

    def run_flask(self):
        @flask_app.route('/shutdown', methods=['POST'])
        def _shutdown():
            func = __import__('werkzeug').serving.request.environ.get('werkzeug.server.shutdown')
            if func: func()
            return 'OK'
        flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    def update_status(self, dt):
        self.status_label.text = 'Server: Running ✓'
        self.ip_label.text = 'Access: http://<PHONE_IP>:5000'

if __name__ == '__main__':
    FaceAppUI().run()
EOF

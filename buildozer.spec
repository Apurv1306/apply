[app]
title = FaceApp
package.name = faceapp
package.domain = com.example
source.dir = app
source.include_exts = py,png,jpg,kv,xml,json
version = 1.0

# ✅ CRITICAL FIX: Pin exact versions for Flask ecosystem compatibility
requirements = python3,kivy==2.2.1,flask==2.3.3,flask-cors==4.0.0,werkzeug==2.3.7,jinja2==3.1.2,markupsafe==2.1.3,itsdangerous==2.1.2,click==8.1.7,opencv-python==4.8.1.78,numpy,requests==2.31.0,pillow==10.0.1,pyjnius,android

orientation = portrait
fullscreen = 0

# ✅ Updated NDK settings for compatibility
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.sdk = 33
android.ndk = 25b

android.permissions = CAMERA,INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE
android.copy_libs = 1

[buildozer]
warn_on_root = 0
log_level = 2

#!/usr/bin/env python3

import subprocess
import sys
import os

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        # pip is not available, try alternative
        try:
            subprocess.check_call(["easy_install", package])
            return True
        except:
            return False

# Essential packages for the app
packages = [
    "flask",
    "flask-socketio", 
    "ffmpeg-python",
    "opencv-python",
    "librosa",
    "yt-dlp",
    "google-api-python-client",
    "google-auth-httplib2", 
    "google-auth-oauthlib",
    "google-auth",
    "pandas",
    "colorama",
    "python-dateutil",
    "numpy",
    "scipy"
]

print("🎯 Installing Clippy dependencies...")
print("=" * 50)

failed_packages = []
for package in packages:
    print(f"Installing {package}...")
    if install_package(package):
        print(f"✅ {package} installed successfully")
    else:
        print(f"❌ Failed to install {package}")
        failed_packages.append(package)

print("\n" + "=" * 50)
if failed_packages:
    print(f"❌ Failed to install: {', '.join(failed_packages)}")
    print("Try running this script with different Python environment")
else:
    print("✅ All packages installed successfully!")
    print("🚀 You can now run: python app.py")

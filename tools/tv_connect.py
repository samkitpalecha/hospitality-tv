#!/usr/bin/env python3
"""
Pure-Python Wireless ADB connector for Smart TVs.
No adb binary or Android SDK installation required.
"""

import os
import sys
import time
import socket

try:
    from adb_shell.adb_device import AdbDeviceTcp
    from adb_shell.auth.keygen import keygen
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
except ImportError:
    sys.exit("Missing dependencies. Run: pip install -r tools/requirements.txt")

KEY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".adbkey")
KEY_PRIV = os.path.join(KEY_DIR, "adbkey")
KEY_PUB = os.path.join(KEY_DIR, "adbkey.pub")

def get_signer():
    os.makedirs(KEY_DIR, exist_ok=True)
    if not os.path.exists(KEY_PRIV):
        print("Generating local ADB authentication key pair...")
        keygen(KEY_PRIV)
    with open(KEY_PRIV, "r") as f:
        priv = f.read()
    with open(KEY_PUB, "r") as f:
        pub = f.read()
    return PythonRSASigner(pub, priv)

def connect(host, port=5555, timeout=10.0):
    signer = get_signer()
    dev = AdbDeviceTcp(host, port, default_transport_timeout_s=timeout)
    print(f"Connecting to TV at {host}:{port}...")
    try:
        dev.connect(rsa_keys=[signer], auth_timeout_s=timeout)
        return dev
    except Exception as e:
        sys.exit(f"Connection failed: {e}\nEnsure your TV has Network ADB enabled and you approved the prompt on the screen.")

def push_file(dev, local_path, remote_path):
    if not os.path.exists(local_path):
        sys.exit(f"Local file not found: {local_path}")
    print(f"Pushing {os.path.basename(local_path)} to TV...")
    dev.push(local_path, remote_path)

def pull_file(dev, remote_path, local_path):
    os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
    dev.pull(remote_path, local_path)

def screenshot(dev, local_png_path):
    remote = "/data/local/tmp/hospitality-shot.png"
    dev.shell(f"rm -f {remote}; screencap -p {remote}")
    pull_file(dev, remote, local_png_path)
    dev.shell(f"rm -f {remote}")
    print(f"Screenshot saved to {local_png_path}")

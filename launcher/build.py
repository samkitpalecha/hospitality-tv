#!/usr/bin/env python3
"""
Hospitality TV - Zero-Gradle Instant APK Builder
Builds a production-ready, signed APK in ~2 seconds using Android command-line tools.
"""

import os
import sys
import shutil
import subprocess
import zipfile

def find_java():
    if "JAVA_HOME" in os.environ and os.path.exists(os.environ["JAVA_HOME"]):
        return os.environ["JAVA_HOME"]
    # Check default known locations
    candidates = [
        r"C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot",
        r"C:\Program Files\Java\jdk-17",
        r"C:\Program Files\Android\Android Studio\jbr",
        "/Library/Java/JavaVirtualMachines",
        "/usr/lib/jvm/default-java"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    # Try looking for javac in PATH
    javac = shutil.which("javac")
    if javac:
        return os.path.dirname(os.path.dirname(javac))
    return None

def find_android_sdk():
    candidates = [
        os.environ.get("ANDROID_HOME"),
        os.environ.get("ANDROID_SDK_ROOT"),
        r"C:\Users\samki\.gemini\antigravity\scratch\android-sdk",
        os.path.expanduser("~/AppData/Local/Android/Sdk"),
        os.path.expanduser("~/Library/Android/sdk"),
        "/usr/lib/android-sdk"
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_dir = script_dir
    build_dir = os.path.join(launcher_dir, "build")
    gen_dir = os.path.join(build_dir, "gen")
    classes_dir = os.path.join(build_dir, "classes")
    dex_dir = os.path.join(build_dir, "dex")

    java_home = find_java()
    sdk_dir = find_android_sdk()

    if not java_home:
        sys.exit("Error: Java JDK not found. Please install JDK 11+ or set JAVA_HOME.")
    if not sdk_dir:
        sys.exit("Error: Android SDK not found. Please set ANDROID_HOME or ANDROID_SDK_ROOT.")

    print(f"-> Using Java: {java_home}")
    print(f"-> Using Android SDK: {sdk_dir}")

    # Locate build tools
    bt_dir = os.path.join(sdk_dir, "build-tools")
    if not os.path.exists(bt_dir):
        sys.exit(f"Error: Build tools not found in {bt_dir}")
    versions = sorted(os.listdir(bt_dir), reverse=True)
    if not versions:
        sys.exit("Error: No build-tools version found.")
    bt = os.path.join(bt_dir, versions[0])
    print(f"-> Using Build Tools: {versions[0]}")

    # Locate android.jar
    platforms_dir = os.path.join(sdk_dir, "platforms")
    platforms = sorted([p for p in os.listdir(platforms_dir) if p.startswith("android-")], reverse=True)
    if not platforms:
        sys.exit("Error: No android platform found in platforms/")
    jar = os.path.join(platforms_dir, platforms[0], "android.jar")
    print(f"-> Using Platform: {platforms[0]}")

    os.makedirs(gen_dir, exist_ok=True)
    os.makedirs(classes_dir, exist_ok=True)
    os.makedirs(dex_dir, exist_ok=True)

    env = os.environ.copy()
    env["JAVA_HOME"] = java_home
    env["PATH"] = os.path.join(java_home, "bin") + os.pathsep + env.get("PATH", "")

    is_win = sys.platform.startswith("win")
    aapt2 = os.path.join(bt, "aapt2.exe" if is_win else "aapt2")
    javac = os.path.join(java_home, "bin", "javac.exe" if is_win else "javac")
    d8 = os.path.join(bt, "d8.bat" if is_win else "d8")
    zipalign = os.path.join(bt, "zipalign.exe" if is_win else "zipalign")
    keytool = os.path.join(java_home, "bin", "keytool.exe" if is_win else "keytool")
    apksigner = os.path.join(bt, "apksigner.bat" if is_win else "apksigner")

    print("[1/7] Compiling resources with aapt2...")
    res_zip = os.path.join(build_dir, "res.zip")
    res_dir = os.path.join(launcher_dir, "res")
    subprocess.check_call([aapt2, "compile", "--dir", res_dir, "-o", res_zip], cwd=launcher_dir, env=env)

    print("[2/7] Linking APK with aapt2...")
    base_apk = os.path.join(build_dir, "base.apk")
    manifest = os.path.join(launcher_dir, "AndroidManifest.xml")
    assets_dir = os.path.join(launcher_dir, "assets")

    cmd_link = [
        aapt2, "link",
        "-o", base_apk,
        "-I", jar,
        "--manifest", manifest,
        "--java", gen_dir,
        "-A", assets_dir,
        "--min-sdk-version", "21",
        "--target-sdk-version", "34",
        res_zip
    ]
    subprocess.check_call(cmd_link, cwd=launcher_dir, env=env)

    print("[3/7] Compiling Java sources with javac...")
    java_files = []
    for root, _, files in os.walk(os.path.join(launcher_dir, "src")):
        for f in files:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))
    for root, _, files in os.walk(gen_dir):
        for f in files:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))

    cmd_javac = [
        javac,
        "-nowarn",
        "-Xlint:-options",
        "--release", "11",
        "-classpath", jar,
        "-d", classes_dir
    ] + java_files
    subprocess.check_call(cmd_javac, cwd=launcher_dir, env=env)

    print("[4/7] Dexing classes with d8...")
    class_files = []
    for root, _, files in os.walk(classes_dir):
        for f in files:
            if f.endswith(".class"):
                class_files.append(os.path.join(root, f))

    cmd_d8 = [d8, "--min-api", "21", "--lib", jar, "--output", dex_dir] + class_files
    if is_win:
        cmd_d8 = ["cmd.exe", "/c"] + cmd_d8
    subprocess.check_call(cmd_d8, cwd=launcher_dir, env=env)

    print("[5/7] Packing classes.dex into APK...")
    unsigned_apk = os.path.join(build_dir, "unsigned.apk")
    with open(base_apk, "rb") as fin, open(unsigned_apk, "wb") as fout:
        fout.write(fin.read())

    dex_path = os.path.join(dex_dir, "classes.dex")
    with zipfile.ZipFile(unsigned_apk, "a") as z:
        z.write(dex_path, "classes.dex")

    print("[6/7] Zipaligning APK...")
    aligned_apk = os.path.join(build_dir, "aligned.apk")
    if os.path.exists(aligned_apk):
        os.remove(aligned_apk)
    subprocess.check_call([zipalign, "-f", "4", unsigned_apk, aligned_apk], cwd=launcher_dir, env=env)

    print("[7/7] Signing APK with debug keystore...")
    keystore = os.path.join(build_dir, "debug.keystore")
    if not os.path.exists(keystore):
        cmd_keytool = [
            keytool, "-genkeypair",
            "-keystore", keystore,
            "-storepass", "android",
            "-keypass", "android",
            "-alias", "hospitality",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-dname", "CN=hospitality"
        ]
        subprocess.check_call(cmd_keytool, cwd=launcher_dir, env=env)

    out_apk = os.path.join(build_dir, "hospitality-tv.apk")
    if os.path.exists(out_apk):
        os.remove(out_apk)

    cmd_sign = [apksigner, "sign", "--ks", keystore, "--ks-pass", "pass:android", "--out", out_apk, aligned_apk]
    if is_win:
        cmd_sign = ["cmd.exe", "/c"] + cmd_sign
    subprocess.check_call(cmd_sign, cwd=launcher_dir, env=env)

    size_mb = os.path.getsize(out_apk) / (1024 * 1024)
    print(f"\nSUCCESS: Built {out_apk} ({size_mb:.2f} MB)")
    print("Ready to install on your TV with: python tools/setup_tv.py --install")

if __name__ == "__main__":
    main()

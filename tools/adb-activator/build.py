#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def find_java():
    if "JAVA_HOME" in os.environ and os.path.exists(os.environ["JAVA_HOME"]):
        return os.environ["JAVA_HOME"]
    candidates = [
        r"C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot",
        r"C:\Program Files\Java\jdk-17",
        r"C:\Program Files\Android\Android Studio\jbr",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    javac = shutil.which("javac")
    if javac:
        return os.path.dirname(os.path.dirname(javac))
    return None

def find_android_sdk():
    candidates = [
        r"C:\Users\samki\.gemini\antigravity\scratch\android-sdk",
        os.environ.get("ANDROID_HOME"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(root_dir, "build")
    gen_dir = os.path.join(build_dir, "gen")
    classes_dir = os.path.join(build_dir, "classes")
    dex_dir = os.path.join(build_dir, "dex")

    java_home = find_java()
    sdk_dir = find_android_sdk()

    bt_dir = os.path.join(sdk_dir, "build-tools")
    versions = sorted(os.listdir(bt_dir), reverse=True)
    bt = os.path.join(bt_dir, versions[0])

    platforms_dir = os.path.join(sdk_dir, "platforms")
    platforms = sorted([p for p in os.listdir(platforms_dir) if p.startswith("android-")], reverse=True)
    jar = os.path.join(platforms_dir, platforms[0], "android.jar")

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

    manifest = os.path.join(root_dir, "AndroidManifest.xml")
    res_dir = os.path.join(root_dir, "res")

    print("[1/6] Compiling resources...")
    res_zip = os.path.join(build_dir, "res.zip")
    subprocess.check_call([aapt2, "compile", "--dir", res_dir, "-o", res_zip], cwd=root_dir, env=env)

    print("[2/6] Linking APK with aapt2...")
    base_apk = os.path.join(build_dir, "base.apk")
    subprocess.check_call([
        aapt2, "link",
        "-I", jar,
        "--manifest", manifest,
        "--java", gen_dir,
        "-o", base_apk,
        res_zip,
        "--auto-add-overlay"
    ], cwd=root_dir, env=env)

    print("[3/6] Compiling Java sources...")
    java_files = []
    for d in [gen_dir, os.path.join(root_dir, "src", "main", "java")]:
        for r, _, files in os.walk(d):
            for f in files:
                if f.endswith(".java"):
                    java_files.append(os.path.join(r, f))

    cmd_javac = [
        javac,
        "-encoding", "UTF-8",
        "-nowarn",
        "-Xlint:-options",
        "--release", "11",
        "-classpath", jar,
        "-d", classes_dir
    ] + java_files
    subprocess.check_call(cmd_javac, cwd=root_dir, env=env)

    print("[4/6] Dexing with d8...")
    class_files = []
    for r, _, files in os.walk(classes_dir):
        for f in files:
            if f.endswith(".class"):
                class_files.append(os.path.join(r, f))

    subprocess.check_call([
        d8,
        "--lib", jar,
        "--output", dex_dir,
        "--min-api", "21"
    ] + class_files, cwd=root_dir, env=env)

    print("[5/6] Packaging unsigned APK...")
    unsigned_apk = os.path.join(build_dir, "unsigned.apk")
    shutil.copy(base_apk, unsigned_apk)
    
    # Add classes.dex
    dex_file = os.path.join(dex_dir, "classes.dex")
    import zipfile
    with zipfile.ZipFile(unsigned_apk, 'a', zipfile.ZIP_DEFLATED) as z:
        z.write(dex_file, "classes.dex")

    print("[6/6] Zipaligning and signing...")
    aligned_apk = os.path.join(build_dir, "aligned.apk")
    if os.path.exists(aligned_apk):
        os.remove(aligned_apk)
    subprocess.check_call([zipalign, "-p", "-f", "4", unsigned_apk, aligned_apk], cwd=root_dir, env=env)

    keystore = os.path.join(build_dir, "debug.keystore")
    if not os.path.exists(keystore):
        subprocess.check_call([
            keytool, "-genkeypair",
            "-keystore", keystore,
            "-storepass", "android",
            "-alias", "androiddebugkey",
            "-keypass", "android",
            "-dname", "CN=Android Debug,O=Android,C=US",
            "-validity", "10000",
            "-keyalg", "RSA",
            "-keysize", "2048"
        ], env=env)

    final_apk = os.path.join(build_dir, "AdbActivator.apk")
    if os.path.exists(final_apk):
        os.remove(final_apk)
    shutil.copy(aligned_apk, final_apk)

    subprocess.check_call([
        apksigner, "sign",
        "--ks", keystore,
        "--ks-pass", "pass:android",
        "--ks-key-alias", "androiddebugkey",
        "--key-pass", "pass:android",
        final_apk
    ], cwd=root_dir, env=env)

    print(f"\nSUCCESS! Built: {final_apk} ({os.path.getsize(final_apk):,} bytes)")

if __name__ == "__main__":
    main()

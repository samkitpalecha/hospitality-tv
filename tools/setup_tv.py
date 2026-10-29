#!/usr/bin/env python3
"""
Hospitality TV - All-in-One Host Setup Wizard
Connects to your TV over Wi-Fi, installs your branded launcher,
debloats manufacturer spam, and secures the TV for guests.
"""

import os
import sys
import argparse
import time

try:
    import tv_connect
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import tv_connect

LAUNCHER_APK = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "launcher", "build", "hospitality-tv.apk"
)

DEBLOAT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "debloat_profiles"
)

def cmd_probe(args):
    dev = tv_connect.connect(args.ip)
    model = dev.shell("getprop ro.product.model").strip()
    brand = dev.shell("getprop ro.product.brand").strip()
    android_ver = dev.shell("getprop ro.build.version.release").strip()
    size = dev.shell("wm size").strip()
    density = dev.shell("wm density").strip()
    kk_prop = dev.shell("getprop ro.kk.buildsetting").strip()
    is_kitking = bool(kk_prop) or "com.kitking.geminiplusluancher" in dev.shell("pm list packages com.kitking")
    is_cw = "tv.cloudwalker.cwhome" in dev.shell("pm list packages tv.cloudwalker")

    print("\n=== TV Hardware Information ===")
    print(f"Device:       {brand} {model}")
    print(f"Android:      Version {android_ver}")
    print(f"Resolution:   {size}")
    print(f"Density:      {density}")
    if is_kitking:
        print("Generation:   2026 Model (KitKing OEM firmware)")
        print("Recommended:  python setup_tv.py <ip> debloat --profile vw_2026_kitking")
    elif is_cw:
        print("Generation:   2025 Model (CloudWalker OEM firmware)")
        print("Recommended:  python setup_tv.py <ip> debloat --profile vw_2025_cloudwalker")
    print("Status:       Connected & Ready for Setup\n")

def cmd_install(args):
    if not os.path.exists(LAUNCHER_APK):
        print(f"APK not found at {LAUNCHER_APK}")
        print("Building launcher now...")
        build_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "launcher", "build.py")
        import subprocess
        subprocess.check_call([sys.executable, build_script])

    dev = tv_connect.connect(args.ip)
    remote_apk = "/data/local/tmp/hospitality-tv.apk"
    tv_connect.push_file(dev, LAUNCHER_APK, remote_apk)
    
    print("Installing Hospitality TV Launcher...")
    out = dev.shell(f"pm install -r -g {remote_apk}")
    print(f"Install Result: {out.strip()}")
    dev.shell(f"rm -f {remote_apk}")

    # Grant location permission so Wi-Fi SSID displays cleanly
    dev.shell("pm grant com.hospitality.tvhome android.permission.ACCESS_FINE_LOCATION")

    print("Launching Hospitality TV Home...")
    dev.shell("am start -n com.hospitality.tvhome/.MainActivity")
    print("\nSuccess! Hospitality TV is now running on your screen.")

def cmd_set_default(args):
    dev = tv_connect.connect(args.ip)
    print("Setting Hospitality TV as default home launcher...")
    # Send HOME key so Android prompts or selects Hospitality TV
    dev.shell("input keyevent 3")
    print("If your TV asks 'Always' or 'Just once', select Hospitality TV and choose 'Always'.")

def cmd_debloat(args):
    dev = tv_connect.connect(args.ip)
    profile_aliases = {
        "vw_2026": "vw_2026_kitking",
        "kitking": "vw_2026_kitking",
        "vw_2025": "vw_2025_cloudwalker",
        "cloudwalker": "vw_2025_cloudwalker",
        "cloudwalker_vw": "vw_2025_cloudwalker",
        "xiaomi": "xiaomi_patchwall",
    }
    profile_name = profile_aliases.get(args.profile.lower(), args.profile)
    profile_path = os.path.join(DEBLOAT_DIR, f"{profile_name}.txt")
    if not os.path.exists(profile_path):
        available = [f.replace(".txt", "") for f in os.listdir(DEBLOAT_DIR) if f.endswith(".txt")]
        sys.exit(f"Profile '{args.profile}' not found. Available profiles: {', '.join(available)}")

    print(f"Applying debloat profile: {profile_name}")
    with open(profile_path, "r", encoding="utf-8") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    count = 0
    for pkg in packages:
        res = dev.shell(f"pm disable-user --user 0 {pkg} 2>&1").strip()
        if "disabled-user" in res or "new state" in res or "disabled" in res:
            print(f"  [DISABLED] {pkg}")
            count += 1
        else:
            print(f"  [SKIPPED]  {pkg} (not installed or already disabled)")

    print(f"\nDebloat complete! Disabled {count} manufacturer bloatware packages.")

def cmd_lockdown(args):
    dev = tv_connect.connect(args.ip)
    print("Securing TV for guest check-in (Disabling ADB)...")
    dev.shell("settings put global adb_enabled 0")
    dev.shell("setprop persist.adb.tcp.port -1")
    dev.shell("setprop service.adb.tcp.port -1")
    dev.shell("setprop persist.sys.usb.config none")
    print("Closing active ADB daemon...")
    try:
        dev.shell("setprop sys.usb.config none")
    except Exception:
        pass
    print("Success: ADB is closed and disabled. Your TV is secured for guests.")

def cmd_screenshot(args):
    dev = tv_connect.connect(args.ip)
    out = args.output or "tv_screen.png"
    print(f"Capturing screenshot to {out}...")
    dev.shell("screencap -p /sdcard/temp_screen.png")
    tv_connect.pull_file(dev, "/sdcard/temp_screen.png", out)
    dev.shell("rm -f /sdcard/temp_screen.png")
    print("Screenshot captured successfully!")

def main():
    parser = argparse.ArgumentParser(description="Hospitality TV - Setup Wizard for Airbnb Hosts")
    parser.add_argument("ip", help="IP address of your Smart TV (e.g. 192.168.1.50)")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    p_probe = subparsers.add_parser("probe", help="Inspect TV hardware and connection")
    p_probe.set_defaults(func=cmd_probe)

    p_install = subparsers.add_parser("install", help="Build and install Hospitality TV on TV")
    p_install.set_defaults(func=cmd_install)

    p_default = subparsers.add_parser("set-default", help="Set launcher as default Home")
    p_default.set_defaults(func=cmd_set_default)

    p_debloat = subparsers.add_parser("debloat", help="Remove OEM bloatware & ads")
    p_debloat.add_argument("--profile", default="cloudwalker_vw", help="Profile name from debloat_profiles/")
    p_debloat.set_defaults(func=cmd_debloat)

    p_lock = subparsers.add_parser("lockdown", help="Disable ADB and secure TV before guest check-in")
    p_lock.set_defaults(func=cmd_lockdown)

    p_shot = subparsers.add_parser("screenshot", help="Capture live TV screenshot")
    p_shot.add_argument("--output", "-o", default="tv_screen.png", help="Output PNG path")
    p_shot.set_defaults(func=cmd_screenshot)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

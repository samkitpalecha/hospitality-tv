# 🚀 5-Minute Quickstart Guide for Hosts

This guide walks you through transforming your TV from scratch with zero coding required.

---

## Step 1: Prepare Your Computer

Make sure you have **Python** installed on your laptop (Windows, Mac, or Linux):
1. Download Python from [python.org](https://www.python.org/downloads/) (check *"Add Python to PATH"* during installation).
2. Open your terminal or Command Prompt, navigate to this project, and install the two required tools:
   ```bash
   pip install -r tools/requirements.txt
   ```

---

## Step 2: Enable Network ADB on Your TV

1. Turn on your Smart TV and open **Settings**.
2. Go to **About TV** (or **Device Preferences** → **About**).
3. Scroll down to **Build Number** and click the **OK** button on your remote **7 times** until you see:
   > *"You are now a developer!"*
4. Go back one menu and open **Developer Options**.
5. Turn ON **USB Debugging** and **Network Debugging** (or ADB over Network).
6. Note down your TV's **IP Address** under **Settings** → **Network** (e.g. `192.168.1.50`).

---

## Step 3: Customize Your Property Details

Open [`launcher/res/values/config.xml`](launcher/res/values/config.xml) with Notepad or any text editor:
- Change `"Welcome to Luxacaves!"` to your own welcome message (e.g., `"Welcome to Villa Pacifica!"`).
- Change `"Luxacaves Boutique Stays"` to your property name.

*(Optional)* If you want to use your own photos for the rotating wallpaper:
```bash
python tools/generate_branding.py --photos-dir ./my_photos --property "VILLA PACIFICA"
```

---

## Step 4: 1-Click Install to Your TV

Run the setup wizard with your TV's IP address:
```bash
python tools/setup_tv.py 192.168.1.50 install
```
A prompt may appear on your TV screen saying *"Allow USB debugging?"* — check *"Always allow from this computer"* and click **OK**.

The script will automatically:
1. Compile your custom branded launcher.
2. Transfer and install it onto your TV.
3. Grant Wi-Fi permissions.
4. Launch the new home screen immediately.

---

## Step 5: Secure Before Guest Check-In

Once you're satisfied with how the TV looks, run the lockdown command:
```bash
python tools/setup_tv.py 192.168.1.50 lockdown
```
This disables remote network debugging, closes port 5555, and ensures that guests cannot tamper with developer settings or connect to the TV.

Enjoy your 5-star guest reviews! ⭐⭐⭐⭐⭐

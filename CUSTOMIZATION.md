# 🎨 Advanced Customization Guide

Hospitality TV was designed to be deeply customizable while remaining ultra-fast and lightweight.

---

## 1. Changing Colors & Glassmorphism

All UI styling is programmatic in [`MainActivity.java`](launcher/src/main/java/com/hospitality/tvhome/MainActivity.java) or configurable in [`styles.xml`](launcher/res/values/styles.xml):

### Accent & Glow Color
When guests highlight apps or tiles, an ambient background backlight glow shifts dynamically:
- To customize the glow intensity or color tint, edit `setGlow(int color)` in `MainActivity.java`.
- Default accent gold: `#E2C48C` (Luxury Champagne Gold).

### Glassmorphic Card Transparency
The dock and inputs dropdown use semi-transparent ARGB gradients:
- Dock backplate: `0x24FFFFFF` (14% white translucent glass).
- Inputs dropdown: `0xF0202228` (94% dark obsidian glass with `0x26FFFFFF` border stroke).

---

## 2. Typography & Fonts

Hospitality TV ships with Google's **Montserrat** font family located in:
`launcher/assets/fonts/`
- `Montserrat-Medium.ttf` (Used for clock AM/PM, dates, greetings, input labels)
- `Montserrat-SemiBold.ttf` (Used for app dock titles and branding badges)

To use your own boutique brand typeface (e.g., Playfair Display, Cinzel, or Helvetica Neue):
1. Replace the `.ttf` files inside `launcher/assets/fonts/`.
2. Keep the file names the same or update the references in `MainActivity.java`:
   ```java
   montserratMedium = Typeface.createFromAsset(getAssets(), "fonts/YourFont-Regular.ttf");
   montserratSemiBold = Typeface.createFromAsset(getAssets(), "fonts/YourFont-Bold.ttf");
   ```

---

## 3. Curated Dock Apps

Find package names for streaming apps installed in your region:

| App | Android Package Name |
| :--- | :--- |
| **YouTube** | `com.google.android.youtube.tv` |
| **Netflix** | `com.netflix.mediaclient` |
| **Prime Video** | `com.amazon.amazonvideo.livingroom` |
| **Disney+ / Hotstar** | `in.startv.hotstar` or `com.disney.disneyplus` |
| **Apple TV** | `com.apple.atve.androidtv.appletv` |
| **Spotify** | `com.spotify.tv.android` |
| **HBO Max / Max** | `com.wbd.stream` |
| **Hulu** | `com.hulu.livingroomplus` |
| **Plex** | `com.plexapp.android` |

Simply add or remove them in [`launcher/res/values/config.xml`](launcher/res/values/config.xml):
```xml
<string-array name="dock_apps">
    <item>com.google.android.youtube.tv</item>
    <item>com.netflix.mediaclient</item>
    <item>com.amazon.amazonvideo.livingroom</item>
    <item>com.spotify.tv.android</item>
    <item>com.apple.atve.androidtv.appletv</item>
</string-array>
```

---

## 4. Direct Hardware Input Switcher

The launcher features direct keycode and `TvInputManager` source switching.
Inside `MainActivity.java` → `showInputs()`:
```java
rows.add(inputRow("HDMI 1", R.drawable.ic_hdmi, () -> switchSource(9, 243)));
rows.add(inputRow("HDMI 2", R.drawable.ic_hdmi, () -> switchSource(10, 244)));
rows.add(inputRow("HDMI 3", R.drawable.ic_hdmi, () -> switchSource(11, 245)));
rows.add(inputRow("AV", R.drawable.ic_av, () -> switchSource(3, 247)));
rows.add(inputRow("Live TV", R.drawable.ic_tv, () -> switchSource(0, 170)));
```

### Standard Android TV Keycodes:
- `KEYCODE_TV_INPUT_HDMI_1` = `243`
- `KEYCODE_TV_INPUT_HDMI_2` = `244`
- `KEYCODE_TV_INPUT_HDMI_3` = `245`
- `KEYCODE_TV_INPUT_HDMI_4` = `246`
- `KEYCODE_TV_INPUT_COMPOSITE_1` (AV) = `247`
- `KEYCODE_TV_INPUT` (Menu) = `178`
- `KEYCODE_TV` (Tuner) = `170`

---

## 5. Wallpaper Rotation Timing

By default, wallpapers crossfade every **20 seconds**.
To change this, edit `wallpaper_interval_seconds` in `config.xml`:
```xml
<integer name="wallpaper_interval_seconds">30</integer>
```
Or specify in seconds: `15`, `30`, `60`, or `120`.

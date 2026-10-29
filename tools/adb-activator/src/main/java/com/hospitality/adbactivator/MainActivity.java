package com.hospitality.adbactivator;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.text.format.Formatter;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URLDecoder;
import java.util.Collections;
import java.util.List;

public class MainActivity extends Activity {

    private TextView tvStatus;
    private TextView tvLog;
    private ScrollView scrollLog;
    private Handler mainHandler;
    private StringBuilder logBuffer = new StringBuilder();
    private ServerSocket serverSocket;
    private boolean serverRunning = false;
    private int httpPort = 8080;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        mainHandler = new Handler(Looper.getMainLooper());

        setupUI();
        startHttpServer();
        autoActivateAdb();
    }

    private void setupUI() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#0F172A"));
        root.setPadding(40, 30, 40, 30);

        // Header Title
        TextView tvTitle = new TextView(this);
        tvTitle.setText("⚡ TV ADB ACTIVATOR & REMOTE CONSOLE");
        tvTitle.setTextColor(Color.parseColor("#38BDF8"));
        tvTitle.setTextSize(26);
        tvTitle.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(tvTitle);

        // Status bar
        tvStatus = new TextView(this);
        tvStatus.setText("Initializing...");
        tvStatus.setTextColor(Color.WHITE);
        tvStatus.setTextSize(18);
        tvStatus.setPadding(0, 10, 0, 20);
        root.addView(tvStatus);

        // Button row 1
        LinearLayout row1 = new LinearLayout(this);
        row1.setOrientation(LinearLayout.HORIZONTAL);
        row1.addView(createTVButton("⚡ Enable ADB (Root/Shell)", v -> runAdbScript()));
        row1.addView(createTVButton("🛠️ Open Dev Options", v -> launchIntent(new Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS))));
        row1.addView(createTVButton("📱 AOSP Dev Dashboard", v -> launchComponent("com.android.settings", "com.android.settings.development.DevelopmentSettingsDashboardActivity")));
        root.addView(row1);

        // Button row 2
        LinearLayout row2 = new LinearLayout(this);
        row2.setOrientation(LinearLayout.HORIZONTAL);
        row2.setPadding(0, 10, 0, 15);
        row2.addView(createTVButton("📺 TV Dev Settings", v -> launchComponent("com.android.tv.settings", "com.android.tv.settings.device.development.DevelopmentSettingsActivity")));
        row2.addView(createTVButton("📶 Wireless Debug (A11+)", v -> launchAction("android.settings.WIRELESS_DEBUGGING_SETTINGS")));
        row2.addView(createTVButton("🏠 Launch Hospitality TV", v -> launchComponent("com.hospitality.tvhome", "com.hospitality.tvhome.MainActivity")));
        root.addView(row2);

        // Live Log Terminal
        TextView tvLogHeader = new TextView(this);
        tvLogHeader.setText("LIVE DIAGNOSTICS & SYSTEM LOG:");
        tvLogHeader.setTextColor(Color.parseColor("#94A3B8"));
        tvLogHeader.setTextSize(14);
        tvLogHeader.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(tvLogHeader);

        scrollLog = new ScrollView(this);
        scrollLog.setBackgroundColor(Color.parseColor("#020617"));
        scrollLog.setPadding(20, 20, 20, 20);

        tvLog = new TextView(this);
        tvLog.setTextColor(Color.parseColor("#4ADE80"));
        tvLog.setTypeface(Typeface.MONOSPACE);
        tvLog.setTextSize(13);
        scrollLog.addView(tvLog);

        LinearLayout.LayoutParams scrollParams = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.0f);
        scrollParams.setMargins(0, 10, 0, 0);
        root.addView(scrollLog, scrollParams);

        setContentView(root);
    }

    private Button createTVButton(String text, View.OnClickListener listener) {
        Button btn = new Button(this);
        btn.setText(text);
        btn.setTextColor(Color.WHITE);
        btn.setTextSize(14);
        btn.setTypeface(Typeface.DEFAULT_BOLD);
        btn.setBackgroundColor(Color.parseColor("#1E293B"));
        btn.setPadding(24, 16, 24, 16);
        btn.setFocusable(true);
        btn.setFocusableInTouchMode(true);
        btn.setOnClickListener(listener);

        btn.setOnFocusChangeListener((v, hasFocus) -> {
            if (hasFocus) {
                btn.setBackgroundColor(Color.parseColor("#0284C7"));
                btn.setScaleX(1.05f);
                btn.setScaleY(1.05f);
            } else {
                btn.setBackgroundColor(Color.parseColor("#1E293B"));
                btn.setScaleX(1.0f);
                btn.setScaleY(1.0f);
            }
        });

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f);
        lp.setMargins(6, 4, 6, 4);
        btn.setLayoutParams(lp);
        return btn;
    }

    private void log(String msg) {
        logBuffer.append(msg).append("\n");
        mainHandler.post(() -> {
            if (tvLog != null) {
                tvLog.setText(logBuffer.toString());
                if (scrollLog != null) {
                    scrollLog.fullScroll(View.FOCUS_DOWN);
                }
            }
        });
    }

    private void updateStatus(String status) {
        mainHandler.post(() -> {
            if (tvStatus != null) {
                tvStatus.setText(status);
            }
        });
    }

    private String getDeviceIp() {
        try {
            List<NetworkInterface> interfaces = Collections.list(NetworkInterface.getNetworkInterfaces());
            for (NetworkInterface intf : interfaces) {
                List<InetAddress> addrs = Collections.list(intf.getInetAddresses());
                for (InetAddress addr : addrs) {
                    if (!addr.isLoopbackAddress()) {
                        String sAddr = addr.getHostAddress();
                        if (sAddr.indexOf(':') < 0) return sAddr;
                    }
                }
            }
        } catch (Exception ignored) {}
        return "127.0.0.1";
    }

    private void autoActivateAdb() {
        new Thread(() -> {
            String ip = getDeviceIp();
            log("-> Device IP: " + ip);
            log("-> Starting automated ADB activation sequence...");

            // 1. Try Settings.Global
            try {
                Settings.Global.putInt(getContentResolver(), Settings.Global.ADB_ENABLED, 1);
                log("✓ Settings.Global.ADB_ENABLED set to 1");
            } catch (Exception e) {
                log("✗ Settings.Global.ADB_ENABLED: " + e.getMessage());
            }

            try {
                Settings.Global.putInt(getContentResolver(), "development_settings_enabled", 1);
                log("✓ development_settings_enabled set to 1");
            } catch (Exception e) {
                log("✗ development_settings_enabled: " + e.getMessage());
            }

            // 2. Run shell & root activation
            runAdbScriptInternal();

            // 3. Probe port 5555
            boolean open = checkPort5555();
            if (open) {
                log("\n🎉 SUCCESS: Port 5555 is OPEN! ADB is active!");
                updateStatus("✅ ADB ACTIVE on " + ip + ":5555 | Web Console: http://" + ip + ":" + httpPort);
            } else {
                log("\n⚠️ Port 5555 is not open yet.");
                updateStatus("🌐 Web Console Ready: http://" + ip + ":" + httpPort + " | Port 5555: Closed");
            }
        }).start();
    }

    private void runAdbScript() {
        new Thread(() -> {
            log("\n--- Manual ADB Activation Triggered ---");
            runAdbScriptInternal();
            boolean open = checkPort5555();
            String ip = getDeviceIp();
            if (open) {
                log("🎉 ADB PORT 5555 IS OPEN!");
                updateStatus("✅ ADB ACTIVE on " + ip + ":5555 | Web Console: http://" + ip + ":" + httpPort);
            } else {
                log("⚠️ Port 5555 still closed after script.");
            }
        }).start();
    }

    private void runAdbScriptInternal() {
        // Try root first
        boolean hasSu = checkSu();
        log("-> Checking for root (su): " + (hasSu ? "YES! (Root available)" : "No standard su binary"));

        String[] commands = new String[]{
                "setprop persist.adb.tcp.port 5555",
                "setprop service.adb.tcp.port 5555",
                "setprop persist.sys.usb.config adb",
                "setprop sys.usb.config adb",
                "stop adbd",
                "start adbd"
        };

        if (hasSu) {
            log("-> Executing ADB startup commands via su...");
            for (String cmd : commands) {
                String out = execCommand("su -c \"" + cmd + "\"");
                log("  su> " + cmd + (out.isEmpty() ? " (OK)" : " -> " + out.trim()));
            }
        } else {
            log("-> Executing ADB startup commands via standard shell...");
            for (String cmd : commands) {
                String out = execCommand(cmd);
                log("  sh> " + cmd + (out.isEmpty() ? " (OK)" : " -> " + out.trim()));
            }
        }
    }

    private boolean checkSu() {
        String[] paths = {"/system/bin/su", "/system/xbin/su", "/sbin/su", "/vendor/bin/su"};
        for (String p : paths) {
            if (new java.io.File(p).exists()) return true;
        }
        try {
            Process p = Runtime.getRuntime().exec("which su");
            BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line = r.readLine();
            p.destroy();
            return line != null && line.length() > 0;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean checkPort5555() {
        try {
            Socket s = new Socket("127.0.0.1", 5555);
            s.close();
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private String execCommand(String cmd) {
        StringBuilder sb = new StringBuilder();
        try {
            Process p = Runtime.getRuntime().exec(new String[]{"sh", "-c", cmd});
            BufferedReader in = new BufferedReader(new InputStreamReader(p.getInputStream()));
            BufferedReader err = new BufferedReader(new InputStreamReader(p.getErrorStream()));
            String line;
            while ((line = in.readLine()) != null) sb.append(line).append("\n");
            while ((line = err.readLine()) != null) sb.append("[err] ").append(line).append("\n");
            p.waitFor();
        } catch (Exception e) {
            sb.append("Exec exception: ").append(e.getMessage());
        }
        return sb.toString();
    }

    private void launchIntent(Intent intent) {
        try {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            log("✓ Launched intent: " + intent);
        } catch (Exception e) {
            log("✗ Failed to launch intent: " + e.getMessage());
        }
    }

    private void launchAction(String action) {
        try {
            Intent intent = new Intent(action);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            log("✓ Launched action: " + action);
        } catch (Exception e) {
            log("✗ Failed action " + action + ": " + e.getMessage());
        }
    }

    private void launchComponent(String pkg, String cls) {
        try {
            Intent intent = new Intent();
            intent.setComponent(new ComponentName(pkg, cls));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            log("✓ Launched " + pkg + "/" + cls);
        } catch (Exception e) {
            log("✗ Failed " + pkg + "/" + cls + ": " + e.getMessage());
        }
    }

    // --- Embedded HTTP Server for Remote Management ---
    private void startHttpServer() {
        new Thread(() -> {
            try {
                serverSocket = new ServerSocket(httpPort);
                serverRunning = true;
                log("✓ Remote Web Console started on port " + httpPort);
                while (serverRunning) {
                    try {
                        Socket client = serverSocket.accept();
                        handleClient(client);
                    } catch (Exception ignored) {}
                }
            } catch (Exception e) {
                log("✗ HTTP Server error: " + e.getMessage());
            }
        }).start();
    }

    private void handleClient(Socket socket) {
        new Thread(() -> {
            try {
                InputStream is = socket.getInputStream();
                BufferedReader reader = new BufferedReader(new InputStreamReader(is));
                String line = reader.readLine();
                if (line == null) {
                    socket.close();
                    return;
                }

                String[] parts = line.split(" ");
                String method = parts[0];
                String path = parts.length > 1 ? parts[1] : "/";

                OutputStream os = socket.getOutputStream();

                if (path.equals("/") || path.startsWith("/?")) {
                    String ip = getDeviceIp();
                    boolean p5555 = checkPort5555();
                    String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>TV Console</title>" +
                            "<style>body{font-family:sans-serif;background:#0f172a;color:#f8fafc;padding:24px;}" +
                            "h1{color:#38bdf8;}button,a{background:#0284c7;color:#fff;padding:10px 16px;text-decoration:none;" +
                            "border:none;border-radius:6px;cursor:pointer;display:inline-block;margin:4px;font-weight:bold;}" +
                            "pre{background:#020617;color:#4ade80;padding:16px;border-radius:8px;overflow-x:auto;}" +
                            "input[type=text]{padding:10px;width:70%;border-radius:6px;border:1px solid #334155;background:#1e293b;color:#fff;}" +
                            "</style></head><body>" +
                            "<h1>⚡ Android TV Remote Console</h1>" +
                            "<p><b>Device IP:</b> " + ip + " | <b>ADB Port 5555:</b> " + (p5555 ? "<span style='color:#4ade80'>OPEN</span>" : "<span style='color:#f87171'>CLOSED</span>") + "</p>" +
                            "<div>" +
                            "<a href='/api/adb'>⚡ Run ADB Enable Script</a> " +
                            "<a href='/api/launch?action=android.settings.APPLICATION_DEVELOPMENT_SETTINGS'>🛠️ Open Dev Settings</a> " +
                            "<a href='/api/launch?pkg=com.hospitality.tvhome&cls=com.hospitality.tvhome.MainActivity'>🏠 Open Hospitality Home</a>" +
                            "</div>" +
                            "<h3>Run Shell Command:</h3>" +
                            "<form action='/exec' method='GET'>" +
                            "<input type='text' name='cmd' placeholder='e.g. getprop or pm list packages' value='getprop ro.build.version.release'>" +
                            "<button type='submit'>Execute</button>" +
                            "</form>" +
                            "<h3>TV Diagnostics Log:</h3>" +
                            "<pre>" + logBuffer.toString() + "</pre>" +
                            "</body></html>";
                    sendResponse(os, 200, "text/html", html.getBytes());
                } else if (path.startsWith("/exec")) {
                    String cmd = extractParam(path, "cmd");
                    String result = execCommand(URLDecoder.decode(cmd, "UTF-8"));
                    String html = "<!DOCTYPE html><html><body style='background:#0f172a;color:#4ade80;font-family:monospace;padding:20px;'>" +
                            "<a href='/' style='color:#38bdf8;'>&larr; Back to Console</a>" +
                            "<h3>Command: " + cmd + "</h3><pre>" + result + "</pre></body></html>";
                    sendResponse(os, 200, "text/html", html.getBytes());
                } else if (path.startsWith("/api/adb")) {
                    runAdbScriptInternal();
                    sendResponse(os, 200, "text/plain", ("Executed ADB script. Port 5555 open: " + checkPort5555()).getBytes());
                } else if (path.startsWith("/api/launch")) {
                    String action = extractParam(path, "action");
                    String pkg = extractParam(path, "pkg");
                    String cls = extractParam(path, "cls");
                    if (!action.isEmpty()) {
                        launchAction(action);
                    } else if (!pkg.isEmpty() && !cls.isEmpty()) {
                        launchComponent(pkg, cls);
                    }
                    sendResponse(os, 200, "text/plain", "Launch attempted".getBytes());
                } else {
                    sendResponse(os, 404, "text/plain", "Not Found".getBytes());
                }
                socket.close();
            } catch (Exception ignored) {}
        }).start();
    }

    private String extractParam(String path, String key) {
        int idx = path.indexOf(key + "=");
        if (idx < 0) return "";
        int start = idx + key.length() + 1;
        int end = path.indexOf("&", start);
        if (end < 0) end = path.length();
        return path.substring(start, end);
    }

    private void sendResponse(OutputStream os, int code, String contentType, byte[] body) {
        try {
            String header = "HTTP/1.1 " + code + " OK\r\n" +
                    "Content-Type: " + contentType + "\r\n" +
                    "Content-Length: " + body.length + "\r\n" +
                    "Access-Control-Allow-Origin: *\r\n" +
                    "Connection: close\r\n\r\n";
            os.write(header.getBytes());
            os.write(body);
            os.flush();
        } catch (Exception ignored) {}
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        serverRunning = false;
        try {
            if (serverSocket != null) serverSocket.close();
        } catch (Exception ignored) {}
    }
}

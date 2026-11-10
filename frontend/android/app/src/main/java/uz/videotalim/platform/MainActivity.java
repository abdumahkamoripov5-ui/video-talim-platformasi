package uz.videotalim.platform;

import android.app.AlertDialog;
import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Bundle;
import android.view.WindowManager;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private boolean closing = false;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Protect course videos: blocks screenshots, screen recording and
        // app previews in the recent-apps list.
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_SECURE, WindowManager.LayoutParams.FLAG_SECURE);
        if (!hasInternet()) {
            closeWithoutInternet();
        }
    }

    @Override
    public void onResume() {
        super.onResume();
        // Content is never stored on the device, so the app closes when offline.
        if (!closing && !hasInternet()) {
            closeWithoutInternet();
        }
    }

    private boolean hasInternet() {
        ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm == null) {
            return false;
        }
        Network network = cm.getActiveNetwork();
        if (network == null) {
            return false;
        }
        NetworkCapabilities caps = cm.getNetworkCapabilities(network);
        return caps != null && caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
    }

    private void closeWithoutInternet() {
        closing = true;
        new AlertDialog.Builder(this)
                .setTitle("Internet yo'q")
                .setMessage("Ilova ishlashi uchun internet aloqasi kerak. Ilova yopiladi.")
                .setCancelable(false)
                .setPositiveButton("OK", new android.content.DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(android.content.DialogInterface dialog, int which) {
                        finishAndRemoveTask();
                    }
                })
                .show();
    }
}

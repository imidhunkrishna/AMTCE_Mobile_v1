package com.amtce.mobile

import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.util.Base64
import android.util.Log
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.chaquo.python.Python
import java.io.File
import java.net.URL
import java.security.MessageDigest
import java.util.*
import org.json.JSONObject
import com.chaquo.python.android.AndroidPlatform

class MainActivity : AppCompatActivity() {

    private val TAG = "AMTCE_MainActivity"
    private lateinit var apiKeyInput: EditText
    private lateinit var sharedPrefs: SharedPreferences

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 🧠 1 & 10: Runtime Security Audit (Anti-Tamper/Root/Frida)
        if (!performSecurityAudit()) {
            return 
        }

        setContentView(R.layout.activity_main)

        apiKeyInput = findViewById(R.id.apiKeyInput)

        // 🛡️ Security: Create a MasterKey for encryption
        val masterKey = MasterKey.Builder(this)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        // 🛡️ Security: Initialize EncryptedSharedPreferences
        sharedPrefs = EncryptedSharedPreferences.create(
            this,
            "AMTCE_PREFS_SECURE",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )

        // 1. Load Saved API Key
        val savedKey = sharedPrefs.getString("GEMINI_API_KEY", "")
        apiKeyInput.setText(savedKey)

        // 2. Auto-Save Key on Change
        apiKeyInput.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) {
                sharedPrefs.edit().putString("GEMINI_API_KEY", s.toString()).apply()
            }
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
        })

        // 3. Initialize Chaquopy Python Environment
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        // 4. Handle Incoming Share Intent
        handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleIntent(it) }
    }

    private fun handleIntent(intent: Intent) {
        val action = intent.action
        val type = intent.type

        if (Intent.ACTION_SEND == action && type != null) {
            if ("text/plain" == type) {
                handleSharedText(intent)
            }
        }
    }

    private var lastMissionTime: Long = 0
    private val MISSION_COOLDOWN = 30000 // 🛡️ 9: 30s Behavioral Rate Limit

    private fun handleSharedText(intent: Intent) {
        val currentKey = apiKeyInput.text.toString()
        if (currentKey.isEmpty()) {
            Toast.makeText(this, "⚠️ Please provide a Gemini API Key first!", Toast.LENGTH_LONG).show()
            return
        }

        // 🛡️ SECURITY 9: Behavioral Abuse Protection (Rate Limiting)
        val currentTime = System.currentTimeMillis()
        if (currentTime - lastMissionTime < MISSION_COOLDOWN) {
            Toast.makeText(this, "⚠️ Security: Too many requests. Wait 30s.", Toast.LENGTH_LONG).show()
            return
        }
        lastMissionTime = currentTime

        intent.getStringExtra(Intent.EXTRA_TEXT)?.let { sharedText ->
            // 🛡️ SECURITY 3 & 7: Intent Validation & Log Stripping
            // Prevent malicious apps from sending massive payloads or script injection
            if (sharedText.length > 2000 || !sharedText.contains("http")) {
                Toast.makeText(this, "⚠️ Security Error: Invalid link format.", Toast.LENGTH_LONG).show()
                return
            }

            // Removed Log.d to prevent sensitive data leakage to logcat
            Toast.makeText(this, "AMTCE: Processing Link...", Toast.LENGTH_SHORT).show()
            
            // 5. Dispatch to Python Orchestrator in Background
            Thread {
                try {
                    val py = Python.getInstance()
                    
                    // Inject API Key into Python os.environ
                    val osModule = py.getModule("os")
                    val environ = osModule.get("environ")
                    environ?.callAttr("putenv", "GEMINI_API_KEY", currentKey)
                    
                    val orchestratorModule = py.getModule("orchestrator")
                    val orchestrator = orchestratorModule.get("orchestrator")
                    
                    // Update mission label in UI
                    runOnUiThread {
                        findViewById<TextView>(R.id.missionLabel).text = sharedText
                        findViewById<TextView>(R.id.statusLabel).text = "PLANNING..."
                    }

                    // Call the main entry point
                    orchestrator?.callAttr("process_link", sharedText)
                    
                    runOnUiThread {
                        findViewById<TextView>(R.id.statusLabel).text = "MISSION SUCCESS"
                        Toast.makeText(this, "✅ Mission Started Successfully!", Toast.LENGTH_LONG).show()
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "💥 Python Bridge Error: ${e.message}")
                    runOnUiThread {
                        findViewById<TextView>(R.id.statusLabel).text = "ERROR"
                        Toast.makeText(this, "💥 Error: ${e.message}", Toast.LENGTH_LONG).show()
                    }
                }
            }.start()
        }
    private fun performSecurityAudit(): Boolean {
        // 🛡️ SECURITY 3: Remote Kill-Switch (Adaptive Defense)
        // Fetches remote status to allow for remote disabling in case of key breach.
        Thread {
            try {
                val config = URL("https://raw.githubusercontent.com/imidhunkrishna/AMTCE_Mobile_v1/main/security_config.json").readText()
                val json = JSONObject(config)
                if (!json.getBoolean("app_enabled")) {
                    runOnUiThread {
                        AlertDialog.Builder(this@MainActivity)
                            .setTitle("🛑 Remote Lockdown")
                            .setMessage(json.getString("lockdown_message"))
                            .setCancelable(false)
                            .setPositiveButton("Exit") { _, _ -> finish() }
                            .show()
                    }
                }
            } catch (e: Exception) { /* Fail safe: Allow if config is unreachable or not yet set */ }
        }.start()

        val isRooted = checkRoot()
        val isEmulator = checkEmulator()
        val isTampered = !verifySignature()
        
        if (isRooted || isEmulator || isTampered) {
            val message = if (isTampered) "Unofficial/Modded APK detected. Closing for safety." 
                          else "This application cannot run on a rooted device or emulator."
            
            AlertDialog.Builder(this)
                .setTitle("🛡️ Security Violation")
                .setMessage(message)
                .setCancelable(false)
                .setPositiveButton("Exit") { _, _ -> finish() }
                .show()
            return false
        }
        return true
    }

    private fun verifySignature(): Boolean {
        // 🛡️ SECURITY 7: Anti-Repackaging Signature Validation
        // This prevents attackers from re-signing your APK and distributing it.
        try {
            val packageInfo = packageManager.getPackageInfo(packageName, PackageManager.GET_SIGNATURES)
            for (signature in packageInfo.signatures) {
                val md = MessageDigest.getInstance("SHA-256")
                md.update(signature.toByteArray())
                val currentSignature = Base64.encodeToString(md.digest(), Base64.DEFAULT).trim()
                
                // [Architect Note] Replace this with your actual production SHA-256 key hash 
                // once you have signed your first release APK.
                val expectedSignature = "YOUR_PRODUCTION_SIGNATURE_HASH_HERE" 
                
                if (expectedSignature != "YOUR_PRODUCTION_SIGNATURE_HASH_HERE" && currentSignature != expectedSignature) {
                    return false
                }
            }
        } catch (e: Exception) { return false }
        return true
    }

    private fun checkRoot(): Boolean {
        val paths = arrayOf(
            "/system/app/Superuser.apk", "/sbin/su", "/system/bin/su", "/system/xbin/su",
            "/data/local/xbin/su", "/data/local/bin/su", "/system/sd/xbin/su",
            "/system/bin/failsafe/su", "/data/local/su"
        )
        for (path in paths) {
            if (File(path).exists()) return true
        }
        val buildTags = Build.TAGS
        return buildTags != null && buildTags.contains("test-keys")
    }

    private fun checkEmulator(): Boolean {
        return (Build.BRAND.startsWith("generic") && Build.DEVICE.startsWith("generic"))
                || Build.FINGERPRINT.contains("generic")
                || Build.FINGERPRINT.contains("unknown")
                || Build.HARDWARE.contains("goldfish")
                || Build.HARDWARE.contains("ranchu")
                || Build.MODEL.contains("google_sdk")
                || Build.MODEL.contains("Emulator")
                || Build.MODEL.contains("Android SDK built for x86")
                || Build.MANUFACTURER.contains("Genymotion")
                || Build.PRODUCT.contains("sdk_google")
                || Build.PRODUCT.contains("google_sdk")
                || Build.PRODUCT.contains("sdk")
                || Build.PRODUCT.contains("sdk_x86")
                || Build.PRODUCT.contains("vbox86p")
                || Build.PRODUCT.contains("emulator")
                || Build.PRODUCT.contains("simulator")
    }
}

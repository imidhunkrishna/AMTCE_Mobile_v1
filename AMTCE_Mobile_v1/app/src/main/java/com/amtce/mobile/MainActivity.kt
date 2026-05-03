package com.amtce.mobile

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class MainActivity : AppCompatActivity() {

    private val TAG = "AMTCE_MainActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 1. Initialize Chaquopy Python Environment
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        // 2. Handle Incoming Share Intent
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

    private fun handleSharedText(intent: Intent) {
        intent.getStringExtra(Intent.EXTRA_TEXT)?.let { sharedText ->
            Log.d(TAG, "📥 Received Shared Link: $sharedText")
            Toast.makeText(this, "AMTCE: Processing Link...", Toast.LENGTH_SHORT).show()
            
            // 3. Dispatch to Python Orchestrator in Background
            Thread {
                try {
                    val py = Python.getInstance()
                    val orchestratorModule = py.getModule("orchestrator")
                    val orchestrator = orchestratorModule.get("orchestrator")
                    
                    // Call the main entry point
                    orchestrator?.callAttr("process_link", sharedText)
                    
                    runOnUiThread {
                        Toast.makeText(this, "✅ Mission Started Successfully!", Toast.LENGTH_LONG).show()
                    }
                } catch (e: Exception) {
                    Log.error(TAG, "💥 Python Bridge Error: ${e.message}")
                    runOnUiThread {
                        Toast.makeText(this, "💥 Error: ${e.message}", Toast.LENGTH_LONG).show()
                    }
                }
            }.start()
        }
    }
}

# 🚀 AMTCE Mobile v1 (Vanguard Edition)

**Autonomous Multimedia Transformation & Compilation Engine**

AMTCE Mobile is a high-performance, mobile-native intelligence suite designed to automate the creation of viral, rhythm-synchronized video content directly from an Android device.

![AMTCE Mobile Banner](https://img.shields.io/badge/Engine-Vanguard_v1.0-blue?style=for-the-badge&logo=android)
![Security](https://img.shields.io/badge/Security-Secret_Protected-green?style=for-the-badge)
![Build](https://img.shields.io/badge/Cloud_Build-GitHub_Actions-orange?style=for-the-badge)

## 🧠 Core Intelligence
*   **RhythmEngine**: Sub-millisecond precision beat-syncing using tension-arc snapping.
*   **VanguardDirector**: Autonomous mission planning with zero-token local RAG fallback.
*   **FashionScout**: Visual detection module optimized for e-commerce conversion.
*   **MonetizationBrain**: Automatic affiliate link integration and sales copy generation.

## 🛠️ Features
- **One-Tap Mission**: Share any Instagram or TikTok link directly to the app to trigger the pipeline.
- **Secure Authentication**: Built-in UI for Gemini API Key management with encrypted local storage.
- **Cloud-Native Build**: Automated CI/CD pipeline via GitHub Actions—build your APK in the cloud.
- **Zero-SDK Workflow**: No local Android development environment required.

## 🚀 Getting Started
1. **Fork/Clone** this repository to your GitHub account.
2. **Add Secrets**: Go to `Settings > Secrets and variables > Actions` and add your `GEMINI_API_KEY`.
3. **Build**: Every push to the `main` branch automatically triggers a build in the **Actions** tab.
4. **Download**: Download the generated APK from the build artifacts and install it on your Android device.

## 🛡️ Security & Privacy
AMTCE Mobile is built with a **Security-First** architecture. Local `.env` files are automatically ignored via `.gitignore`, and all sensitive keys are injected at runtime using GitHub Secrets or the secure on-device UI.

## 🛡️ Post-Deployment Security Ops (SYSTEM DESIGNER LEVEL)
Your application is now hardened at the client level. To reach 100% system-level security and protect your API economics, you MUST follow these steps:

### 1. Google Cloud Platform (GCP) Hardening
*   **Restrict API Key:** Go to GCP Console > Credentials. Restrict your Gemini API key to **Android Apps**.
*   **Add Fingerprint:** Add your app's Package Name (`com.amtce.mobile`) and your SHA-1 certificate fingerprint. This prevents anyone from using your key outside of your specific, signed APK.
*   **Set Quotas:** Set a "Daily Budget" or "Requests per Minute" quota in the Google AI Studio console. This limits your financial exposure if your key is proxied.

### 2. Adaptive Defense (Remote Kill Switch)
*   You can remotely disable your app by editing `security_config.json` in this repository.
*   Set `"app_enabled": false` to instantly lock all deployed APKs if you suspect a breach.

### 3. Red Teaming (Attack Your Own App)
To verify your growth, attempt these attacks:
1.  **Bypass Cooldown:** Use an auto-clicker to try and launch missions faster than 30s.
2.  **Signature Spoof:** Try to re-sign the APK with a different key and install it.
3.  **Root Inspection:** Try running the app on a rooted emulator with Frida.

### 🚀 Production Readiness
*   **Kotlin:** Resilient (Fail-Closed Kill-Switch / Root & Emulator Detection / Signature Pinning)
*   **Python:** Hardened (Path & Prompt Sanitization / RAG Encryption)
*   **Network:** Verified (Strict TLS / No Cleartext / Adversarial Telemetry active)
*   **Management:** System-Level (Remote config with lockdown capability)

## 🧨 Resilience & Recovery Protocol
Security is a process, not a state. If you detect an anomaly:
1.  **Immediate Lockdown:** Edit `security_config.json` and set `"app_enabled": false`.
2.  **Key Rotation:** Revoke the old API key in Google Cloud Console.
3.  **Audit Logs:** Check your `LOG_URL` endpoint for `ROOT_DETECTED` or `SIGNATURE_MISMATCH` payloads.
4.  **Redeploy:** Generate a new APK with the rotated key and update the `expectedSignature` hash if you changed your signing key.

---
*Developed by Google Deepmind Team x AMTCE Intelligence*

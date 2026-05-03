# 🚀 How to Launch AMTCE Mobile in Android Studio

I have prepared the full project structure for you. Follow these steps to "build" and run it:

### Step 1: Open the Project
1. Open **Android Studio**.
2. Click **Open** (or File > Open).
3. Navigate to: `e:\Android app\AMTCE_Mobile_v1`.
4. Select the folder and click **OK**.

### Step 2: Sync Gradle (The "Venv" Setup)
Once the project opens, Android Studio will automatically start "Syncing." 
*   This is where it creates your **isolated Python environment**.
*   It will download `yt-dlp`, `requests`, and `python-dotenv` automatically.
*   **Wait** until the progress bar at the bottom finishes.

### Step 3: Verify the Python Engine
You can find your extracted Python logic here:
`app > src > main > python`

Your `.env` file is located at the root of the project. Android Studio will use this for the Python scripts.

### Step 4: Running the App
1. Connect your **4GB RAM Android Phone** via USB (Enable USB Debugging).
2. Click the **Run** button (Green Triangle) in the top toolbar.
3. The app will compile and install.

### 🛡️ Why this is "Isolated"
*   The Python interpreter is embedded inside the app.
*   The `pip` dependencies are downloaded into a private build cache.
*   Nothing is installed on your Windows system Python; everything stays inside `AMTCE_Mobile_v1`.

**I have finished setting up the folders and configuration files. You are now ready to open the project!**

# scripts/test_engine.py
import sys
import os

# Add the Android Python directory to sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "app", "src", "main", "python"))

def test_imports():
    print("Testing Module Imports (with Dependency Mocking)...")
    try:
        # Mock yt_dlp for this specific test environment
        import sys
        from unittest.mock import MagicMock
        sys.modules["yt_dlp"] = MagicMock()
        
        from orchestrator import AMTCE_Mobile_Orchestrator
        print("Orchestrator Import: SUCCESS")
        return True
    except ImportError as e:
        print(f"Import Failed: {e}")
        return False

def test_logic_flow():
    print("\nTesting Logic Flow (Mock Mode)...")
    from orchestrator import AMTCE_Mobile_Orchestrator
    
    engine = AMTCE_Mobile_Orchestrator()
    
    # Mock data
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    mock_hints = {
        "suggested_cuts": [5.0, 10.0, 15.0],
        "effects": [{"type": "zoom_in"}],
        "watermarks": [{"x": 10, "y": 10, "w": 100, "h": 50}]
    }

    print(f"Running pipeline for URL: {test_url}")
    
    # We monkeypatch the downloader to avoid actual network calls during test
    engine.downloader.download = lambda url: {
        "id": "mock_id",
        "title": "Mock Video",
        "duration": 30,
        "local_path": "downloads/mock.mp4"
    }

    result = engine.process_link(test_url, mock_hints)
    
    if result["status"] == "success":
        print("Logic Flow: SUCCESS")
        print(f"Result Payload: {result['upload_payload']['title']}")
        return True
    else:
        print(f"Logic Flow: FAILED - {result.get('message')}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        test_logic_flow()
    
    print("\nTest Completed.")

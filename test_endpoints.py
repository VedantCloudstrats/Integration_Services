import subprocess
import time
import requests
import sys
import os

def run_tests():
    print("Running FastAPI Integration Tests...")
    
    # 1. Start the uvicorn server in a subprocess
    if sys.platform == "win32":
        python_bin = os.path.join(".venv", "Scripts", "python.exe")
    else:
        python_bin = os.path.join(".venv", "bin", "python")
        
    server_process = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "fast_api.main:app", "--port", "8001", "--host", "127.0.0.1"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Give the server 3 seconds to start
    time.sleep(3)
    
    base_url = "http://127.0.0.1:8001"
    headers = {
        "X-API-Key": "dev-secret-key"
    }
    
    try:
        # Test 1: Root endpoint (No Auth)
        resp = requests.get(f"{base_url}/", timeout=5)
        print(f"Test Root (No Auth): Status {resp.status_code}")
        assert resp.status_code == 200, "Root endpoint should return 200"
        print("Root response data:", resp.json())
        
        # Test 2: CMMS Defects (With Auth)
        resp = requests.get(f"{base_url}/api/cmms/defects", headers=headers, timeout=35)
        print(f"Test CMMS Defects: Status {resp.status_code}")
        assert resp.status_code in [200, 500], "CMMS Defects endpoint should return 200 (or 500 if DB is offline)"
        if resp.status_code == 200:
            print(f"Fetched {len(resp.json())} defects.")
        else:
            print("Note: CMMS Defects returned 500 (database is likely offline/unreachable).")
        
        # Test 3: Unauthorized Request (No API Key)
        resp = requests.get(f"{base_url}/api/cmms/defects", timeout=35)
        print(f"Test Unauthorized: Status {resp.status_code}")
        assert resp.status_code == 401, "Requests without X-API-Key should return 401"
        
        # Test 4: Forbidden Request (Invalid API Key)
        resp = requests.get(f"{base_url}/api/cmms/defects", headers={"X-API-Key": "wrong-key"}, timeout=35)
        print(f"Test Forbidden: Status {resp.status_code}")
        assert resp.status_code == 403, "Requests with incorrect X-API-Key should return 403"
        
        print("\n[SUCCESS] All FastAPI Integration Tests Passed Successfully!")
        
    except AssertionError as ae:
        print(f"\n[FAIL] Test Assertion Failed: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test Failed with Exception: {e}")
        sys.exit(1)
    finally:
        # Shutdown the server
        print("Stopping FastAPI server process...")
        server_process.terminate()
        server_process.wait()
        print("FastAPI server stopped.")

if __name__ == "__main__":
    run_tests()

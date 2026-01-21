import uvicorn
import sys
import os
import traceback

# Ensure current directory is in path
sys.path.append(os.getcwd())

if __name__ == "__main__":
    try:
        print("Importing app...")
        from backend.main import app
        print("Starting uvicorn...")
        # Use a different port just to be safe, but user wants 8000.
        # We try 8000.
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
    except Exception:
        with open("server_crash.txt", "w") as f:
            f.write(traceback.format_exc())
        print("CRASHED")

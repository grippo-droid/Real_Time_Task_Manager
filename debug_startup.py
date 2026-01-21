import sys
import os

# Add current directory to sys.path
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"Current working directory: {current_dir}")
print(f"Python path: {sys.path}")

try:
    print("Attempting to import backend.main...")
    import backend.main
    print("Successfully imported backend.main")
except Exception as e:
    print(f"Failed to import backend.main: {e}")
    import traceback
    traceback.print_exc()

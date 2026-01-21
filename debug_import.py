import sys
import traceback

try:
    print("Attempting import...")
    import backend.main
    print("Import successful")
except Exception:
    with open("debug_error.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Import failed, traceback written to debug_error.txt")

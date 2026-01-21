
import os
import subprocess
import re
import sys

def kill_port_8000():
    print("Looking for process on port 8000...")
    try:
        # Run netstat to find the process ID (PID)
        output = subprocess.check_output("netstat -ano | findstr :8000", shell=True).decode()
        lines = output.strip().split('\n')
        
        pids = set()
        for line in lines:
            parts = re.split(r'\s+', line.strip())
            if len(parts) > 4:
                pid = parts[-1]
                pids.add(pid)
        
        if not pids:
            print("No process found on port 8000.")
            return

        for pid in pids:
            if pid == "0": continue # Don't kill system idle process
            print(f"killing process with PID: {pid}")
            os.system(f"taskkill /F /PID {pid}")
            print("Process killed.")
            
    except subprocess.CalledProcessError:
        print("No process found on port 8000 (netstat error or empty).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    kill_port_8000()

import sys
import traceback
import os

log_file = "e:/LETS COOK/Projects/Real_Time_Taskmanager/crash_report.txt"

def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")
    print(msg)

try:
    if os.path.exists(log_file):
        os.remove(log_file)
    
    log("Starting incremental debug...")
    
    log("Importing backend.database...")
    import backend.database
    log("Success: backend.database")

    log("Importing backend.models...")
    import backend.models
    log("Success: backend.models")

    log("Importing backend.routers.auth...")
    import backend.routers.auth
    log("Success: backend.routers.auth")

    log("Importing backend.routers.admin...")
    import backend.routers.admin
    log("Success: backend.routers.admin")

    log("Importing backend.main...")
    import backend.main
    log("Success: backend.main")

except Exception:
    log("CRASHED!")
    log(traceback.format_exc())

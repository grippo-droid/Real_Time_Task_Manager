import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    from backend.database import users_collection, _MockCollection
    print(f"Users collection type: {type(users_collection)}")
    
    # Simulate the call from admin.py
    print("Attempting to find users with projection...")
    users = list(users_collection.find({}, {"password": 0}))
    print(f"Successfully found {len(users)} users.")
    for u in users:
        print(u)

except Exception as e:
    print("CRASHED!")
    import traceback
    traceback.print_exc()

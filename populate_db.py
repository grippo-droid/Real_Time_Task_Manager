import requests
import time
import random
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@123.com"
ADMIN_PASSWORD = "admin@123"

# Data Sets
USERS = [
    {"username": "Sarah Jenkins", "email": "sarah.j@company.com", "password": "password123", "role": "team_manager", "avatar": "https://i.pravatar.cc/150?u=sarah"},
    {"username": "Mike Ross", "email": "mike.r@company.com", "password": "password123", "role": "team_member", "avatar": "https://i.pravatar.cc/150?u=mike"},
    {"username": "Jessica Lee", "email": "jessica.l@company.com", "password": "password123", "role": "team_member", "avatar": "https://i.pravatar.cc/150?u=jessica"},
    {"username": "David Chen", "email": "david.c@company.com", "password": "password123", "role": "team_member", "avatar": "https://i.pravatar.cc/150?u=david"},
    {"username": "Emily Blunt", "email": "emily.b@company.com", "password": "password123", "role": "team_manager", "avatar": "https://i.pravatar.cc/150?u=emily"},
]

TEAMS = [
    {"name": "Product Development", "description": "Core engineering team responsible for the main product line."},
    {"name": "Marketing & Creative", "description": "Brand awareness, website design, and campaigns."},
]

BOARDS = [
    {"name": "Q1 Roadmap", "team_idx": 0, "description": "High-level strategic goals for Q1 2026"},
    {"name": "Sprint 23 - Backend", "team_idx": 0, "description": "Active tasks for the current backend sprint"},
    {"name": "Frontend Revamp", "team_idx": 0, "description": "UI/UX overhaul tasks"},
    {"name": "Website Redesign", "team_idx": 1, "description": "Main corporate website update"},
    {"name": "Social Media Campaign", "team_idx": 1, "description": "Q1 Social outreach planning"},
]

TASKS = [
    # Q1 Roadmap
    {"board_idx": 0, "title": "Implement OAuth2 Authentication", "status": "in_progress", "priority": "high", "description": "Switch from JWT custom auth to standard OAuth2 provider integration."},
    {"board_idx": 0, "title": "Database Sharding Strategy", "status": "todo", "priority": "urgent", "description": "Plan out the sharding strategy for user data as we scale to 1M users."},
    {"board_idx": 0, "title": "Mobile App MVP", "status": "review", "priority": "medium", "description": "Finalize scope for the iOS MVP application."},
    
    # Sprint 23
    {"board_idx": 1, "title": "Fix memory leak in websocket handler", "status": "in_progress", "priority": "urgent", "description": "Server crashes after 10k connections. Need to profile the ws_handler."},
    {"board_idx": 1, "title": "Optimize API response times", "status": "completed", "priority": "high", "description": "Reduce latency on /tasks endpoint. Reduced from 200ms to 50ms."},
    {"board_idx": 1, "title": "Add rate limiting", "status": "todo", "priority": "medium", "description": "Prevent abuse of the login endpoint."},
    
    # Frontend Revamp
    {"board_idx": 2, "title": "Update color palette to Tailwind", "status": "review", "priority": "high", "description": "Replace all hex codes with Tailwind classes."},
    {"board_idx": 2, "title": "Create reusable modal component", "status": "completed", "priority": "low", "description": "Standardize all modals across the app."},
    {"board_idx": 2, "title": "Implement Dark Mode", "status": "in_progress", "priority": "medium", "description": "Add dark mode toggle and styles."},

    # Website Redesign
    {"board_idx": 3, "title": "Design hero section", "status": "completed", "priority": "high", "description": "New hero image and catching copy."},
    {"board_idx": 3, "title": "Copywriting for features page", "status": "in_progress", "priority": "medium", "description": "Draft text needed for the features grid."},
]

COMMENTS = [
    "Great progress on this!",
    "Can we discuss this in the standup?",
    "Blocked by the API dependency.",
    "I'll pick this up tomorrow.",
    "Implemented the fix, ready for review.",
    "Make sure to check the mobile view.",
    "This is critical for the next release.",
]

def login(email, password):
    try:
        response = requests.post(f"{BASE_URL}/auth/token", data={"username": email, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def create_user(token, user_data):
    # Check if user exists first roughly (optional, but good for idempotency if API supported listing users easily)
    # Just trying to create, assuming email unique constraint handled by backend
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # Signup doesn't require token usually, but maybe admin can create? 
        # Models says SignupModel. Let's try /auth/signup or /admin/users if exists.
        # Checking backend/routers/auth.py would confirm, but usually signup is public.
        # However, we want to assign roles.
        # Let's try public signup first.
        signup_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "role": user_data["role"]
        }
        res = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
        if res.status_code == 200 or res.status_code == 201:
            print(f"Created user: {user_data['username']}")
            return res.json() # might return token or user
        elif res.status_code == 400 and "registered" in res.text:
            print(f"User {user_data['username']} already exists.")
             # Login to get ID? Or just skip.
            return None
        else:
            print(f"Failed to create user {user_data['username']}: {res.status_code} {res.text}")
    except Exception as e:
        print(f"Error creating user: {e}")

def get_user_token(email, password):
    return login(email, password)

def main():
    print("Starting data seeding...")
    
    # 1. Login as Admin
    admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not admin_token:
        print("Cannot login as admin. Ensure server is running and admin exists.")
        return

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    created_users = []
    
    # 2. Create Users
    print("\n--- Creating Users ---")
    for u in USERS:
        create_user(admin_token, u)
        # Login to get their ID and Token
        token = get_user_token(u["email"], u["password"])
        if token:
            # Get me to find ID
            res = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
            if res.status_code == 200:
                user_info = res.json()
                created_users.append({"id": user_info["id"], "token": token, "email": u["email"]})
    
    # 3. Create Teams
    print("\n--- Creating Teams ---")
    created_teams = []
    # Use Admin to create teams (or managers)
    for t in TEAMS:
        res = requests.post(f"{BASE_URL}/manager/teams", json=t, headers=admin_headers)
        if res.status_code == 200:
            team = res.json()
            created_teams.append(team)
            print(f"Created Team: {team['name']}")
        else:
            print(f"Failed to create team {t['name']}: {res.text}")
            
    # 4. Create Boards
    print("\n--- Creating Boards ---")
    created_boards = []
    for b in BOARDS:
        if b["team_idx"] < len(created_teams):
            team_id = created_teams[b["team_idx"]]["id"]
            # Add all users to the board for visibility
            member_ids = [u["id"] for u in created_users]
            
            board_payload = {
                "name": b["name"],
                "description": b["description"],
                "team_id": team_id,
                "member_ids": member_ids
            }
            res = requests.post(f"{BASE_URL}/manager/boards", json=board_payload, headers=admin_headers)
            if res.status_code == 200:
                board = res.json()
                created_boards.append(board)
                print(f"Created Board: {board['name']}")
            else:
                print(f"Failed to create board {b['name']}: {res.text}")

    # 5. Create Tasks
    print("\n--- Creating Tasks ---")
    created_tasks = []
    for t in TASKS:
        if t["board_idx"] < len(created_boards):
            board_id = created_boards[t["board_idx"]]["id"]
            # Assign random user
            assignee = random.choice(created_users)["id"] if created_users else None
            
            task_payload = {
                "title": t["title"],
                "description": t["description"],
                "board_id": board_id,
                "status": t["status"],
                "priority": t["priority"],
                "assigned_to": assignee,
                # due date in 1-14 days
                "due_date": (datetime.utcnow() + timedelta(days=random.randint(1, 14))).isoformat()
            }
            
            # Create task using admin or random user?
            # Creating as different users generates activity logs
            creator = random.choice(created_users)
            user_headers = {"Authorization": f"Bearer {creator['token']}"}
            
            res = requests.post(f"{BASE_URL}/tasks/", json=task_payload, headers=user_headers)
            if res.status_code == 200:
                task = res.json()
                created_tasks.append(task)
                print(f"Created Task: {task['title']}")
                
                # Add comments
                num_comments = random.randint(0, 3)
                for _ in range(num_comments):
                    commenter = random.choice(created_users)
                    c_headers = {"Authorization": f"Bearer {commenter['token']}"}
                    c_payload = {
                        "task_id": task["id"],
                        "content": random.choice(COMMENTS)
                    }
                    requests.post(f"{BASE_URL}/tasks/{task['id']}/comments", json=c_payload, headers=c_headers)
                    
            else:
                print(f"Failed to create task {t['title']}: {res.text}")

    print("\nData Seeding Completed!")

if __name__ == "__main__":
    main()

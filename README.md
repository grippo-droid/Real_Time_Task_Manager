# Real-Time Task Manager

## Project Startup Instructions

To start the project, you need to run the backend and frontend servers in separate terminal windows.

### 1. Start the Backend

First, activate the virtual environment:

```powershell
.\myenv\Scripts\Activate.ps1
```

Then run the server:

```powershell
python run_server.py
```

The server will start on `http://127.0.0.1:8000`.

### 2. Start the Frontend

Open a new terminal, navigate to the `frontend` directory, and start the React application:

```powershell
cd frontend
npm start
```

The frontend will open automatically at `http://localhost:3000`.

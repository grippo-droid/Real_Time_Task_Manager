# Deployment Guide

This guide details how to deploy the Real-Time Task Manager.

## Prerequisites
- GitHub Repository with the latest code pushed.
- Accounts on [Render](https://render.com/) and [Vercel](https://vercel.com/).
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) connection string (which you already have).

---

## 1. Push Code to GitHub
Ensure all your latest changes are pushed to your GitHub repository.
```bash
git push origin master
# or main, depending on your branch
```

---

## 2. Deploy Backend (Render)

1.  **New Web Service**: Go to the Render Dashboard and click **New +** -> **Web Service**.
2.  **Connect GitHub**: Select your `Real_Time_Task_Manager` repository.
3.  **Configure Settings**:
    - **Name**: `task-manager-api` (or similar)
    - **Region**: Closest to you (e.g., Singapore, Frankfurt, Oregon)
    - **Branch**: `master` (or main)
    - **Root Directory**: `.` (leave empty or dot)
    - **Runtime**: `Python 3`
    - **Build Command**: `pip install -r backend/requirements.txt`
    - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4.  **Environment Variables**:
    Scroll down to "Environment Variables" and add:
    - `MONGO_URI`: `your_mongodb_connection_string` (Copy from your `.env` file)
    - `DB_NAME`: `real_time_task_manager`
    - `SECRET_KEY`: `your_secret_key` (Generate a random string if you haven't)
    - `PYTHON_VERSION`: `3.10.0` (Optional, good for stability)
5.  **Deploy Web Service**: Click **Create Web Service**.

> [!NOTE]
> Wait for the deployment to finish. Once done, copy the **onrender.com URL** (e.g., `https://task-manager-api.onrender.com`).

---

## 3. Deploy Frontend (Vercel)

1.  **Import Project**: Go to Vercel Dashboard and click **Add New...** -> **Project**.
2.  **Select Repository**: Import `Real_Time_Task_Manager`.
3.  **Configure Project**:
    - **Framework Preset**: Create React App (should be detected automatically).
    - **Root Directory**: Click "Edit" and select `frontend`. **This is crucial!**
4.  **Environment Variables**:
    Expand the "Environment Variables" section and add:
    - `REACT_APP_API_URL`: Paste the **Render Backend URL** from the previous step.
      *(Example: `https://task-manager-api.onrender.com` - **do not** include a trailing slash)*
5.  **Deploy**: Click **Deploy**.

---

## 4. Final Configuration

1.  **Update Backend CORS (Optional/Recommended)**:
    - Once the frontend is live on Vercel, copy the **Vercel URL** (e.g., `https://task-manager-frontend.vercel.app`).
    - Go back to your Render Dashboard -> Environment Variables.
    - You can add a `FRONTEND_URL` variable if you refactor the code to use it, but currently, we set CORS to allow `*` (All origins), so it should work out of the box!
    - For better security later, update `backend/main.py` to only allow your Vercel domain.

## 5. Verification
- Open your Vercel URL.
- Try to Sign Up (this verifies database connection).
- Check the "Activity" or create a Task to verify functionality.

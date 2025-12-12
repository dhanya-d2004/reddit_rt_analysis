# MongoDB Setup Guide

You can run MongoDB locally or use the free cloud version (MongoDB Atlas).

## Option 1: MongoDB Atlas (Free Cloud) - Recommended
This is the easiest way to get started without installing database software.

1. **Create an Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).
   - Sign up for a free account.

2. **Create a Cluster**
   - Click **+ Create** to build a database.
   - Select the **M0 (Free)** tier.
   - Choose a provider (AWS/Google/Azure) and region close to you.
   - Click **Create Deployment**.

3. **Set Up Security**
   - **Database User**: Create a username and password. **Write these down**.
   - **Network Access**: Click "Add Current IP Address" (or allow access from anywhere `0.0.0.0/0` for development convenience).

4. **Get Connection String**
   - Go to **Database** in the sidebar.
   - Click **Connect** on your cluster.
   - Select **Drivers** (Python).
   - You will see a string like:
     ```
     mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
     ```
   - Copy this string.

5. **Update your .env**
   - Replace `<username>` and `<password>` with the user you created in step 3.
   - Paste into your `.env`:
     ```env
     MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
     ```

## Option 2: Local MongoDB
If you prefer to keep everything on your machine.

1. **Install MongoDB Community Server**
   - Download from the [official download center](https://www.mongodb.com/try/download/community).
   - Follow the installation instructions for Windows.
   - **Tip**: Install "MongoDB Compass" as well (a GUI for viewing data).

2. **Start MongoDB**
   - On Windows, it usually runs as a Service automatically.

3. **Connection String**
   - Your URI is standard:
     ```env
     MONGODB_URI=mongodb://localhost:27017/
     ```

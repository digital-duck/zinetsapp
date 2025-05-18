# Project Structure

Here's the recommended project structure for the Chinese Character Manager application:

```
chinese-character-manager/
├── frontend/                   # Vue.js frontend
│   ├── public/
│   │   ├── favicon.ico
│   │   └── index.html         # HTML template
│   ├── src/
│   │   ├── App.vue            # Main application component
│   │   ├── main.js            # Vue application entry point
│   │   ├── assets/            # Static assets (images, fonts, etc.)
│   │   ├── components/        # Vue components (if you decide to split App.vue)
│   │   └── services/          # API services (if you decide to separate API calls)
│   ├── .gitignore
│   ├── babel.config.js
│   ├── package.json           # Frontend dependencies
│   ├── vue.config.js          # Vue.js configuration
│   └── README.md
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Backend dependencies
│   ├── init_db.py             # Database initialization script
│   └── README.md
├── zinets_cache.sqlite        # SQLite database
└── README.md                  # Project README
```

## Setup Guide

### 1. Set up the project structure

```bash
# Create project directories
mkdir -p chinese-character-manager/frontend/public
mkdir -p chinese-character-manager/frontend/src
mkdir -p chinese-character-manager/backend

# Navigate to project root
cd chinese-character-manager
```

### 2. Set up the backend

```bash
# Navigate to backend directory
cd backend

# Create files
touch main.py
touch requirements.txt
touch init_db.py

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic python-multipart

# Save dependencies to requirements.txt
pip freeze > requirements.txt
```

Copy the provided backend code to the respective files.

### 3. Set up the frontend

```bash
# Navigate to frontend directory
cd ../frontend

npm -v # 10.8.3 
node -v # v20.10.0

# Initialize a new Vue.js project
npm init -y

# Install dependencies
npm install vue@next element-plus axios @element-plus/icons-vue vue-axios core-js
npm install -D @vue/cli-service @vue/cli-plugin-babel @vue/cli-plugin-eslint
```

Copy the provided frontend code to the respective files.

### 4. Initialize the database

```bash
# Navigate to backend directory
cd ../backend

# Activate virtual environment if not already activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run database initialization script
python init_db.py
```

### 5. Start the application

```bash
# Start the backend (from the backend directory)
uvicorn main:app --reload

- Backend API: http://localhost:8000

# In a new terminal, start the frontend (from the frontend directory)
cd ../frontend
npm run serve 
# npm run dev  # for Vite projects
# Frontend application: http://localhost:8080
```

Now you can access:
- Frontend application: http://localhost:8080
- Backend API: http://localhost:8000
- API documentation: http://localhost:8000/docs

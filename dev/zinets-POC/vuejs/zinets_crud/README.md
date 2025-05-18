# Chinese Character Manager

A Vue.js and FastAPI application for managing Chinese character data.

## Features

- **Search**: Find characters based on specific criteria
- **Read**: Retrieve character information from the database
- **Update**: Modify existing character information
- **Create**: Add a new character to the database
- **Soft-Delete**: Update character status to inactive

## Project Structure

```
chinese-character-manager/
├── frontend/                   # Vue.js frontend
│   ├── public/
│   ├── src/
│   │   ├── App.vue             # Main application component
│   │   ├── main.js             # Vue application entry point
│   │   └── ...
│   ├── package.json            # Frontend dependencies
│   └── ...
├── backend/                    # FastAPI backend
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Backend dependencies
│   └── ...
└── zinets_cache.sqlite         # SQLite database
```

## Requirements

### Frontend
- Node.js (v16+)
- npm or yarn

### Backend
- Python 3.8+
- FastAPI
- Uvicorn
- SQLite3

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install backend dependencies:
```bash
pip install fastapi uvicorn sqlalchemy pydantic python-multipart
```

3. Start the backend server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

1. Install frontend dependencies:
```bash
npm install
# or
yarn install
```

2. Start the development server:
```bash
npm run serve
# or
yarn serve
```

The application will be available at `http://localhost:8080`.

## Database Schema

The application uses SQLite with the following schema:

```sql
CREATE TABLE IF NOT EXISTS character_cache (
    character TEXT,
    pinyin TEXT,
    meaning TEXT,
    composition TEXT,
    phrases TEXT,
    llm_provider TEXT,
    llm_model_name TEXT,
    timestamp TEXT,
    is_active TEXT DEFAULT 'Y',
    is_best TEXT DEFAULT 'Y',
    PRIMARY KEY (character, llm_provider, llm_model_name)
)
```

## API Endpoints

- `GET /api/characters`: List all characters (with pagination and filtering)
- `GET /api/characters/{character}/{llm_provider}/{llm_model_name}`: Get a specific character
- `POST /api/characters`: Create a new character
- `PUT /api/characters/{character}/{llm_provider}/{llm_model_name}`: Update a character
- `PATCH /api/characters/{character}/{llm_provider}/{llm_model_name}/deactivate`: Deactivate a character (soft delete)

## Development

### Backend Development

- API documentation is available at `http://localhost:8000/docs` when the backend is running.
- You can test the API endpoints using the Swagger UI at this URL.

### Frontend Development

- Edit the Vue components in the `src` directory.
- The application uses Element Plus for the UI components.

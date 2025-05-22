import sqlite3
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import datetime

# Create FastAPI app
app = FastAPI(title="Chinese Character API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('zinets_cache.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic models
class CharacterBase(BaseModel):
    character: str
    pinyin: str
    meaning: str
    composition: str
    phrases: str
    llm_provider: str
    llm_model_name: str
    timestamp: str
    is_active: str = "Y"
    is_best: str = "Y"

class Character(CharacterBase):
    pass

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseModel):
    pinyin: Optional[str] = None
    meaning: Optional[str] = None
    composition: Optional[str] = None
    phrases: Optional[str] = None
    timestamp: Optional[str] = None
    is_active: Optional[str] = None
    is_best: Optional[str] = None

class CharacterResponse(BaseModel):
    items: List[Character]
    total: int

# Initialize database
@app.on_event("startup")
def startup_db_client():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
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
    ''')
    
    conn.commit()
    conn.close()

# API Routes
@app.get("/api/characters", response_model=CharacterResponse)
def get_characters(
    character: Optional[str] = None,
    pinyin: Optional[str] = None,
    meaning: Optional[str] = None,
    llm_provider: Optional[str] = None,
    llm_model_name: Optional[str] = None,
    is_active: Optional[str] = None,
    is_best: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    conn = Depends(get_db_connection)
):
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT * FROM character_cache WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM character_cache WHERE 1=1"
    params = []
    
    # Add filters
    if character:
        query += " AND character LIKE ?"
        count_query += " AND character LIKE ?"
        params.append(f"%{character}%")
    
    if pinyin:
        query += " AND pinyin LIKE ?"
        count_query += " AND pinyin LIKE ?"
        params.append(f"%{pinyin}%")
    
    if meaning:
        query += " AND meaning LIKE ?"
        count_query += " AND meaning LIKE ?"
        params.append(f"%{meaning}%")
    
    if llm_provider:
        query += " AND llm_provider = ?"
        count_query += " AND llm_provider = ?"
        params.append(llm_provider)
    
    if llm_model_name:
        query += " AND llm_model_name LIKE ?"
        count_query += " AND llm_model_name LIKE ?"
        params.append(f"%{llm_model_name}%")
    
    if is_active:
        query += " AND is_active = ?"
        count_query += " AND is_active = ?"
        params.append(is_active)
    
    if is_best:
        query += " AND is_best = ?"
        count_query += " AND is_best = ?"
        params.append(is_best)
    
    # Add pagination
    query += " ORDER BY character LIMIT ? OFFSET ?"
    params.extend([page_size, (page - 1) * page_size])
    
    # Execute queries
    cursor.execute(count_query, params[:-2] if params else [])
    total_count = cursor.fetchone()[0]
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert to list of dictionaries
    characters = [dict(row) for row in rows]
    
    conn.close()
    
    return {"items": characters, "total": total_count}

@app.get("/api/characters/{character}/{llm_provider}/{llm_model_name}", response_model=Character)
def get_character(
    character: str,
    llm_provider: str,
    llm_model_name: str,
    conn = Depends(get_db_connection)
):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM character_cache WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        (character, llm_provider, llm_model_name)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return dict(row)

@app.post("/api/characters", response_model=Character)
def create_character(
    character: CharacterCreate,
    conn = Depends(get_db_connection)
):
    cursor = conn.cursor()
    
    # Check if character already exists
    cursor.execute(
        "SELECT * FROM character_cache WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        (character.character, character.llm_provider, character.llm_model_name)
    )
    
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Character already exists")
    
    # Set timestamp if not provided
    if not character.timestamp:
        character.timestamp = datetime.datetime.now().isoformat()
    
    # Insert new character
    cursor.execute(
        """
        INSERT INTO character_cache 
        (character, pinyin, meaning, composition, phrases, llm_provider, llm_model_name, timestamp, is_active, is_best)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            character.character, character.pinyin, character.meaning, character.composition,
            character.phrases, character.llm_provider, character.llm_model_name,
            character.timestamp, character.is_active, character.is_best
        )
    )
    
    conn.commit()
    conn.close()
    
    return character

@app.put("/api/characters/{character}/{llm_provider}/{llm_model_name}", response_model=Character)
def update_character(
    character: str,
    llm_provider: str,
    llm_model_name: str,
    character_update: CharacterUpdate,
    conn = Depends(get_db_connection)
):
    cursor = conn.cursor()
    
    # Check if character exists
    cursor.execute(
        "SELECT * FROM character_cache WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        (character, llm_provider, llm_model_name)
    )
    
    existing_char = cursor.fetchone()
    if not existing_char:
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Update timestamp
    character_update_dict = character_update.dict(exclude_unset=True)
    if not character_update_dict.get("timestamp"):
        character_update_dict["timestamp"] = datetime.datetime.now().isoformat()
    
    # Build update query
    update_fields = []
    update_values = []
    
    for key, value in character_update_dict.items():
        if value is not None:
            update_fields.append(f"{key} = ?")
            update_values.append(value)
    
    if not update_fields:
        conn.close()
        return dict(existing_char)
    
    # Add primary key values
    update_values.extend([character, llm_provider, llm_model_name])
    
    # Execute update
    cursor.execute(
        f"UPDATE character_cache SET {', '.join(update_fields)} WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        update_values
    )
    
    conn.commit()
    
    # Get updated character
    cursor.execute(
        "SELECT * FROM character_cache WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        (character, llm_provider, llm_model_name)
    )
    
    updated_char = cursor.fetchone()
    conn.close()
    
    return dict(updated_char)

@app.patch("/api/characters/{character}/{llm_provider}/{llm_model_name}/deactivate")
def deactivate_character(
    character: str,
    llm_provider: str,
    llm_model_name: str,
    conn = Depends(get_db_connection)
):
    cursor = conn.cursor()
    
    # Check if character exists
    cursor.execute(
        "SELECT * FROM character_cache WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        (character, llm_provider, llm_model_name)
    )
    
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Soft delete - set is_active to 'N'
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute(
        "UPDATE character_cache SET is_active = 'N', timestamp = ? WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        (timestamp, character, llm_provider, llm_model_name)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Character deactivated successfully"}

# Run the application with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import sqlite3
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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

class CharacterCache(BaseModel):
    character: str
    pinyin: Optional[str] = None
    meaning: Optional[str] = None
    composition: Optional[str] = None
    phrases: Optional[str] = None

class CacheStats(BaseModel):
    total_characters: int
    active_characters: int
    providers: dict
    last_updated: Optional[str] = None



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
        character.timestamp = datetime.now().isoformat()
    
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
        character_update_dict["timestamp"] = datetime.now().isoformat()
    
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
    timestamp = datetime.now().isoformat()
    cursor.execute(
        "UPDATE character_cache SET is_active = 'N', timestamp = ? WHERE character = ? AND llm_provider = ? AND llm_model_name = ?",
        (timestamp, character, llm_provider, llm_model_name)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "Character deactivated successfully"}

# Endpoint 1: Check if character exists in cache (for LLM optimization)
@app.get("/api/characters/cache/{character}", response_model=CharacterCache)
def get_cached_character(character: str, conn = Depends(get_db_connection)):
    """
    Get character from cache if available.
    Returns 404 if not found, used by frontend to decide whether to call LLM API.
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT character, pinyin, meaning, composition, phrases 
        FROM character_cache 
        WHERE character = ? AND is_active = 'Y' AND is_best = 'Y'
        ORDER BY timestamp DESC
        LIMIT 1
    """, (character,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Character not found in cache")
    
    return CharacterCache(
        character=result[0],
        pinyin=result[1],
        meaning=result[2],
        composition=result[3],
        phrases=result[4]
    )

# Endpoint 2: Batch check for multiple characters
@app.post("/api/characters/cache/batch", response_model=List[CharacterCache])
def get_cached_characters_batch(characters: List[str], conn = Depends(get_db_connection)):
    """
    Check cache for multiple characters at once.
    Returns only characters that are found in cache.
    """
    cursor = conn.cursor()
    
    # Create placeholder string for SQL IN clause
    placeholders = ','.join('?' * len(characters))
    
    cursor.execute(f"""
        SELECT character, pinyin, meaning, composition, phrases 
        FROM character_cache 
        WHERE character IN ({placeholders}) 
        AND is_active = 'Y' AND is_best = 'Y'
        ORDER BY character
    """, characters)
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        CharacterCache(
            character=row[0],
            pinyin=row[1],
            meaning=row[2],
            composition=row[3],
            phrases=row[4]
        )
        for row in results
    ]

# Endpoint 3: Add character to cache (after LLM call)
@app.post("/api/characters/cache", response_model=dict)
def cache_character(character_data: CharacterCreate, conn = Depends(get_db_connection)):
    """
    Add character to cache after successful LLM API call.
    Handles both new characters and updates to existing ones.
    """
    cursor = conn.cursor()
    
    # Set timestamp
    character_data.timestamp = datetime.now().isoformat()
    
    try:
        # Try to insert new character
        cursor.execute('''
            INSERT INTO character_cache 
            (character, pinyin, meaning, composition, phrases, llm_provider, llm_model_name, timestamp, is_active, is_best)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Y', 'Y')
        ''', (
            character_data.character,
            character_data.pinyin,
            character_data.meaning,
            character_data.composition,
            character_data.phrases,
            character_data.llm_provider,
            character_data.llm_model_name,
            character_data.timestamp
        ))
        
        conn.commit()
        conn.close()
        
        return {"message": "Character cached successfully", "character": character_data.character}
        
    except sqlite3.IntegrityError:
        # Character already exists, update timestamp
        cursor.execute('''
            UPDATE character_cache 
            SET timestamp = ?, is_active = 'Y'
            WHERE character = ? AND llm_provider = ? AND llm_model_name = ?
        ''', (
            character_data.timestamp,
            character_data.character,
            character_data.llm_provider,
            character_data.llm_model_name
        ))
        
        conn.commit()
        conn.close()
        
        return {"message": "Character cache updated", "character": character_data.character}

# Endpoint 4: Get cache statistics
@app.get("/api/cache/stats", response_model=CacheStats)
def get_cache_statistics(conn = Depends(get_db_connection)):
    """
    Get statistics about the character cache.
    """
    cursor = conn.cursor()
    
    # Total characters
    cursor.execute("SELECT COUNT(*) FROM character_cache")
    total_count = cursor.fetchone()[0]
    
    # Active characters
    cursor.execute("SELECT COUNT(*) FROM character_cache WHERE is_active = 'Y'")
    active_count = cursor.fetchone()[0]
    
    # Provider distribution
    cursor.execute("""
        SELECT llm_provider, COUNT(*) 
        FROM character_cache 
        WHERE is_active = 'Y' 
        GROUP BY llm_provider
    """)
    providers = dict(cursor.fetchall())
    
    # Last updated
    cursor.execute("""
        SELECT timestamp 
        FROM character_cache 
        WHERE is_active = 'Y' 
        ORDER BY timestamp DESC 
        LIMIT 1
    """)
    result = cursor.fetchone()
    last_updated = result[0] if result else None
    
    conn.close()
    
    return CacheStats(
        total_characters=total_count,
        active_characters=active_count,
        providers=providers,
        last_updated=last_updated
    )

# Endpoint 5: Clear cache (soft delete)
@app.delete("/api/cache/clear")
def clear_character_cache(conn = Depends(get_db_connection)):
    """
    Clear all cached characters by marking them as inactive.
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE character_cache 
        SET is_active = 'N', timestamp = ?
        WHERE is_active = 'Y'
    """, (datetime.now().isoformat(),))
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    return {"message": f"Cache cleared. {affected_rows} characters marked as inactive."}

# Endpoint 6: Health check for ZiNets integration
@app.get("/api/zinets/health")
def zinets_health_check():
    """
    Simple health check endpoint for ZiNets visualization app.
    """
    return {
        "status": "healthy",
        "service": "zinets-backend",
        "features": ["character_cache", "llm_integration", "network_visualization"],
        "timestamp": datetime.now().isoformat()
    }


# Run the application with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

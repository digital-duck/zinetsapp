import sqlite3
# Add these endpoints to your existing zinets_crud FastAPI backend

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from datetime import datetime

# Add to your existing main.py

# Additional Pydantic models for ZiNets visualization
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

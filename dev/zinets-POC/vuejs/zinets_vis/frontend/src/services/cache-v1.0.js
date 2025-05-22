// services/cache.js - Character caching logic
import { cacheAPI } from './api.js'

/**
 * Character cache service that manages:
 * - Checking cache before LLM calls
 * - Storing results after LLM calls
 * - Cache statistics and management
 */
export class CacheService {
  constructor() {
    this.memoryCache = new Map() // In-memory cache for session
  }

  /**
   * Get character from cache (checks memory first, then backend)
   * @param {string} character - Chinese character
   * @returns {Object|null} Character data or null if not found
   */
  async getCharacter(character) {
    // Check memory cache first
    if (this.memoryCache.has(character)) {
      console.log(`Found ${character} in memory cache`)
      return this.memoryCache.get(character)
    }

    // Check backend cache
    try {
      const cachedData = await cacheAPI.getCharacter(character)
      if (cachedData) {
        // Store in memory cache for faster access
        this.memoryCache.set(character, cachedData)
        console.log(`Found ${character} in backend cache`)
        return cachedData
      }
    } catch (error) {
      // 404 means not in cache, other errors should be logged
      if (error.response?.status !== 404) {
        console.error(`Error checking cache for ${character}:`, error)
      }
    }

    return null
  }

  /**
   * Get multiple characters from cache
   * @param {string[]} characters - Array of Chinese characters
   * @returns {Object} Object with character as key, data as value
   */
  async getCharactersBatch(characters) {
    const result = {}
    const missingCharacters = []

    // Check memory cache first
    for (const char of characters) {
      if (this.memoryCache.has(char)) {
        result[char] = this.memoryCache.get(char)
      } else {
        missingCharacters.push(char)
      }
    }

    // Check backend for missing characters
    if (missingCharacters.length > 0) {
      try {
        const cachedData = await cacheAPI.getCharactersBatch(missingCharacters)
        
        // Add to both result and memory cache
        for (const data of cachedData) {
          result[data.character] = data
          this.memoryCache.set(data.character, data)
        }
      } catch (error) {
        console.error('Error batch checking cache:', error)
      }
    }

    return result
  }

  /**
   * Add character to cache (both memory and backend)
   * @param {string} character - Chinese character
   * @param {Object} data - Character data
   */
  async addCharacter(character, data) {
    // Skip placeholder data
    if (this.isPlaceholderData(data)) {
      return
    }

    try {
      // Add to backend cache
      await cacheAPI.addCharacter({
        character: character,
        pinyin: data.pinyin,
        meaning: data.meaning,
        composition: data.composition,
        phrases: data.phrases,
        llm_provider: 'Google',
        llm_model_name: 'gemini-2.0-flash'
      })

      // Add to memory cache
      this.memoryCache.set(character, data)
      
      console.log(`Cached character: ${character}`)
    } catch (error) {
      console.error(`Failed to cache character ${character}:`, error)
    }
  }

  /**
   * Add multiple characters to cache
   * @param {Object} charactersData - Object with character as key, data as value
   */
  async addCharactersBatch(charactersData) {
    const promises = []
    
    for (const [character, data] of Object.entries(charactersData)) {
      promises.push(this.addCharacter(character, data))
    }

    await Promise.allSettled(promises)
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  async getStats() {
    try {
      const stats = await cacheAPI.getStats()
      return {
        ...stats,
        memoryCache: this.memoryCache.size
      }
    } catch (error) {
      console.error('Error getting cache stats:', error)
      return {
        total_characters: 0,
        active_characters: 0,
        providers: {},
        last_updated: null,
        memoryCache: this.memoryCache.size
      }
    }
  }

  /**
   * Clear all cache (both memory and backend)
   */
  async clearCache() {
    try {
      // Clear backend cache
      await cacheAPI.clearCache()
      
      // Clear memory cache
      this.memoryCache.clear()
      
      console.log('Cache cleared successfully')
      return true
    } catch (error) {
      console.error('Error clearing cache:', error)
      return false
    }
  }

  /**
   * Clear only memory cache (keep backend cache)
   */
  clearMemoryCache() {
    this.memoryCache.clear()
    console.log('Memory cache cleared')
  }

  /**
   * Check if data is placeholder data (don't cache placeholders)
   * @param {Object} data - Character data
   * @returns {boolean}
   */
  isPlaceholderData(data) {
    return data.pinyin === 'Unknown' && data.meaning === 'Meaning not available'
  }

  /**
   * Get all characters from memory cache
   * @returns {string[]} Array of cached character keys
   */
  getMemoryCacheKeys() {
    return Array.from(this.memoryCache.keys())
  }

  /**
   * Check if character exists in memory cache
   * @param {string} character - Chinese character
   * @returns {boolean}
   */
  hasInMemory(character) {
    return this.memoryCache.has(character)
  }

  /**
   * Preload characters into memory cache
   * @param {string[]} characters - Characters to preload
   */
  async preloadCharacters(characters) {
    console.log(`Preloading ${characters.length} characters...`)
    
    const cachedData = await this.getCharactersBatch(characters)
    const loadedCount = Object.keys(cachedData).length
    
    console.log(`Preloaded ${loadedCount}/${characters.length} characters`)
    return cachedData
  }
}

// Export singleton instance
export default new CacheService()

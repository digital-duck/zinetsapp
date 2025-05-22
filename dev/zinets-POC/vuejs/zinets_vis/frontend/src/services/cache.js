// services/cache.js - Character caching logic
import { cacheAPI } from './api.js'

/**
 * Character cache service that manages:
 * - Checking cache before LLM calls
 * - Storing results after LLM calls  
 * - Cache statistics and management
 * - Memory cache for session performance
 */
export class CacheService {
  constructor() {
    this.memoryCache = new Map() // In-memory cache for session
    this.cacheHits = 0
    this.cacheMisses = 0
  }

  /**
   * Get character from cache (checks memory first, then backend)
   * @param {string} character - Chinese character
   * @returns {Object|null} Character data or null if not found
   */
  async getCachedCharacter(character) {
    if (!character) return null

    // Check memory cache first
    if (this.memoryCache.has(character)) {
      this.cacheHits++
      console.log(`Found ${character} in memory cache`)
      const data = this.memoryCache.get(character)
      return { ...data, cached: true }
    }

    // Check backend cache
    try {
      const cachedData = await cacheAPI.getCharacter(character)
      if (cachedData) {
        this.cacheHits++
        // Store in memory cache for faster access
        const processedData = this.processBackendData(cachedData)
        this.memoryCache.set(character, processedData)
        console.log(`Found ${character} in backend cache`)
        return { ...processedData, cached: true }
      }
    } catch (error) {
      console.error(`Error checking cache for ${character}:`, error)
    }

    this.cacheMisses++
    return null
  }

  /**
   * Get multiple characters from cache
   * @param {string[]} characters - Array of Chinese characters
   * @returns {Object} Object with character as key, data as value
   */
  async getCachedCharactersBatch(characters) {
    if (!characters || characters.length === 0) return {}

    const result = {}
    const missingCharacters = []

    // Check memory cache first
    for (const char of characters) {
      if (this.memoryCache.has(char)) {
        this.cacheHits++
        result[char] = { ...this.memoryCache.get(char), cached: true }
      } else {
        missingCharacters.push(char)
      }
    }

    // Check backend for missing characters
    if (missingCharacters.length > 0) {
      try {
        const cachedData = await cacheAPI.getCharactersBatch(missingCharacters)
        
        // Process and add to both result and memory cache
        for (const data of cachedData) {
          const processedData = this.processBackendData(data)
          result[data.character] = { ...processedData, cached: true }
          this.memoryCache.set(data.character, processedData)
          this.cacheHits++
        }

        // Count misses for characters not found in backend
        const foundCharacters = cachedData.map(d => d.character)
        const stillMissing = missingCharacters.filter(char => !foundCharacters.includes(char))
        this.cacheMisses += stillMissing.length

      } catch (error) {
        console.error('Error batch checking cache:', error)
        this.cacheMisses += missingCharacters.length
      }
    }

    return result
  }

  /**
   * Cache character data (both memory and backend)
   * @param {string} character - Chinese character
   * @param {Object} data - Character data
   * @param {string} llmProvider - LLM provider name
   * @param {string} llmModel - LLM model name
   */
  async cacheCharacter(character, data, llmProvider = 'Google', llmModel = 'gemini-2.0-flash') {
    if (!character || !data) return false

    // Skip placeholder data
    if (this.isPlaceholderData(data)) {
      console.log(`Skipping cache for placeholder data: ${character}`)
      return false
    }

    try {
      // Prepare data for backend
      const backendData = {
        character: character,
        pinyin: data.pinyin,
        meaning: data.meaning,
        composition: data.composition,
        phrases: data.phrases,
        llm_provider: llmProvider,
        llm_model_name: llmModel,
        timestamp: new Date().toISOString(),
        is_active: 'Y',
        is_best: 'Y'
      }

      // Add to backend cache
      await cacheAPI.addCharacter(backendData)

      // Add to memory cache
      this.memoryCache.set(character, data)
      
      console.log(`Successfully cached character: ${character}`)
      return true
    } catch (error) {
      console.error(`Failed to cache character ${character}:`, error)
      return false
    }
  }

  /**
   * Cache multiple characters
   * @param {Object} charactersData - Object with character as key, data as value
   * @param {string} llmProvider - LLM provider name
   * @param {string} llmModel - LLM model name
   */
  async cacheCharactersBatch(charactersData, llmProvider = 'Google', llmModel = 'gemini-2.0-flash') {
    if (!charactersData || Object.keys(charactersData).length === 0) return { success: 0, failed: 0 }

    let successCount = 0
    let failedCount = 0

    // Filter out placeholder data
    const validCharacters = Object.entries(charactersData).filter(([char, data]) => 
      !this.isPlaceholderData(data)
    )

    if (validCharacters.length === 0) {
      console.log('No valid characters to cache (all are placeholders)')
      return { success: 0, failed: 0 }
    }

    try {
      // Prepare batch data for backend
      const batchData = validCharacters.map(([character, data]) => ({
        character: character,
        pinyin: data.pinyin,
        meaning: data.meaning,
        composition: data.composition,
        phrases: data.phrases,
        llm_provider: llmProvider,
        llm_model_name: llmModel,
        timestamp: new Date().toISOString(),
        is_active: 'Y',
        is_best: 'Y'
      }))

      // Add to backend cache in batch
      await cacheAPI.addCharactersBatch(batchData)

      // Add to memory cache
      for (const [character, data] of validCharacters) {
        this.memoryCache.set(character, data)
        successCount++
      }

      console.log(`Successfully cached ${successCount} characters in batch`)
    } catch (error) {
      console.error('Failed to cache characters in batch:', error)
      
      // Fallback to individual caching
      console.log('Falling back to individual character caching...')
      for (const [character, data] of validCharacters) {
        const success = await this.cacheCharacter(character, data, llmProvider, llmModel)
        if (success) {
          successCount++
        } else {
          failedCount++
        }
      }
    }

    return { success: successCount, failed: failedCount }
  }

  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  async getCacheStatistics() {
    try {
      const backendStats = await cacheAPI.getStats()
      return {
        ...backendStats,
        memoryCache: this.memoryCache.size,
        cacheHits: this.cacheHits,
        cacheMisses: this.cacheMisses,
        hitRate: this.cacheHits + this.cacheMisses > 0 
          ? ((this.cacheHits / (this.cacheHits + this.cacheMisses)) * 100).toFixed(2) + '%'
          : '0%'
      }
    } catch (error) {
      console.error('Error getting cache stats:', error)
      return {
        total_characters: 0,
        active_characters: 0,
        providers: {},
        last_updated: null,
        memoryCache: this.memoryCache.size,
        cacheHits: this.cacheHits,
        cacheMisses: this.cacheMisses,
        hitRate: this.cacheHits + this.cacheMisses > 0 
          ? ((this.cacheHits / (this.cacheHits + this.cacheMisses)) * 100).toFixed(2) + '%'
          : '0%'
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
      
      // Reset statistics
      this.cacheHits = 0
      this.cacheMisses = 0
      
      console.log('Cache cleared successfully')
      return true
    } catch (error) {
      console.error('Error clearing cache:', error)
      return false
    }
  }

  /**
   * Clear specific characters from cache
   * @param {string[]} characters - Characters to clear
   */
  async clearCharacters(characters) {
    try {
      // Clear from backend
      await cacheAPI.clearCharacters(characters)
      
      // Clear from memory cache
      for (const char of characters) {
        this.memoryCache.delete(char)
      }
      
      console.log(`Cleared ${characters.length} characters from cache`)
      return true
    } catch (error) {
      console.error('Error clearing specific characters:', error)
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
    return !data || 
           data.pinyin === 'Unknown' || 
           data.meaning === 'Meaning not available' ||
           data.placeholder === true
  }

  /**
   * Process backend data to frontend format
   * @param {Object} backendData - Data from backend
   * @returns {Object} Processed data
   */
  processBackendData(backendData) {
    return {
      pinyin: backendData.pinyin,
      meaning: backendData.meaning,
      composition: backendData.composition,
      phrases: backendData.phrases,
      llmProvider: backendData.llm_provider,
      llmModel: backendData.llm_model_name,
      timestamp: backendData.timestamp
    }
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
    if (!characters || characters.length === 0) return {}

    console.log(`Preloading ${characters.length} characters...`)
    
    const cachedData = await this.getCachedCharactersBatch(characters)
    const loadedCount = Object.keys(cachedData).length
    
    console.log(`Preloaded ${loadedCount}/${characters.length} characters`)
    return cachedData
  }

  /**
   * Get memory cache size
   * @returns {number} Number of characters in memory cache
   */
  getMemoryCacheSize() {
    return this.memoryCache.size
  }

  /**
   * Get cache hit/miss statistics
   * @returns {Object} Cache performance stats
   */
  getCachePerformance() {
    const total = this.cacheHits + this.cacheMisses
    return {
      hits: this.cacheHits,
      misses: this.cacheMisses,
      total: total,
      hitRate: total > 0 ? ((this.cacheHits / total) * 100).toFixed(2) + '%' : '0%'
    }
  }

  /**
   * Reset cache performance statistics
   */
  resetCacheStats() {
    this.cacheHits = 0
    this.cacheMisses = 0
    console.log('Cache statistics reset')
  }
}

// Export singleton instance
export default new CacheService()
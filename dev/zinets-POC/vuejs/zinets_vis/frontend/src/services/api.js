// services/api.js - Backend API calls
import axios from 'axios'

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000, // 30 seconds to match settings
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for unified error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error(`API Error ${error.response.status}:`, error.response.data)
    } else if (error.request) {
      // Request was made but no response received
      console.error('API Network Error:', error.message)
    } else {
      // Something happened setting up the request
      console.error('API Setup Error:', error.message)
    }
    return Promise.reject(error)
  }
)

// Character cache operations
export const cacheAPI = {
  // Check if character exists in cache
  async getCharacter(character) {
    try {
      const response = await api.get(`/characters/cache/${encodeURIComponent(character)}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 404) {
        return null // Character not in cache
      }
      throw new Error(`Failed to get character from cache: ${error.message}`)
    }
  },

  // Check multiple characters at once
  async getCharactersBatch(characters) {
    try {
      const response = await api.post('/characters/cache/batch', { characters })
      return response.data.characters || []
    } catch (error) {
      throw new Error(`Failed to get characters batch from cache: ${error.message}`)
    }
  },

  // Add character to cache after LLM call
  async addCharacter(characterData) {
    try {
      const response = await api.post('/characters/cache', characterData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to add character to cache: ${error.message}`)
    }
  },

  // Add multiple characters to cache
  async addCharactersBatch(charactersData) {
    try {
      const response = await api.post('/characters/cache/batch-add', { characters: charactersData })
      return response.data
    } catch (error) {
      throw new Error(`Failed to add characters batch to cache: ${error.message}`)
    }
  },

  // Get cache statistics
  async getStats() {
    try {
      const response = await api.get('/cache/stats')
      return response.data
    } catch (error) {
      throw new Error(`Failed to get cache statistics: ${error.message}`)
    }
  },

  // Clear all cache
  async clearCache() {
    try {
      const response = await api.delete('/cache/clear')
      return response.data
    } catch (error) {
      throw new Error(`Failed to clear cache: ${error.message}`)
    }
  },

  // Clear specific characters from cache
  async clearCharacters(characters) {
    try {
      const response = await api.delete('/cache/characters', { 
        data: { characters } 
      })
      return response.data
    } catch (error) {
      throw new Error(`Failed to clear specific characters from cache: ${error.message}`)
    }
  },

  // Update character in cache
  async updateCharacter(character, characterData) {
    try {
      const response = await api.put(`/characters/cache/${encodeURIComponent(character)}`, characterData)
      return response.data
    } catch (error) {
      throw new Error(`Failed to update character in cache: ${error.message}`)
    }
  },

  // Health check
  async healthCheck() {
    try {
      const response = await api.get('/health')
      return response.data
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`)
    }
  },

  // Get cache info for specific character
  async getCharacterInfo(character) {
    try {
      const response = await api.get(`/characters/cache/${encodeURIComponent(character)}/info`)
      return response.data
    } catch (error) {
      if (error.response?.status === 404) {
        return null
      }
      throw new Error(`Failed to get character info: ${error.message}`)
    }
  }
}

// Update axios instance configuration (for dynamic settings)
export const updateApiConfig = (config) => {
  if (config.baseURL) {
    api.defaults.baseURL = config.baseURL
  }
  if (config.timeout) {
    api.defaults.timeout = config.timeout
  }
  if (config.headers) {
    Object.assign(api.defaults.headers, config.headers)
  }
}

// Get current API configuration
export const getApiConfig = () => ({
  baseURL: api.defaults.baseURL,
  timeout: api.defaults.timeout,
  headers: { ...api.defaults.headers }
})

export default api
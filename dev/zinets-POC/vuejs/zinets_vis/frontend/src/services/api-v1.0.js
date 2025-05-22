// services/api.js - Backend API calls (similar to zinets_crud)
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Character cache operations
export const cacheAPI = {
  // Check if character exists in cache
  async getCharacter(character) {
    try {
      const response = await api.get(`/characters/cache/${character}`)
      return response.data
    } catch (error) {
      if (error.response?.status === 404) {
        return null // Character not in cache
      }
      throw error
    }
  },

  // Check multiple characters at once
  async getCharactersBatch(characters) {
    const response = await api.post('/characters/cache/batch', characters)
    return response.data
  },

  // Add character to cache after LLM call
  async addCharacter(characterData) {
    const response = await api.post('/characters/cache', characterData)
    return response.data
  },

  // Get cache statistics
  async getStats() {
    const response = await api.get('/cache/stats')
    return response.data
  },

  // Clear cache
  async clearCache() {
    const response = await api.delete('/cache/clear')
    return response.data
  },

  // Health check
  async healthCheck() {
    const response = await api.get('/zinets/health')
    return response.data
  }
}

export default api

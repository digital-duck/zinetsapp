// API service for character operations
import axios from 'axios'

// Configure axios defaults
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
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

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error)
    
    // Handle common error scenarios
    if (error.response) {
      // Server responded with error status
      console.error('Error Status:', error.response.status)
      console.error('Error Data:', error.response.data)
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received:', error.request)
    } else {
      // Something else happened
      console.error('Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

// Character API service
export const characterService = {
  // Get all characters with pagination and filtering
  async getCharacters(params = {}) {
    try {
      const response = await api.get('/characters', { params })
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch characters')
    }
  },

  // Get a specific character
  async getCharacter(character, llmProvider, llmModelName) {
    try {
      const response = await api.get(`/characters/${character}/${llmProvider}/${llmModelName}`)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch character')
    }
  },

  // Create a new character
  async createCharacter(characterData) {
    try {
      const response = await api.post('/characters', characterData)
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create character')
    }
  },

  // Update an existing character
  async updateCharacter(character, llmProvider, llmModelName, characterData) {
    try {
      const response = await api.put(
        `/characters/${character}/${llmProvider}/${llmModelName}`,
        characterData
      )
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update character')
    }
  },

  // Deactivate a character (soft delete)
  async deactivateCharacter(character, llmProvider, llmModelName) {
    try {
      const response = await api.patch(
        `/characters/${character}/${llmProvider}/${llmModelName}/deactivate`
      )
      return response.data
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to deactivate character')
    }
  },
}

// Export the configured axios instance for direct use if needed
export default api

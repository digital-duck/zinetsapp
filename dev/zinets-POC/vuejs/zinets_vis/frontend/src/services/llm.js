// services/llm.js - LLM service for Gemini API
import cacheService from './cache.js'

const GEMINI_API_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models'

// Available Gemini models
export const GEMINI_MODELS = [
  'gemini-2.0-flash',
  'gemini-2.5-flash', 
  'gemini-1.5-flash',
  'gemini-2.5-pro'
]

// Base prompt template
const BASE_PROMPT = `
For each character, provide the following information in this format:
- pinyin: the pronunciation with tone marks
- meaning: main meanings  
- composition: how character is structurally composed from radicals and parts
- phrases: 5 common phrases with pinyin and meaning

Ensure explanation texts are in the target language of '{language}'.

Format character's information like this:

Character: [character]
pinyin: [pronunciation]
meaning: [meanings]
composition: [explanation]
phrases: [phrase1]<br>[phrase2]<br>[phrase3]<br>[phrase4]<br>[phrase5]

Start each character with "Character:" on a new line.
Do not include any other formatting, explanations, or markdown.
`

export class LLMService {
  constructor() {
    this.apiKey = null
    this.model = GEMINI_MODELS[0]
    this.requestCount = 0
    this.totalTokensUsed = 0
    this.lastRequestTime = null
  }

  /**
   * Set Gemini API key
   * @param {string} apiKey - Gemini API key
   */
  setApiKey(apiKey) {
    this.apiKey = apiKey
  }

  /**
   * Set Gemini model
   * @param {string} model - Model name
   */
  setModel(model) {
    if (GEMINI_MODELS.includes(model)) {
      this.model = model
    } else {
      console.warn(`Invalid model: ${model}. Using default: ${this.model}`)
    }
  }

  /**
   * Get character data with caching
   * @param {string|string[]} characters - Character(s) to fetch
   * @param {string} language - Target language
   * @param {boolean} useCache - Whether to use cache
   * @param {number} chunkSize - Batch size for processing
   * @returns {Object} Character data
   */
  async getCharacterData(characters, language = 'English', useCache = true, chunkSize = 10) {
    // Normalize input to array
    const charArray = Array.isArray(characters) ? characters : [characters]
    const result = {}
    let charactersToFetch = [...charArray]

    // Step 1: Check cache for all characters
    if (useCache) {
      try {
        const cachedData = await cacheService.getCachedCharactersBatch(charArray)
        
        // Add cached data to result and remove from fetch list
        Object.entries(cachedData).forEach(([char, data]) => {
          result[char] = data
          charactersToFetch = charactersToFetch.filter(c => c !== char)
        })
        
        console.log(`Found ${Object.keys(cachedData).length} characters in cache`)
      } catch (error) {
        console.error('Error checking cache:', error)
      }
    }

    // Step 2: Fetch missing characters from Gemini
    if (charactersToFetch.length > 0 && this.apiKey) {
      console.log(`Fetching ${charactersToFetch.length} characters from Gemini...`)
      
      try {
        const geminiData = await this.fetchFromGemini(charactersToFetch, language, chunkSize)
        
        // Step 3: Cache the new data
        if (useCache && Object.keys(geminiData).length > 0) {
          await cacheService.cacheCharactersBatch(geminiData, 'Google', this.model)
        }
        
        // Add to result
        Object.assign(result, geminiData)
      } catch (error) {
        console.error('Error fetching from Gemini:', error)
      }
    } else if (charactersToFetch.length > 0 && !this.apiKey) {
      console.warn('No API key set, cannot fetch from Gemini')
    }

    // Step 4: Generate placeholders for any remaining characters
    for (const char of charArray) {
      if (!result[char]) {
        result[char] = this.generatePlaceholder(char)
      }
    }

    // Return single object if input was single character
    if (typeof characters === 'string') {
      return result[characters]
    }

    return result
  }

  /**
   * Fetch characters from Gemini API
   * @param {string[]} characters - Characters to fetch
   * @param {string} language - Target language
   * @param {number} chunkSize - Batch size
   * @returns {Object} Character data
   */
  async fetchFromGemini(characters, language, chunkSize = 10) {
    if (!this.apiKey) {
      throw new Error('Gemini API key not set')
    }

    const result = {}
    const chunks = this.chunkArray(characters, chunkSize)

    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i]
      
      try {
        let chunkData = {}
        
        if (chunk.length > 1) {
          // Batch processing
          chunkData = await this.processBatch(chunk, language)
        } else {
          // Individual processing
          const charData = await this.processIndividual(chunk[0], language)
          if (charData) {
            chunkData[chunk[0]] = charData
          }
        }
        
        // Add to result
        Object.assign(result, chunkData)
        
        // Rate limiting delay between chunks
        if (i < chunks.length - 1) {
          const delay = Math.min(1000 + (i * 200), 3000) // Progressive delay
          await this.delay(delay)
        }
        
      } catch (error) {
        console.error(`Error processing chunk ${i + 1}:`, error)
        
        // Generate placeholders for failed chunk
        for (const char of chunk) {
          if (!result[char]) {
            result[char] = this.generatePlaceholder(char)
          }
        }
      }
    }

    return result
  }

  /**
   * Process batch of characters
   * @param {string[]} characters - Characters to process
   * @param {string} language - Target language
   * @returns {Object} Character data
   */
  async processBatch(characters, language) {
    const charactersStr = characters.map(char => `'${char}'`).join(', ')
    const prompt = `Generate information about these Chinese characters: ${charactersStr}\n\n${BASE_PROMPT.replace('{language}', language)}`
    
    const response = await this.callGeminiAPI(prompt)
    return this.parseGeminiResponse(response, characters)
  }

  /**
   * Process individual character
   * @param {string} character - Character to process
   * @param {string} language - Target language
   * @returns {Object} Character data
   */
  async processIndividual(character, language) {
    const prompt = `Generate information about this Chinese character '${character}'\n\n${BASE_PROMPT.replace('{language}', language)}`
    
    const response = await this.callGeminiAPI(prompt)
    const parsed = this.parseGeminiResponse(response, [character])
    return parsed[character] || this.generatePlaceholder(character)
  }

  /**
   * Call Gemini API
   * @param {string} prompt - Prompt to send
   * @returns {string} API response text
   */
  async callGeminiAPI(prompt) {
    if (!this.apiKey) {
      throw new Error('Gemini API key not set')
    }

    const url = `${GEMINI_API_BASE_URL}/${this.model}:generateContent?key=${this.apiKey}`
    
    const requestBody = {
      contents: [{
        parts: [{ text: prompt }]
      }],
      generationConfig: {
        temperature: 0.2,
        topP: 0.95,
        topK: 40,
        maxOutputTokens: 8192,
        candidateCount: 1,
        stopSequences: []
      },
      safetySettings: [
        {
          category: "HARM_CATEGORY_HARASSMENT",
          threshold: "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
          category: "HARM_CATEGORY_HATE_SPEECH", 
          threshold: "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
          category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
          threshold: "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
          category: "HARM_CATEGORY_DANGEROUS_CONTENT",
          threshold: "BLOCK_MEDIUM_AND_ABOVE"
        }
      ]
    }

    // Record request time
    this.lastRequestTime = new Date()
    this.requestCount++

    const response = await fetch(url, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'User-Agent': 'ZiNets-Vis/1.0'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(`Gemini API error ${response.status}: ${errorData.error?.message || response.statusText}`)
    }

    const data = await response.json()
    
    // Check for safety issues or content blocks
    if (data.candidates?.[0]?.finishReason === 'SAFETY') {
      throw new Error('Content blocked by Gemini safety filters')
    }
    
    if (!data.candidates?.[0]?.content?.parts?.[0]?.text) {
      throw new Error('Invalid Gemini API response: no text content found')
    }

    // Update token usage if available
    if (data.usageMetadata?.totalTokenCount) {
      this.totalTokensUsed += data.usageMetadata.totalTokenCount
    }

    return data.candidates[0].content.parts[0].text
  }

  /**
   * Parse Gemini response to extract character data
   * @param {string} responseText - API response text
   * @param {string[]} expectedCharacters - Expected characters
   * @returns {Object} Parsed character data
   */
  parseGeminiResponse(responseText, expectedCharacters) {
    const result = {}
    const lines = responseText.split('\n')
    
    let currentChar = null
    let currentData = {}
    let currentField = null
    
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      
      if (trimmed.startsWith('Character:')) {
        // Save previous character if valid
        if (currentChar && this.isValidCharacterData(currentData)) {
          result[currentChar] = currentData
        }
        
        // Start new character - find matching character
        const charPart = trimmed.split(':', 1)[1]?.trim()
        currentChar = expectedCharacters.find(char => charPart?.includes(char)) || null
        currentData = {}
        currentField = null
        
      } else if (trimmed.includes(':') && !trimmed.startsWith('phrases:')) {
        // Parse field (handle special case for phrases field)
        const colonIndex = trimmed.indexOf(':')
        const fieldName = trimmed.substring(0, colonIndex).trim().toLowerCase()
        const fieldValue = trimmed.substring(colonIndex + 1).trim()
        
        if (['pinyin', 'meaning', 'composition', 'phrases'].includes(fieldName)) {
          currentData[fieldName] = fieldValue
          currentField = fieldName
        }
        
      } else if (currentField) {
        // Continue previous field
        currentData[currentField] += ' ' + trimmed
      }
    }
    
    // Don't forget the last character
    if (currentChar && this.isValidCharacterData(currentData)) {
      result[currentChar] = currentData
    }
    
    return result
  }

  /**
   * Validate character data completeness
   * @param {Object} data - Character data
   * @returns {boolean} Whether data is complete
   */
  isValidCharacterData(data) {
    const requiredFields = ['pinyin', 'meaning', 'composition', 'phrases']
    return requiredFields.every(field => 
      data[field] && 
      typeof data[field] === 'string' && 
      data[field].trim().length > 0
    )
  }

  /**
   * Generate placeholder data for a character
   * @param {string} character - Chinese character
   * @returns {Object} Placeholder data
   */
  generatePlaceholder(character) {
    return {
      pinyin: 'Unknown',
      meaning: 'Meaning not available',
      composition: 'Composition not available',
      phrases: `${character}语 - Example phrase 1<br>${character}文 - Example phrase 2<br>${character}词 - Example phrase 3<br>${character}句 - Example phrase 4<br>${character}话 - Example phrase 5`,
      placeholder: true,
      timestamp: new Date().toISOString()
    }
  }

  /**
   * Split array into chunks
   * @param {Array} array - Array to chunk
   * @param {number} size - Chunk size
   * @returns {Array[]} Array of chunks
   */
  chunkArray(array, size) {
    const chunks = []
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size))
    }
    return chunks
  }

  /**
   * Delay execution
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise} Promise that resolves after delay
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * Test API connection
   * @returns {boolean} Whether API is working
   */
  async testConnection() {
    if (!this.apiKey) {
      throw new Error('No API key set')
    }

    try {
      const testPrompt = "Generate information about the Chinese character '心' in this format:\n\nCharacter: 心\npinyin: xīn\nmeaning: heart\ncomposition: pictographic\nphrases: 心情<br>中心<br>小心<br>心理<br>爱心"
      
      const response = await this.callGeminiAPI(testPrompt)
      
      // Simple validation - check if response contains expected content
      return response.includes('Character:') && response.includes('pinyin:')
      
    } catch (error) {
      console.error('API test failed:', error)
      throw error
    }
  }

  /**
   * Get service statistics
   * @returns {Object} Service statistics
   */
  getStatistics() {
    return {
      apiKey: this.apiKey ? '***' + this.apiKey.slice(-4) : 'Not set',
      model: this.model,
      requestCount: this.requestCount,
      totalTokensUsed: this.totalTokensUsed,
      lastRequestTime: this.lastRequestTime,
      averageTokensPerRequest: this.requestCount > 0 
        ? Math.round(this.totalTokensUsed / this.requestCount) 
        : 0
    }
  }

  /**
   * Reset statistics
   */
  resetStatistics() {
    this.requestCount = 0
    this.totalTokensUsed = 0
    this.lastRequestTime = null
    console.log('LLM service statistics reset')
  }

  /**
   * Get available models
   * @returns {string[]} Available Gemini models
   */
  getAvailableModels() {
    return [...GEMINI_MODELS]
  }

  /**
   * Validate API key format
   * @param {string} apiKey - API key to validate
   * @returns {boolean} Whether API key format is valid
   */
  validateApiKey(apiKey) {
    if (!apiKey || typeof apiKey !== 'string') return false
    
    // Gemini API keys typically start with 'AIza' and are around 39 characters long
    const keyPattern = /^AIza[a-zA-Z0-9_-]{35}$/
    return keyPattern.test(apiKey.trim())
  }

  /**
   * Get estimated cost (rough estimate based on token usage)
   * @returns {Object} Cost estimation
   */
  getEstimatedCost() {
    // Rough estimates for Gemini pricing (subject to change)
    const pricePerToken = 0.00015 / 1000 // Approximate price per token
    const estimatedCost = this.totalTokensUsed * pricePerToken
    
    return {
      totalTokens: this.totalTokensUsed,
      estimatedCostUSD: estimatedCost.toFixed(4),
      requests: this.requestCount
    }
  }
}

// Export singleton instance
export default new LLMService()
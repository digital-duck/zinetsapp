// services/llm.js - LLM service for Gemini API
import { cacheAPI } from './api.js'

const GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models'

// Base prompt from your Python script
const BASE_PROMPT = `
For each character, provide the following information in this format:
- pinyin: the pronunciation with tone marks
- meaning: main meanings  
- composition: how character is structurally composed from radicals and parts
- phrases: 5 common phrases with pinyin and meaning

Ensure explanation texts are in the target language of '{language}'

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
    this.model = 'gemini-2.0-flash'
  }

  setApiKey(apiKey) {
    this.apiKey = apiKey
  }

  // Main function: get character data with caching
  async getCharacterData(characters, language = 'English', useCache = true) {
    const result = {}
    let charactersToFetch = [...characters]

    // Step 1: Check cache for all characters
    if (useCache) {
      try {
        const cachedCharacters = await cacheAPI.getCharactersBatch(characters)
        
        for (const cached of cachedCharacters) {
          result[cached.character] = cached
          charactersToFetch = charactersToFetch.filter(char => char !== cached.character)
        }
        
        console.log(`Found ${cachedCharacters.length} characters in cache`)
      } catch (error) {
        console.error('Error checking cache:', error)
      }
    }

    // Step 2: Fetch missing characters from Gemini
    if (charactersToFetch.length > 0 && this.apiKey) {
      console.log(`Fetching ${charactersToFetch.length} characters from Gemini...`)
      
      const geminiData = await this.fetchFromGemini(charactersToFetch, language)
      
      // Step 3: Cache the new data
      if (useCache) {
        await this.cacheCharacters(geminiData)
      }
      
      Object.assign(result, geminiData)
    }

    // Step 4: Generate placeholders for any remaining characters
    for (const char of characters) {
      if (!result[char]) {
        result[char] = this.generatePlaceholder(char)
      }
    }

    return result
  }

  // Fetch characters from Gemini API
  async fetchFromGemini(characters, language) {
    if (!this.apiKey) {
      throw new Error('Gemini API key not set')
    }

    const result = {}
    const chunkSize = 10
    const chunks = this.chunkArray(characters, chunkSize)

    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i]
      
      try {
        if (chunk.length > 1) {
          // Batch processing
          const batchData = await this.processBatch(chunk, language)
          Object.assign(result, batchData)
        } else {
          // Individual processing
          const charData = await this.processIndividual(chunk[0], language)
          if (charData) {
            result[chunk[0]] = charData
          }
        }
        
        // Rate limiting delay
        if (i < chunks.length - 1) {
          await this.delay(1000)
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

  // Process batch of characters
  async processBatch(characters, language) {
    const charactersStr = characters.map(char => `'${char}'`).join(', ')
    const prompt = `Generate information about these Chinese characters: ${charactersStr}\n\n${BASE_PROMPT.replace('{language}', language)}`
    
    const response = await this.callGeminiAPI(prompt)
    return this.parseResponse(response, characters)
  }

  // Process individual character
  async processIndividual(character, language) {
    const prompt = `Generate information about this Chinese character '${character}'\n\n${BASE_PROMPT.replace('{language}', language)}`
    
    const response = await this.callGeminiAPI(prompt)
    const parsed = this.parseResponse(response, [character])
    return parsed[character] || this.generatePlaceholder(character)
  }

  // Call Gemini API
  async callGeminiAPI(prompt) {
    const url = `${GEMINI_API_URL}/${this.model}:generateContent?key=${this.apiKey}`
    
    const requestBody = {
      contents: [{
        parts: [{ text: prompt }]
      }],
      generationConfig: {
        temperature: 0.2,
        topP: 0.95,
        topK: 40,
        maxOutputTokens: 8192
      }
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`)
    }

    const data = await response.json()
    
    if (!data.candidates?.[0]?.content?.parts?.[0]?.text) {
      throw new Error('Invalid Gemini API response')
    }

    return data.candidates[0].content.parts[0].text
  }

  // Parse Gemini response (from your Python script)
  parseResponse(responseText, expectedCharacters) {
    const result = {}
    const lines = responseText.split('\n')
    
    let currentChar = null
    let currentData = {}
    let currentField = null
    
    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue
      
      if (trimmed.startsWith('Character:')) {
        // Save previous character
        if (currentChar && this.isCompleteData(currentData)) {
          result[currentChar] = currentData
        }
        
        // Start new character
        const charPart = trimmed.split(':', 1)[1]?.trim()
        for (const char of expectedCharacters) {
          if (charPart?.includes(char)) {
            currentChar = char
            break
          }
        }
        currentData = {}
      } else if (trimmed.includes(':')) {
        const [fieldName, ...fieldValueParts] = trimmed.split(':')
        const fieldValue = fieldValueParts.join(':').trim()
        const field = fieldName.trim().toLowerCase()
        
        if (['pinyin', 'meaning', 'composition', 'phrases'].includes(field)) {
          currentData[field] = fieldValue
          currentField = field
        }
      } else if (currentField) {
        currentData[currentField] += ' ' + trimmed
      }
    }
    
    // Don't forget the last character
    if (currentChar && this.isCompleteData(currentData)) {
      result[currentChar] = currentData
    }
    
    return result
  }

  // Cache characters in backend
  async cacheCharacters(characterData) {
    for (const [char, data] of Object.entries(characterData)) {
      // Skip placeholder data
      if (data.pinyin === 'Unknown') continue
      
      try {
        await cacheAPI.addCharacter({
          character: char,
          pinyin: data.pinyin,
          meaning: data.meaning,
          composition: data.composition,
          phrases: data.phrases,
          llm_provider: 'Google',
          llm_model_name: this.model
        })
      } catch (error) {
        console.error(`Failed to cache character ${char}:`, error)
      }
    }
  }

  // Utility functions
  isCompleteData(data) {
    return ['pinyin', 'meaning', 'composition', 'phrases'].every(
      field => data[field] && data[field].trim()
    )
  }

  generatePlaceholder(character) {
    return {
      pinyin: 'Unknown',
      meaning: 'Meaning not available',
      composition: 'Composition not available',
      phrases: `${character}语 - Example phrase 1<br>${character}文 - Example phrase 2`
    }
  }

  chunkArray(array, size) {
    const chunks = []
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size))
    }
    return chunks
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

export default new LLMService()

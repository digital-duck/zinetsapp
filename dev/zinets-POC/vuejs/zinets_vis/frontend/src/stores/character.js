import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '@/services/api'
import { llmService } from '@/services/llm'
import { cacheService } from '@/services/cache'

export const useCharacterStore = defineStore('character', () => {
  // State
  const characters = ref(new Map()) // Map of character -> character data
  const selectedCharacter = ref(null) // Currently selected character
  const loading = ref(false)
  const error = ref(null)
  const cacheStats = ref({
    total: 0,
    cached: 0,
    fresh: 0
  })

  // Getters
  const selectedCharacterData = computed(() => {
    if (!selectedCharacter.value) return null
    return characters.value.get(selectedCharacter.value)
  })

  const characterList = computed(() => {
    return Array.from(characters.value.keys()).sort()
  })

  const getCachedCharacters = computed(() => {
    return Array.from(characters.value.entries()).filter(([char, data]) => data.cached)
  })

  const getFreshCharacters = computed(() => {
    return Array.from(characters.value.entries()).filter(([char, data]) => !data.cached)
  })

  // Actions
  async function fetchCharacterData(character, useCache = true) {
    if (!character) return null

    loading.value = true
    error.value = null

    try {
      // Check if already in store
      if (characters.value.has(character)) {
        const existingData = characters.value.get(character)
        if (existingData.pinyin !== 'Unknown') {
          loading.value = false
          return existingData
        }
      }

      let characterData = null

      // Try cache first if enabled
      if (useCache) {
        try {
          characterData = await cacheService.getCachedCharacter(character)
          if (characterData) {
            characterData.cached = true
            characters.value.set(character, characterData)
            cacheStats.value.cached++
            loading.value = false
            return characterData
          }
        } catch (cacheError) {
          console.warn('Cache lookup failed:', cacheError)
        }
      }

      // If not in cache, fetch from LLM
      try {
        characterData = await llmService.getCharacterData(character)
        if (characterData && characterData.pinyin !== 'Unknown') {
          characterData.cached = false
          characters.value.set(character, characterData)
          cacheStats.value.fresh++

          // Save to cache for future use
          if (useCache) {
            try {
              await cacheService.cacheCharacter(character, characterData)
            } catch (cacheError) {
              console.warn('Failed to cache character:', cacheError)
            }
          }
        } else {
          // Generate placeholder data
          characterData = generatePlaceholderData(character)
          characters.value.set(character, characterData)
        }
      } catch (llmError) {
        console.error('LLM fetch failed:', llmError)
        characterData = generatePlaceholderData(character)
        characters.value.set(character, characterData)
      }

      loading.value = false
      return characterData

    } catch (err) {
      error.value = err.message
      loading.value = false
      console.error('Error fetching character data:', err)
      
      // Return placeholder data on error
      const placeholderData = generatePlaceholderData(character)
      characters.value.set(character, placeholderData)
      return placeholderData
    }
  }

  async function fetchMultipleCharacters(characterList, useCache = true, chunkSize = 10) {
    if (!characterList || characterList.length === 0) return

    loading.value = true
    error.value = null
    
    const results = new Map()
    
    try {
      // Process characters in chunks to avoid overwhelming the API
      for (let i = 0; i < characterList.length; i += chunkSize) {
        const chunk = characterList.slice(i, i + chunkSize)
        
        // Process chunk in parallel
        const chunkPromises = chunk.map(char => fetchCharacterData(char, useCache))
        const chunkResults = await Promise.allSettled(chunkPromises)
        
        // Process results
        chunkResults.forEach((result, index) => {
          if (result.status === 'fulfilled') {
            results.set(chunk[index], result.value)
          } else {
            console.error(`Failed to fetch data for ${chunk[index]}:`, result.reason)
            results.set(chunk[index], generatePlaceholderData(chunk[index]))
          }
        })

        // Add small delay between chunks to be respectful to APIs
        if (i + chunkSize < characterList.length) {
          await new Promise(resolve => setTimeout(resolve, 500))
        }
      }

      loading.value = false
      return results

    } catch (err) {
      error.value = err.message
      loading.value = false
      throw err
    }
  }

  function selectCharacter(character) {
    selectedCharacter.value = character
  }

  function clearSelection() {
    selectedCharacter.value = null
  }

  function addCharacter(character, data) {
    characters.value.set(character, data)
  }

  function removeCharacter(character) {
    characters.value.delete(character)
    if (selectedCharacter.value === character) {
      selectedCharacter.value = null
    }
  }

  function clearCharacters() {
    characters.value.clear()
    selectedCharacter.value = null
    cacheStats.value = { total: 0, cached: 0, fresh: 0 }
  }

  async function refreshCharacter(character) {
    if (!character) return null
    
    // Remove from store first
    characters.value.delete(character)
    
    // Fetch fresh data without cache
    return await fetchCharacterData(character, false)
  }

  async function updateCacheStats() {
    try {
      const stats = await cacheService.getCacheStatistics()
      cacheStats.value = stats
    } catch (err) {
      console.error('Failed to update cache stats:', err)
    }
  }

  function generatePlaceholderData(character) {
    return {
      pinyin: 'Unknown',
      meaning: 'Meaning not available',
      composition: 'Composition not available',
      phrases: `${character}语 - Example phrase 1<br>${character}文 - Example phrase 2<br>${character}词 - Example phrase 3<br>${character}句 - Example phrase 4<br>${character}话 - Example phrase 5`,
      cached: false,
      placeholder: true
    }
  }

  // Helper function to extract characters from tree data
  function extractCharactersFromTree(treeData) {
    const characters = new Set()
    
    function traverse(node) {
      if (node.name && node.name.length === 1) {
        characters.add(node.name)
      }
      if (node.children && Array.isArray(node.children)) {
        node.children.forEach(child => traverse(child))
      }
    }
    
    traverse(treeData)
    return Array.from(characters)
  }

  return {
    // State
    characters,
    selectedCharacter,
    loading,
    error,
    cacheStats,
    
    // Getters
    selectedCharacterData,
    characterList,
    getCachedCharacters,
    getFreshCharacters,
    
    // Actions
    fetchCharacterData,
    fetchMultipleCharacters,
    selectCharacter,
    clearSelection,
    addCharacter,
    removeCharacter,
    clearCharacters,
    refreshCharacter,
    updateCacheStats,
    extractCharactersFromTree
  }
})
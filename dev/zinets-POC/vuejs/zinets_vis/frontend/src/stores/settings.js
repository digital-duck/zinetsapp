import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  // State
  const apiSettings = ref({
    geminiApiKey: '',
    geminiModel: 'gemini-2.0-flash',
    useCache: true,
    chunkSize: 10,
    language: 'English'
  })

  const uiSettings = ref({
    theme: 'light', // 'light' | 'dark' | 'auto'
    treeLayout: 'TB', // 'TB' | 'BT' | 'LR' | 'RL'
    symbolSize: 40,
    fontSize: 25,
    autoExpandTree: false,
    showDecomposition: true,
    showTooltips: true,
    animationEnabled: true,
    language: 'en' // UI language
  })

  const backendSettings = ref({
    baseUrl: 'http://localhost:8000',
    timeout: 30000,
    retryAttempts: 3
  })

  const displaySettings = ref({
    charactersPerPage: 20,
    showCacheStatus: true,
    showStatistics: true,
    compactMode: false,
    showPinyin: true,
    showMeaning: true,
    phraseDisplayLimit: 5
  })

  const exportSettings = ref({
    includeMetadata: true,
    format: 'json', // 'json' | 'markdown' | 'html'
    includeTimestamp: true,
    prettyPrint: true
  })

  // Local storage keys
  const STORAGE_KEYS = {
    API_SETTINGS: 'zinets_api_settings',
    UI_SETTINGS: 'zinets_ui_settings',
    BACKEND_SETTINGS: 'zinets_backend_settings',
    DISPLAY_SETTINGS: 'zinets_display_settings',
    EXPORT_SETTINGS: 'zinets_export_settings'
  }

  // Getters
  const hasGeminiApiKey = computed(() => {
    return apiSettings.value.geminiApiKey && apiSettings.value.geminiApiKey.trim().length > 0
  })

  const isApiConfigured = computed(() => {
    return hasGeminiApiKey.value
  })

  const currentTheme = computed(() => {
    if (uiSettings.value.theme === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return uiSettings.value.theme
  })

  const apiHeaders = computed(() => {
    const headers = {
      'Content-Type': 'application/json'
    }
    
    if (hasGeminiApiKey.value) {
      headers['Authorization'] = `Bearer ${apiSettings.value.geminiApiKey}`
    }
    
    return headers
  })

  const geminiModels = computed(() => [
    'gemini-2.0-flash',
    'gemini-2.5-flash',
    'gemini-1.5-flash',
    'gemini-2.5-pro'
  ])

  const supportedLanguages = computed(() => [
    { code: 'English', name: 'English' },
    { code: 'Chinese', name: '中文' },
    { code: 'Spanish', name: 'Español' },
    { code: 'French', name: 'Français' },
    { code: 'German', name: 'Deutsch' },
    { code: 'Japanese', name: '日本語' },
    { code: 'Korean', name: '한국어' },
    { code: 'Arabic', name: 'العربية' },
    { code: 'Latin', name: 'Latin' }
  ])

  const treeLayoutOptions = computed(() => [
    { value: 'TB', label: 'Top to Bottom', icon: '⬇️' },
    { value: 'BT', label: 'Bottom to Top', icon: '⬆️' },
    { value: 'LR', label: 'Left to Right', icon: '➡️' },
    { value: 'RL', label: 'Right to Left', icon: '⬅️' }
  ])

  // Actions
  function updateApiSettings(newSettings) {
    Object.assign(apiSettings.value, newSettings)
    saveToLocalStorage(STORAGE_KEYS.API_SETTINGS, apiSettings.value)
  }

  function updateUiSettings(newSettings) {
    Object.assign(uiSettings.value, newSettings)
    saveToLocalStorage(STORAGE_KEYS.UI_SETTINGS, uiSettings.value)
  }

  function updateBackendSettings(newSettings) {
    Object.assign(backendSettings.value, newSettings)
    saveToLocalStorage(STORAGE_KEYS.BACKEND_SETTINGS, backendSettings.value)
  }

  function updateDisplaySettings(newSettings) {
    Object.assign(displaySettings.value, newSettings)
    saveToLocalStorage(STORAGE_KEYS.DISPLAY_SETTINGS, displaySettings.value)
  }

  function updateExportSettings(newSettings) {
    Object.assign(exportSettings.value, newSettings)
    saveToLocalStorage(STORAGE_KEYS.EXPORT_SETTINGS, exportSettings.value)
  }

  function setGeminiApiKey(apiKey) {
    apiSettings.value.geminiApiKey = apiKey
    saveToLocalStorage(STORAGE_KEYS.API_SETTINGS, apiSettings.value)
  }

  function setGeminiModel(model) {
    if (geminiModels.value.includes(model)) {
      apiSettings.value.geminiModel = model
      saveToLocalStorage(STORAGE_KEYS.API_SETTINGS, apiSettings.value)
    }
  }

  function setLanguage(language) {
    apiSettings.value.language = language
    saveToLocalStorage(STORAGE_KEYS.API_SETTINGS, apiSettings.value)
  }

  function setTheme(theme) {
    uiSettings.value.theme = theme
    saveToLocalStorage(STORAGE_KEYS.UI_SETTINGS, uiSettings.value)
    applyTheme(currentTheme.value)
  }

  function setTreeLayout(layout) {
    if (['TB', 'BT', 'LR', 'RL'].includes(layout)) {
      uiSettings.value.treeLayout = layout
      saveToLocalStorage(STORAGE_KEYS.UI_SETTINGS, uiSettings.value)
    }
  }

  function toggleCache() {
    apiSettings.value.useCache = !apiSettings.value.useCache
    saveToLocalStorage(STORAGE_KEYS.API_SETTINGS, apiSettings.value)
  }

  function resetToDefaults() {
    apiSettings.value = {
      geminiApiKey: '',
      geminiModel: 'gemini-2.0-flash',
      useCache: true,
      chunkSize: 10,
      language: 'English'
    }

    uiSettings.value = {
      theme: 'light',
      treeLayout: 'TB',
      symbolSize: 40,
      fontSize: 25,
      autoExpandTree: false,
      showDecomposition: true,
      showTooltips: true,
      animationEnabled: true,
      language: 'en'
    }

    backendSettings.value = {
      baseUrl: 'http://localhost:8000',
      timeout: 30000,
      retryAttempts: 3
    }

    displaySettings.value = {
      charactersPerPage: 20,
      showCacheStatus: true,
      showStatistics: true,
      compactMode: false,
      showPinyin: true,
      showMeaning: true,
      phraseDisplayLimit: 5
    }

    exportSettings.value = {
      includeMetadata: true,
      format: 'json',
      includeTimestamp: true,
      prettyPrint: true
    }

    // Save all to localStorage
    saveAllToLocalStorage()
  }

  function loadFromLocalStorage() {
    try {
      const savedApiSettings = localStorage.getItem(STORAGE_KEYS.API_SETTINGS)
      if (savedApiSettings) {
        Object.assign(apiSettings.value, JSON.parse(savedApiSettings))
      }

      const savedUiSettings = localStorage.getItem(STORAGE_KEYS.UI_SETTINGS)
      if (savedUiSettings) {
        Object.assign(uiSettings.value, JSON.parse(savedUiSettings))
      }

      const savedBackendSettings = localStorage.getItem(STORAGE_KEYS.BACKEND_SETTINGS)
      if (savedBackendSettings) {
        Object.assign(backendSettings.value, JSON.parse(savedBackendSettings))
      }

      const savedDisplaySettings = localStorage.getItem(STORAGE_KEYS.DISPLAY_SETTINGS)
      if (savedDisplaySettings) {
        Object.assign(displaySettings.value, JSON.parse(savedDisplaySettings))
      }

      const savedExportSettings = localStorage.getItem(STORAGE_KEYS.EXPORT_SETTINGS)
      if (savedExportSettings) {
        Object.assign(exportSettings.value, JSON.parse(savedExportSettings))
      }

      // Apply theme after loading
      applyTheme(currentTheme.value)

    } catch (error) {
      console.error('Error loading settings from localStorage:', error)
    }
  }

  function saveToLocalStorage(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`Error saving ${key} to localStorage:`, error)
    }
  }

  function saveAllToLocalStorage() {
    saveToLocalStorage(STORAGE_KEYS.API_SETTINGS, apiSettings.value)
    saveToLocalStorage(STORAGE_KEYS.UI_SETTINGS, uiSettings.value)
    saveToLocalStorage(STORAGE_KEYS.BACKEND_SETTINGS, backendSettings.value)
    saveToLocalStorage(STORAGE_KEYS.DISPLAY_SETTINGS, displaySettings.value)
    saveToLocalStorage(STORAGE_KEYS.EXPORT_SETTINGS, exportSettings.value)
  }

  function clearAllSettings() {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key)
    })
    resetToDefaults()
  }

  function exportSettings() {
    const settings = {
      api: apiSettings.value,
      ui: uiSettings.value,
      backend: backendSettings.value,
      display: displaySettings.value,
      export: exportSettings.value,
      exportedAt: new Date().toISOString()
    }

    return JSON.stringify(settings, null, 2)
  }

  function importSettings(settingsJson) {
    try {
      const settings = JSON.parse(settingsJson)
      
      if (settings.api) updateApiSettings(settings.api)
      if (settings.ui) updateUiSettings(settings.ui)
      if (settings.backend) updateBackendSettings(settings.backend)
      if (settings.display) updateDisplaySettings(settings.display)
      if (settings.export) updateExportSettings(settings.export)
      
      return true
    } catch (error) {
      console.error('Error importing settings:', error)
      return false
    }
  }

  function applyTheme(theme) {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme)
      document.documentElement.classList.toggle('dark', theme === 'dark')
    }
  }

  function validateApiKey(apiKey) {
    // Basic validation for Gemini API key format
    if (!apiKey || typeof apiKey !== 'string') return false
    
    // Gemini API keys typically start with 'AI' and are around 39 characters long
    const keyPattern = /^AI[a-zA-Z0-9_-]{37}$/
    return keyPattern.test(apiKey.trim())
  }

  function getEChartsTheme() {
    return currentTheme.value === 'dark' ? 'dark' : 'light'
  }

  // Watch for theme changes and apply them
  watch(currentTheme, (newTheme) => {
    applyTheme(newTheme)
  })

  // Auto-save settings when they change
  watch(apiSettings, () => {
    saveToLocalStorage(STORAGE_KEYS.API_SETTINGS, apiSettings.value)
  }, { deep: true })

  watch(uiSettings, () => {
    saveToLocalStorage(STORAGE_KEYS.UI_SETTINGS, uiSettings.value)
  }, { deep: true })

  watch(backendSettings, () => {
    saveToLocalStorage(STORAGE_KEYS.BACKEND_SETTINGS, backendSettings.value)
  }, { deep: true })

  watch(displaySettings, () => {
    saveToLocalStorage(STORAGE_KEYS.DISPLAY_SETTINGS, displaySettings.value)
  }, { deep: true })

  watch(exportSettings, () => {
    saveToLocalStorage(STORAGE_KEYS.EXPORT_SETTINGS, exportSettings.value)
  }, { deep: true })

  return {
    // State
    apiSettings,
    uiSettings,
    backendSettings,
    displaySettings,
    exportSettings,
    
    // Getters
    hasGeminiApiKey,
    isApiConfigured,
    currentTheme,
    apiHeaders,
    geminiModels,
    supportedLanguages,
    treeLayoutOptions,
    
    // Actions
    updateApiSettings,
    updateUiSettings,
    updateBackendSettings,
    updateDisplaySettings,
    updateExportSettings,
    setGeminiApiKey,
    setGeminiModel,
    setLanguage,
    setTheme,
    setTreeLayout,
    toggleCache,
    resetToDefaults,
    loadFromLocalStorage,
    saveToLocalStorage,
    saveAllToLocalStorage,
    clearAllSettings,
    exportSettings,
    importSettings,
    validateApiKey,
    getEChartsTheme
  }
})
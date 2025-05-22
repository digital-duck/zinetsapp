<template>
  <div id="app">
    <el-container class="app-container">
      <!-- Header -->
      <el-header class="app-header">
        <div class="header-left">
          <h1>ZiNets - Character Network Visualization</h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showInputDialog">
            <el-icon><DocumentAdd /></el-icon>
            Load Network
          </el-button>
          <el-button @click="showSettingsDialog">
            <el-icon><Setting /></el-icon>
            Settings
          </el-button>
        </div>
      </el-header>

      <!-- Main Content -->
      <el-container class="main-container">
        <!-- Network Visualization -->
        <el-main class="chart-area">
          <CharacterTree
            :tree-data="treeData"
            :character-data="characterData"
            @character-selected="handleCharacterSelected"
            :loading="isLoadingNetwork"
          />
        </el-main>

        <!-- Sidebar -->
        <el-aside width="400px" class="sidebar">
          <CharacterDetails
            :character="selectedCharacter"
            :character-data="selectedCharacterData"
            :loading="isLoadingCharacterData"
          />
          
          <!-- Cache Info -->
          <el-card class="cache-info">
            <template #header>
              <div class="card-header">
                <span>Cache Status</span>
                <el-button size="small" text @click="refreshCacheStats">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="cache-stats">
              <div class="stat-item">
                <span class="stat-label">Cached Characters:</span>
                <span class="stat-value">{{ cacheStats.active_characters || 0 }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Memory Cache:</span>
                <span class="stat-value">{{ cacheStats.memoryCache || 0 }}</span>
              </div>
              <div class="stat-item" v-if="cacheStats.last_updated">
                <span class="stat-label">Last Updated:</span>
                <span class="stat-value">{{ formatDate(cacheStats.last_updated) }}</span>
              </div>
            </div>
            <div class="cache-actions">
              <el-button size="small" @click="clearCache" :loading="isClearingCache">
                Clear Cache
              </el-button>
            </div>
          </el-card>
        </el-aside>
      </el-container>
    </el-container>

    <!-- Dialogs -->
    <NetworkInput
      v-model:visible="inputDialogVisible"
      @network-loaded="handleNetworkLoaded"
      :loading="isLoadingNetwork"
    />
    
    <SettingsDialog
      v-model:visible="settingsDialogVisible"
      @settings-saved="handleSettingsSaved"
    />

    <!-- Global Loading -->
    <el-loading v-loading="isInitializing" text="Initializing application..." element-loading-background="rgba(0, 0, 0, 0.8)" />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentAdd, Setting, Refresh } from '@element-plus/icons-vue'

// Components
import CharacterTree from './components/CharacterTree.vue'
import CharacterDetails from './components/CharacterDetails.vue'
import NetworkInput from './components/NetworkInput.vue'
import SettingsDialog from './components/SettingsDialog.vue'

// Services
import MarkdownParser from './services/parser.js'
import llmService from './services/llm.js'
import cacheService from './services/cache.js'
import { cacheAPI } from './services/api.js'

export default {
  name: 'App',
  components: {
    CharacterTree,
    CharacterDetails,
    NetworkInput,
    SettingsDialog,
    DocumentAdd,
    Setting,
    Refresh
  },
  
  setup() {
    // State
    const isInitializing = ref(true)
    const treeData = ref(null)
    const characterData = ref({})
    const selectedCharacter = ref(null)
    const isLoadingNetwork = ref(false)
    const isLoadingCharacterData = ref(false)
    const isClearingCache = ref(false)
    
    // UI State
    const inputDialogVisible = ref(false)
    const settingsDialogVisible = ref(false)
    
    // Cache Statistics
    const cacheStats = reactive({
      total_characters: 0,
      active_characters: 0,
      providers: {},
      last_updated: null,
      memoryCache: 0
    })
    
    // Computed Properties
    const selectedCharacterData = computed(() => {
      return selectedCharacter.value ? characterData.value[selectedCharacter.value] : null
    })
    
    // Methods
    async function initializeApp() {
      try {
        // Check backend connection
        await cacheAPI.healthCheck()
        console.log('Backend connection established')
        
        // Load settings from localStorage
        loadSettings()
        
        // Refresh cache stats
        await refreshCacheStats()
        
        // Load default network if no tree data
        if (!treeData.value) {
          await loadDefaultNetwork()
        }
        
      } catch (error) {
        console.error('Failed to initialize app:', error)
        ElMessage.error('Failed to connect to backend. Please ensure the server is running.')
      } finally {
        isInitializing.value = false
      }
    }
    
    async function loadDefaultNetwork() {
      const defaultMarkdown = `心
- 想(相+心)
    - 愿(原+心)
    - 惟(忄+隹)
- 情(忄+青)
    - 愛(爫+冖+心+夊)
    - 恋(亦+心)
- 忘(亡+心)
    - 怯(忄+去)
    - 悔(忄+每)
- 志(士+心)
    - 意(立+心)
    - 思(田+心)`
    
      await processNetwork(defaultMarkdown, 'English', true, true)
    }
    
    async function handleNetworkLoaded(networkData) {
      const { markdown, language, useCache, useLLM } = networkData
      await processNetwork(markdown, language, useCache, useLLM)
    }
    
    async function processNetwork(markdownText, language = 'English', useCache = true, useLLM = true) {
      isLoadingNetwork.value = true
      
      try {
        // Parse markdown to tree
        const validation = MarkdownParser.validateMarkdown(markdownText)
        if (!validation.valid) {
          ElMessage.error(`Invalid markdown: ${validation.errors.join(', ')}`)
          return
        }
        
        if (validation.warnings.length > 0) {
          console.warn('Markdown warnings:', validation.warnings)
        }
        
        const parsedTree = MarkdownParser.parseMarkdownToTree(markdownText)
        treeData.value = parsedTree
        
        // Extract characters
        const characters = MarkdownParser.extractAllCharacters(parsedTree)
        console.log(`Found ${characters.length} characters:`, characters)
        
        // Load character data
        if (characters.length > 0) {
          await loadCharacterData(characters, language, useCache, useLLM)
        }
        
        // Reset selected character
        selectedCharacter.value = null
        
        ElMessage.success(`Network loaded successfully with ${characters.length} characters`)
        
      } catch (error) {
        console.error('Error processing network:', error)
        ElMessage.error('Failed to process network: ' + error.message)
      } finally {
        isLoadingNetwork.value = false
      }
    }
    
    async function loadCharacterData(characters, language, useCache, useLLM) {
      isLoadingCharacterData.value = true
      
      try {
        // Check settings for API key
        const settings = getSettings()
        if (useLLM && !settings.geminiApiKey) {
          ElMessage.warning('Gemini API key not configured. Using cache and placeholders only.')
          useLLM = false
        }
        
        // Configure LLM service
        if (useLLM && settings.geminiApiKey) {
          llmService.setApiKey(settings.geminiApiKey)
        }
        
        // Get character data
        const newCharacterData = await llmService.getCharacterData(characters, language, useCache)
        characterData.value = newCharacterData
        
        // Refresh cache stats
        await refreshCacheStats()
        
        console.log(`Loaded data for ${Object.keys(newCharacterData).length} characters`)
        
      } catch (error) {
        console.error('Error loading character data:', error)
        ElMessage.error('Failed to load character data: ' + error.message)
      } finally {
        isLoadingCharacterData.value = false
      }
    }
    
    function handleCharacterSelected(character) {
      selectedCharacter.value = character
      console.log('Selected character:', character)
    }
    
    function handleSettingsSaved(settings) {
      saveSettings(settings)
      if (settings.geminiApiKey) {
        llmService.setApiKey(settings.geminiApiKey)
      }
      ElMessage.success('Settings saved successfully')
    }
    
    async function refreshCacheStats() {
      try {
        const stats = await cacheService.getStats()
        Object.assign(cacheStats, stats)
      } catch (error) {
        console.error('Error refreshing cache stats:', error)
      }
    }
    
    async function clearCache() {
      try {
        await ElMessageBox.confirm(
          'This will clear all cached character data. Are you sure?',
          'Clear Cache',
          {
            confirmButtonText: 'Clear',
            cancelButtonText: 'Cancel',
            type: 'warning'
          }
        )
        
        isClearingCache.value = true
        await cacheService.clearCache()
        await refreshCacheStats()
        
        ElMessage.success('Cache cleared successfully')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Error clearing cache:', error)
          ElMessage.error('Failed to clear cache')
        }
      } finally {
        isClearingCache.value = false
      }
    }
    
    function showInputDialog() {
      inputDialogVisible.value = true
    }
    
    function showSettingsDialog() {
      settingsDialogVisible.value = true
    }
    
    function formatDate(timestamp) {
      if (!timestamp) return ''
      try {
        return new Date(timestamp).toLocaleString()
      } catch {
        return timestamp
      }
    }
    
    // Settings Management
    function getSettings() {
      try {
        const saved = localStorage.getItem('zinets_vis_settings')
        return saved ? JSON.parse(saved) : {}
      } catch {
        return {}
      }
    }
    
    function saveSettings(settings) {
      try {
        localStorage.setItem('zinets_vis_settings', JSON.stringify(settings))
      } catch (error) {
        console.error('Failed to save settings:', error)
      }
    }
    
    function loadSettings() {
      const settings = getSettings()
      if (settings.geminiApiKey) {
        llmService.setApiKey(settings.geminiApiKey)
      }
    }
    
    // Lifecycle
    onMounted(() => {
      initializeApp()
    })
    
    // Watch for tree data changes to auto-reload character data
    watch(treeData, (newTreeData) => {
      if (newTreeData) {
        const characters = MarkdownParser.extractAllCharacters(newTreeData)
        if (characters.length > 0) {
          // Preload characters in memory cache for better performance
          cacheService.preloadCharacters(characters)
        }
      }
    })
    
    return {
      // State
      isInitializing,
      treeData,
      characterData,
      selectedCharacter,
      selectedCharacterData,
      isLoadingNetwork,
      isLoadingCharacterData,
      isClearingCache,
      
      // UI State
      inputDialogVisible,
      settingsDialogVisible,
      
      // Cache
      cacheStats,
      
      // Methods
      handleNetworkLoaded,
      handleCharacterSelected,
      handleSettingsSaved,
      refreshCacheStats,
      clearCache,
      showInputDialog,
      showSettingsDialog,
      formatDate,
      
      // Icons
      DocumentAdd,
      Setting,
      Refresh
    }
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 12px;
}

.main-container {
  height: calc(100vh - 60px);
}

.chart-area {
  padding: 0;
  overflow: hidden;
}

.sidebar {
  background-color: #f8f9fa;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
  padding: 20px;
}

.cache-info {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cache-stats {
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  color: #303133;
  font-weight: 600;
  font-size: 14px;
}

.cache-actions {
  text-align: center;
}

/* Responsive Design */
@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    padding: 15px;
    gap: 10px;
  }
  
  .header-left h1 {
    font-size: 20px;
  }
  
  .main-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100% !important;
    max-height: 300px;
  }
}
</style>

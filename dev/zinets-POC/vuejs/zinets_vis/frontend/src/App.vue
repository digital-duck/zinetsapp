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
    <span class="stat-value">{{ cacheStats.cached || 0 }}</span>
  </div>
  <div class="stat-item">
    <span class="stat-label">Fresh Characters:</span>
    <span class="stat-value">{{ cacheStats.fresh || 0 }}</span>
  </div>
  <div class="stat-item">
    <span class="stat-label">Total Characters:</span>
    <span class="stat-value">{{ cacheStats.total || 0 }}</span>
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentAdd, Setting, Refresh } from '@element-plus/icons-vue'

// Components
import CharacterTree from './components/CharacterTree.vue'
import CharacterDetails from './components/CharacterDetails.vue'
import NetworkInput from './components/NetworkInput.vue'
import SettingsDialog from './components/SettingsDialog.vue'

// Pinia Stores
import { useCharacterStore } from './stores/character'
import { useNetworkStore } from './stores/network'
import { useSettingsStore } from './stores/settings'

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
    // Pinia Stores
    const characterStore = useCharacterStore()
    const networkStore = useNetworkStore()
    const settingsStore = useSettingsStore()
    
    // UI State
    const isInitializing = ref(true)
    const inputDialogVisible = ref(false)
    const settingsDialogVisible = ref(false)
    
    // Computed Properties from stores
    const treeData = computed(() => networkStore.treeData)
    const characterData = computed(() => characterStore.characters)
    const selectedCharacter = computed(() => characterStore.selectedCharacter)
    const selectedCharacterData = computed(() => characterStore.selectedCharacterData)
    const isLoadingNetwork = computed(() => networkStore.loading)
    const isLoadingCharacterData = computed(() => characterStore.loading)
    const cacheStats = computed(() => characterStore.cacheStats)
    
    // Methods
    async function initializeApp() {
      try {
        // Load settings from localStorage
        settingsStore.loadFromLocalStorage()
        
        // Initialize cache stats
        await characterStore.updateCacheStats()
        
        // Load default network if no tree data
        if (!networkStore.hasTreeData) {
          await loadDefaultNetwork()
        }
        
        ElMessage.success('Application initialized successfully')
        
      } catch (error) {
        console.error('Failed to initialize app:', error)
        ElMessage.error('Failed to initialize application: ' + error.message)
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
      try {
        // Parse markdown using network store
        const success = await networkStore.parseMarkdown(markdownText)
        if (!success) {
          ElMessage.error('Failed to parse network markdown')
          return
        }
        
        // Extract characters from the tree
        const characters = characterStore.extractCharactersFromTree(networkStore.treeData)
        console.log(`Found ${characters.length} characters:`, characters)
        
        // Update API language setting
        settingsStore.setLanguage(language)
        settingsStore.updateApiSettings({ useCache })
        
        // Load character data if LLM is enabled
        if (useLLM && characters.length > 0) {
          // Check if API key is configured
          if (!settingsStore.hasGeminiApiKey) {
            ElMessage.warning('Gemini API key not configured. Using cache and placeholders only.')
            useLLM = false
          }
          
          if (useLLM) {
            await characterStore.fetchMultipleCharacters(
              characters, 
              useCache, 
              settingsStore.apiSettings.chunkSize
            )
          }
        }
        
        // Select root character by default
        if (networkStore.rootCharacter) {
          characterStore.selectCharacter(networkStore.rootCharacter)
        }
        
        ElMessage.success(`Network loaded successfully with ${characters.length} characters`)
        
      } catch (error) {
        console.error('Error processing network:', error)
        ElMessage.error('Failed to process network: ' + error.message)
      }
    }
    
    function handleCharacterSelected(character) {
      characterStore.selectCharacter(character)
      console.log('Selected character:', character)
    }
    
    function handleSettingsSaved(settings) {
      // Update all relevant store settings
      settingsStore.updateApiSettings(settings.api || {})
      settingsStore.updateUiSettings(settings.ui || {})
      settingsStore.updateDisplaySettings(settings.display || {})
      
      ElMessage.success('Settings saved successfully')
    }
    
    async function refreshCacheStats() {
      try {
        await characterStore.updateCacheStats()
      } catch (error) {
        console.error('Error refreshing cache stats:', error)
        ElMessage.error('Failed to refresh cache statistics')
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
        
        // Clear both character store and network store
        characterStore.clearCharacters()
        await characterStore.updateCacheStats()
        
        ElMessage.success('Cache cleared successfully')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Error clearing cache:', error)
          ElMessage.error('Failed to clear cache')
        }
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
    
    // Lifecycle
    onMounted(() => {
      initializeApp()
    })
    
    return {
      // State
      isInitializing,
      
      // Computed from stores
      treeData,
      characterData,
      selectedCharacter,
      selectedCharacterData,
      isLoadingNetwork,
      isLoadingCharacterData,
      cacheStats,
      
      // UI State
      inputDialogVisible,
      settingsDialogVisible,
      
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

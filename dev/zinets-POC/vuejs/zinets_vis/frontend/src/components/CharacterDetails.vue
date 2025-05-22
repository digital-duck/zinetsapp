<template>
  <div class="character-details">
    <el-card class="details-card">
      <template #header>
        <div class="card-header">
          <span>Character Details</span>
          <el-button 
            v-if="selectedCharacter" 
            size="small" 
            text 
            @click="refreshCharacterData"
            :loading="characterStore.loading"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
      </template>
      
      <!-- No Character Selected -->
      <div v-if="!selectedCharacter" class="no-selection">
        <el-empty 
          description="Click a character in the network to view details"
          :image-size="120"
        />
      </div>
      
      <!-- Character Display -->
      <div v-else class="character-content">
        <!-- Character Header -->
        <div class="character-header">
          <div class="character-display">{{ selectedCharacter }}</div>
          <div class="character-pinyin">
            {{ selectedCharacterData?.pinyin || 'Loading...' }}
          </div>
        </div>
        
        <!-- Details Tabs -->
        <el-tabs v-model="activeTab" class="details-tabs">
          <!-- Overview Tab -->
          <el-tab-pane label="Overview" name="overview">
            <div class="tab-content">
              <div class="detail-section">
                <h4>Meaning</h4>
                <div class="detail-text">
                  {{ selectedCharacterData?.meaning || 'Loading meaning...' }}
                </div>
              </div>
              
              <div class="detail-section">
                <h4>Composition</h4>
                <div class="detail-text">
                  {{ selectedCharacterData?.composition || 'Loading composition...' }}
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- Phrases Tab -->
          <el-tab-pane label="Phrases" name="phrases">
            <div class="tab-content">
              <div class="detail-section">
                <h4>Example Phrases</h4>
                <div 
                  class="phrases-content"
                  v-html="selectedCharacterData?.phrases || 'Loading phrases...'"
                />
              </div>
            </div>
          </el-tab-pane>
          
          <!-- Search Tab -->
          <el-tab-pane label="Search" name="search">
            <div class="tab-content">
              <div class="detail-section">
                <h4>External Resources</h4>
                <p class="search-description">
                  Search for "{{ selectedCharacter }}" in online dictionaries and resources:
                </p>
                <div class="search-buttons">
                  <el-button
                    v-for="site in searchSites"
                    :key="site.key"
                    size="small"
                    type="primary"
                    plain
                    @click="openSearch(site)"
                  >
                    {{ site.name }}
                  </el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
        
        <!-- Data Status -->
        <div class="data-status">
          <el-tag 
            :type="getDataStatusType()" 
            size="small"
            effect="light"
          >
            {{ getDataStatusText() }}
          </el-tag>
        </div>
      </div>
      
      <!-- Loading Overlay -->
      <div 
        v-if="characterStore.loading && selectedCharacter" 
        class="loading-overlay"
        v-loading="characterStore.loading"
        element-loading-text="Loading character data..."
        element-loading-background="rgba(255, 255, 255, 0.8)"
      />
    </el-card>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'

// Pinia Store
import { useCharacterStore } from '@/stores/character'

// Search sites configuration
const SEARCH_SITES = [
  { 
    key: 'zdic', 
    name: '汉典', 
    url: 'https://www.zdic.net/hans/' 
  },
  { 
    key: 'qianp', 
    name: '千篇国学', 
    url: 'https://zidian.qianp.com/zi/' 
  },
  { 
    key: 'hwxnet', 
    name: '文学网', 
    url: 'https://zd.hwxnet.com/search.do?keyword=' 
  },
  { 
    key: 'hanziyuan', 
    name: '字源', 
    url: 'https://hanziyuan.net/#' 
  },
  { 
    key: 'cuhk', 
    name: '多功能字庫', 
    url: 'https://humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/search.php?word=' 
  },
  { 
    key: 'baidu', 
    name: 'Baidu', 
    url: 'https://www.google.com/search?q=baidu+' 
  }
]

export default {
  name: 'CharacterDetails',
  components: {
    Refresh
  },
  
  setup() {
    // Pinia Store
    const characterStore = useCharacterStore()
    
    // Local state
    const activeTab = ref('overview')
    const searchSites = ref(SEARCH_SITES)
    
    // Computed properties from store
    const selectedCharacter = computed(() => characterStore.selectedCharacter)
    const selectedCharacterData = computed(() => characterStore.selectedCharacterData)
    
    // Methods
    async function refreshCharacterData() {
      if (selectedCharacter.value) {
        try {
          await characterStore.refreshCharacter(selectedCharacter.value)
          ElMessage.success('Character data refreshed successfully')
        } catch (error) {
          console.error('Failed to refresh character:', error)
          ElMessage.error('Failed to refresh character data: ' + error.message)
        }
      }
    }
    
    function openSearch(site) {
      if (selectedCharacter.value) {
        const url = site.url + encodeURIComponent(selectedCharacter.value)
        window.open(url, '_blank', 'noopener,noreferrer')
      }
    }
    
    function getDataStatusType() {
      if (!selectedCharacterData.value) return 'info'
      
      if (selectedCharacterData.value.placeholder) {
        return 'warning'
      }
      
      if (selectedCharacterData.value.cached) {
        return 'success'
      }
      
      return 'primary'
    }
    
    function getDataStatusText() {
      if (!selectedCharacterData.value) return 'Loading...'
      
      if (selectedCharacterData.value.placeholder) {
        return 'Placeholder Data'
      }
      
      if (selectedCharacterData.value.cached) {
        return 'Cached Data'
      }
      
      return 'Fresh Data'
    }
    
    // Watch for character changes to reset tab
    watch(selectedCharacter, (newCharacter) => {
      if (newCharacter) {
        activeTab.value = 'overview'
      }
    })
    
    return {
      // Store
      characterStore,
      
      // Computed
      selectedCharacter,
      selectedCharacterData,
      
      // Local state
      activeTab,
      searchSites,
      
      // Methods
      refreshCharacterData,
      openSearch,
      getDataStatusType,
      getDataStatusText,
      
      // Icons
      Refresh
    }
  }
}
</script>

<style scoped>
.character-details {
  height: 100%;
}

.details-card {
  height: 100%;
  position: relative;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.no-selection {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.character-content {
  position: relative;
}

.character-header {
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.character-display {
  font-size: 80px;
  font-weight: bold;
  color: #1890ff;
  line-height: 1;
  margin-bottom: 8px;
}

.character-pinyin {
  font-size: 24px;
  color: #666;
  font-style: italic;
}

.details-tabs {
  margin-top: 15px;
}

.tab-content {
  padding: 10px 0;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
  border-left: 3px solid #1890ff;
  padding-left: 10px;
}

.detail-text {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.phrases-content {
  color: #606266;
  line-height: 1.8;
  font-size: 14px;
}

.phrases-content :deep(br) {
  margin-bottom: 8px;
}

.search-description {
  color: #909399;
  font-size: 14px;
  margin-bottom: 15px;
}

.search-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}

.data-status {
  position: absolute;
  bottom: 10px;
  right: 10px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  border-radius: 4px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .character-display {
    font-size: 60px;
  }
  
  .character-pinyin {
    font-size: 20px;
  }
  
  .search-buttons {
    grid-template-columns: 1fr;
  }
}
</style>
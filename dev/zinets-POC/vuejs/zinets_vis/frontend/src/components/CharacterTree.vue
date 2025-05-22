<template>
  <div class="character-tree-container">
    <div 
      v-if="networkStore.loading" 
      class="loading-overlay"
      v-loading="networkStore.loading"
      element-loading-text="Loading network..."
      element-loading-background="rgba(255, 255, 255, 0.9)"
    >
    </div>
    
    <div v-else-if="!networkStore.hasTreeData" class="empty-state">
      <el-empty description="No network data loaded">
        <el-button type="primary" @click="$emit('load-network')">
          Load Network
        </el-button>
      </el-empty>
    </div>
    
    <div v-else class="chart-wrapper">
      <v-chart
        ref="chartRef"
        class="character-chart"
        :option="chartOption"
        @click="handleNodeClick"
        autoresize
      />
      
      <!-- Network Info -->
      <div class="network-info">
        <el-tag type="info" size="small">
          Root: {{ networkStore.rootCharacter }}
        </el-tag>
        <el-tag type="success" size="small">
          Characters: {{ totalCharacters }}
        </el-tag>
        <el-tag v-if="characterStore.selectedCharacter" type="warning" size="small">
          Selected: {{ characterStore.selectedCharacter }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { TreeChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'

// Pinia Stores
import { useCharacterStore } from '@/stores/character'
import { useNetworkStore } from '@/stores/network'
import { useSettingsStore } from '@/stores/settings'

// Register ECharts components
use([
  CanvasRenderer,
  TreeChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

export default {
  name: 'CharacterTree',
  components: {
    VChart
  },
  
  emits: ['load-network'],
  
  setup(props, { emit }) {
    // Pinia Stores
    const characterStore = useCharacterStore()
    const networkStore = useNetworkStore()
    const settingsStore = useSettingsStore()
    
    // Local refs
    const chartRef = ref(null)
    
    // Computed Properties
    const totalCharacters = computed(() => {
      if (!networkStore.hasTreeData) return 0
      return characterStore.extractCharactersFromTree(networkStore.treeData).length
    })
    
    const chartOption = computed(() => {
      if (!networkStore.hasTreeData) return {}
      
      return {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            const character = params.data.name
            const decomposition = params.data.decomposition
            
            if (decomposition) {
              return `
                <div style="font-size:16px; font-weight:bold; margin-bottom:5px;">
                  ${character}
                </div>
                <div style="color:#666; font-size:14px;">
                  ${decomposition}
                </div>
              `
            } else {
              return `
                <div style="font-size:16px; font-weight:bold;">
                  ${character}
                </div>
              `
            }
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#ddd',
          borderWidth: 1,
          textStyle: {
            color: '#333'
          },
          padding: [8, 12]
        },
        
        series: [{
          type: 'tree',
          data: [networkStore.treeData],
          
          // Tree Layout
          top: '5%',
          left: '5%',
          bottom: '5%',
          right: '5%',
          
          symbolSize: (value, params) => {
            // Larger symbols for characters with data
            const character = params.data.name
            const hasData = characterStore.characters.has(character)
            const isSelected = character === characterStore.selectedCharacter
            
            if (isSelected) return 50
            if (hasData) return settingsStore.uiSettings.symbolSize
            return settingsStore.uiSettings.symbolSize - 5
          },
          
          symbol: 'rect',
          orient: settingsStore.uiSettings.treeLayout,
          
          label: {
            show: true,
            position: 'inside',
            fontSize: (params) => {
              const character = params.data.name
              const isSelected = character === characterStore.selectedCharacter
              return isSelected ? settingsStore.uiSettings.fontSize + 4 : settingsStore.uiSettings.fontSize
            },
            fontWeight: 'bold',
            // Dynamic color based on data availability
            color: (params) => {
              const character = params.data.name
              const hasData = characterStore.characters.has(character)
              const isSelected = character === characterStore.selectedCharacter
              
              if (isSelected) return '#fff'
              if (hasData) return '#1890ff'
              return '#666'
            }
          },
          
          itemStyle: {
            borderColor: '#333',
            borderWidth: 1,
            // Dynamic color based on state
            color: (params) => {
              const character = params.data.name
              const hasData = characterStore.characters.has(character)
              const isSelected = character === characterStore.selectedCharacter
              
              if (isSelected) return '#1890ff'
              if (hasData) return '#f0f9ff'
              return '#fafafa'
            }
          },
          
          emphasis: {
            focus: 'relative',
            itemStyle: {
              borderColor: '#1890ff',
              borderWidth: 2,
              shadowBlur: 10,
              shadowColor: 'rgba(24, 144, 255, 0.5)'
            },
            label: {
              fontSize: settingsStore.uiSettings.fontSize + 2,
              fontWeight: 'bold'
            }
          },
          
          leaves: {
            label: {
              position: 'inside',
              verticalAlign: 'middle',
              align: 'center'
            }
          },
          
          expandAndCollapse: false,
          animationDuration: settingsStore.uiSettings.animationEnabled ? 750 : 0,
          animationDurationUpdate: settingsStore.uiSettings.animationEnabled ? 750 : 0,
          
          lineStyle: {
            width: 2,
            color: '#999',
            curveness: 0.5
          }
        }]
      }
    })
    
    // Methods
    function handleNodeClick(params) {
      const character = params.data.name
      
      // Only handle single characters
      if (character && isSingleCharacter(character)) {
        characterStore.selectCharacter(character)
        
        // Fetch character data if not already loaded
        if (!characterStore.characters.has(character)) {
          characterStore.fetchCharacterData(character, settingsStore.apiSettings.useCache)
        }
      }
    }
    
    function isSingleCharacter(str) {
      if (!str || str.length !== 1) return false
      
      // Check if it's a Chinese character
      const code = str.charCodeAt(0)
      return (code >= 0x4E00 && code <= 0x9FFF) || // CJK Unified Ideographs
             (code >= 0x3400 && code <= 0x4DBF) || // CJK Extension A
             (code >= 0x20000 && code <= 0x2A6DF)   // CJK Extension B
    }
    
    function resizeChart() {
      if (chartRef.value) {
        chartRef.value.resize()
      }
    }
    
    // Watch for tree data changes to trigger chart updates
    watch(() => networkStore.treeData, () => {
      nextTick(() => {
        resizeChart()
      })
    })
    
    // Watch for character data changes to update node colors
    watch(() => characterStore.characters, () => {
      nextTick(() => {
        resizeChart()
      })
    }, { deep: true })
    
    // Watch for settings changes
    watch(() => settingsStore.uiSettings, () => {
      nextTick(() => {
        resizeChart()
      })
    }, { deep: true })
    
    return {
      // Stores
      characterStore,
      networkStore,
      settingsStore,
      
      // Refs
      chartRef,
      
      // Computed
      chartOption,
      totalCharacters,
      
      // Methods
      handleNodeClick,
      resizeChart
    }
  }
}
</script>

<style scoped>
.character-tree-container {
  position: relative;
  height: 100%;
  width: 100%;
  background-color: #fff;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.chart-wrapper {
  position: relative;
  height: 100%;
  width: 100%;
}

.character-chart {
  height: 100%;
  width: 100%;
}

.network-info {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  max-width: 300px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .network-info {
    position: relative;
    top: 0;
    left: 0;
    padding: 10px;
    background-color: rgba(255, 255, 255, 0.9);
    border-bottom: 1px solid #eee;
    max-width: none;
  }
  
  .character-chart {
    height: calc(100% - 60px);
  }
}
</style>
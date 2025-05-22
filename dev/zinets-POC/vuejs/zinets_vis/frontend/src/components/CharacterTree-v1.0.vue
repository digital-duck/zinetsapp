<template>
  <div class="character-tree-container">
    <div 
      v-if="loading" 
      class="loading-overlay"
      v-loading="loading"
      element-loading-text="Loading network..."
      element-loading-background="rgba(255, 255, 255, 0.9)"
    >
    </div>
    
    <div v-else-if="!treeData" class="empty-state">
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
          Root: {{ treeData.name }}
        </el-tag>
        <el-tag type="success" size="small">
          Characters: {{ totalCharacters }}
        </el-tag>
        <el-tag v-if="selectedCharacter" type="warning" size="small">
          Selected: {{ selectedCharacter }}
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
  
  props: {
    treeData: {
      type: Object,
      default: null
    },
    characterData: {
      type: Object,
      default: () => ({})
    },
    loading: {
      type: Boolean,
      default: false
    },
    selectedCharacter: {
      type: String,
      default: null
    }
  },
  
  emits: ['character-selected', 'load-network'],
  
  setup(props, { emit }) {
    const chartRef = ref(null)
    
    // Computed Properties
    const totalCharacters = computed(() => {
      if (!props.treeData) return 0
      return extractAllCharacters(props.treeData).length
    })
    
    const chartOption = computed(() => {
      if (!props.treeData) return {}
      
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
          data: [props.treeData],
          
          // Tree Layout
          top: '5%',
          left: '5%',
          bottom: '5%',
          right: '5%',
          
          symbolSize: (value, params) => {
            // Larger symbols for characters with data
            const character = params.data.name
            const hasData = props.characterData[character]
            const isSelected = character === props.selectedCharacter
            
            if (isSelected) return 50
            if (hasData) return 40
            return 35
          },
          
          symbol: 'rect',
          orient: 'TB', // Top to Bottom
          
          label: {
            show: true,
            position: 'inside',
            color: '#333',
            fontSize: (params) => {
              const character = params.data.name
              const isSelected = character === props.selectedCharacter
              return isSelected ? 20 : 16
            },
            fontWeight: 'bold',
            // Dynamic color based on data availability
            color: (params) => {
              const character = params.data.name
              const hasData = props.characterData[character]
              const isSelected = character === props.selectedCharacter
              
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
              const hasData = props.characterData[character]
              const isSelected = character === props.selectedCharacter
              
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
              fontSize: 18,
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
          animationDuration: 750,
          animationDurationUpdate: 750,
          
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
      
      // Only emit for single characters
      if (character && isSingleCharacter(character)) {
        emit('character-selected', character)
      }
    }
    
    function extractAllCharacters(treeData) {
      const characters = new Set()
      
      const traverse = (node) => {
        if (node.name && isSingleCharacter(node.name)) {
          characters.add(node.name)
        }
        
        if (node.children) {
          for (const child of node.children) {
            traverse(child)
          }
        }
      }
      
      traverse(treeData)
      return Array.from(characters)
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
    watch(() => props.treeData, () => {
      nextTick(() => {
        resizeChart()
      })
    })
    
    // Watch for character data changes to update node colors
    watch(() => props.characterData, () => {
      nextTick(() => {
        resizeChart()
      })
    }, { deep: true })
    
    return {
      chartRef,
      chartOption,
      totalCharacters,
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

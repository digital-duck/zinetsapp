import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { parserService } from '@/services/parser'

export const useNetworkStore = defineStore('network', () => {
  // State
  const treeData = ref(null) // Parsed tree structure
  const originalMarkdown = ref('') // Original markdown input
  const selectedNode = ref(null) // Currently selected node in the tree
  const expandedNodes = ref(new Set()) // Track expanded/collapsed nodes
  const treeLayout = ref('TB') // Tree orientation: 'TB', 'BT', 'LR', 'RL'
  const loading = ref(false)
  const error = ref(null)
  const parseTimestamp = ref(null)

  // Getters
  const hasTreeData = computed(() => {
    return treeData.value !== null && treeData.value.name
  })

  const rootCharacter = computed(() => {
    return treeData.value?.name || null
  })

  const allNodes = computed(() => {
    if (!treeData.value) return []
    
    const nodes = []
    function traverse(node, path = []) {
      nodes.push({
        ...node,
        path: [...path, node.name]
      })
      if (node.children) {
        node.children.forEach((child, index) => {
          traverse(child, [...path, node.name])
        })
      }
    }
    traverse(treeData.value)
    return nodes
  })

  const leafNodes = computed(() => {
    return allNodes.value.filter(node => !node.children || node.children.length === 0)
  })

  const branchNodes = computed(() => {
    return allNodes.value.filter(node => node.children && node.children.length > 0)
  })

  const selectedNodeData = computed(() => {
    if (!selectedNode.value || !treeData.value) return null
    
    function findNode(node, targetName) {
      if (node.name === targetName) return node
      if (node.children) {
        for (const child of node.children) {
          const found = findNode(child, targetName)
          if (found) return found
        }
      }
      return null
    }
    
    return findNode(treeData.value, selectedNode.value)
  })

  const treeStatistics = computed(() => {
    if (!treeData.value) return null
    
    return {
      totalNodes: allNodes.value.length,
      leafNodes: leafNodes.value.length,
      branchNodes: branchNodes.value.length,
      maxDepth: getMaxDepth(treeData.value),
      rootCharacter: rootCharacter.value
    }
  })

  // Actions
  async function parseMarkdown(markdownText) {
    if (!markdownText || !markdownText.trim()) {
      error.value = 'Empty markdown text'
      return false
    }

    loading.value = true
    error.value = null

    try {
      const parsedData = await parserService.parseMarkdown(markdownText)
      
      if (!parsedData || !parsedData.name) {
        throw new Error('Invalid tree structure parsed from markdown')
      }

      treeData.value = parsedData
      originalMarkdown.value = markdownText
      selectedNode.value = null
      expandedNodes.value.clear()
      parseTimestamp.value = new Date().toISOString()
      
      loading.value = false
      return true

    } catch (err) {
      error.value = err.message
      loading.value = false
      console.error('Error parsing markdown:', err)
      return false
    }
  }

  function selectNode(nodeName) {
    selectedNode.value = nodeName
  }

  function clearSelection() {
    selectedNode.value = null
  }

  function toggleNodeExpansion(nodeName) {
    if (expandedNodes.value.has(nodeName)) {
      expandedNodes.value.delete(nodeName)
    } else {
      expandedNodes.value.add(nodeName)
    }
  }

  function expandNode(nodeName) {
    expandedNodes.value.add(nodeName)
  }

  function collapseNode(nodeName) {
    expandedNodes.value.delete(nodeName)
  }

  function expandAllNodes() {
    allNodes.value.forEach(node => {
      if (node.children && node.children.length > 0) {
        expandedNodes.value.add(node.name)
      }
    })
  }

  function collapseAllNodes() {
    expandedNodes.value.clear()
  }

  function setTreeLayout(layout) {
    if (['TB', 'BT', 'LR', 'RL'].includes(layout)) {
      treeLayout.value = layout
    }
  }

  function clearTree() {
    treeData.value = null
    originalMarkdown.value = ''
    selectedNode.value = null
    expandedNodes.value.clear()
    parseTimestamp.value = null
    error.value = null
  }

  // Helper function to get maximum depth of tree
  function getMaxDepth(node, currentDepth = 0) {
    if (!node.children || node.children.length === 0) {
      return currentDepth
    }
    
    let maxChildDepth = currentDepth
    node.children.forEach(child => {
      const childDepth = getMaxDepth(child, currentDepth + 1)
      maxChildDepth = Math.max(maxChildDepth, childDepth)
    })
    
    return maxChildDepth
  }

  // Helper function to get node path
  function getNodePath(nodeName) {
    if (!treeData.value) return []
    
    function findPath(node, target, path = []) {
      const currentPath = [...path, node.name]
      
      if (node.name === target) {
        return currentPath
      }
      
      if (node.children) {
        for (const child of node.children) {
          const foundPath = findPath(child, target, currentPath)
          if (foundPath.length > 0) {
            return foundPath
          }
        }
      }
      
      return []
    }
    
    return findPath(treeData.value, nodeName)
  }

  // Helper function to get siblings of a node
  function getNodeSiblings(nodeName) {
    if (!treeData.value) return []
    
    function findSiblings(node, target, parent = null) {
      if (node.name === target && parent) {
        return parent.children.filter(child => child.name !== target)
      }
      
      if (node.children) {
        for (const child of node.children) {
          const siblings = findSiblings(child, target, node)
          if (siblings.length > 0) {
            return siblings
          }
        }
      }
      
      return []
    }
    
    return findSiblings(treeData.value, nodeName)
  }

  // Helper function to get parent of a node
  function getNodeParent(nodeName) {
    if (!treeData.value || treeData.value.name === nodeName) return null
    
    function findParent(node, target) {
      if (node.children) {
        for (const child of node.children) {
          if (child.name === target) {
            return node
          }
          const parent = findParent(child, target)
          if (parent) return parent
        }
      }
      return null
    }
    
    return findParent(treeData.value, nodeName)
  }

  // Export tree data as different formats
  function exportAsJson() {
    return treeData.value ? JSON.stringify(treeData.value, null, 2) : null
  }

  function exportAsMarkdown() {
    if (!treeData.value) return null
    
    function nodeToMarkdown(node, depth = 0) {
      const indent = '    '.repeat(depth)
      let result = depth === 0 ? node.name : `${indent}- ${node.name}`
      
      if (node.decomposition) {
        result += ` (${node.decomposition})`
      }
      
      if (node.children && node.children.length > 0) {
        node.children.forEach(child => {
          result += '\n' + nodeToMarkdown(child, depth + 1)
        })
      }
      
      return result
    }
    
    return nodeToMarkdown(treeData.value)
  }

  return {
    // State
    treeData,
    originalMarkdown,
    selectedNode,
    expandedNodes,
    treeLayout,
    loading,
    error,
    parseTimestamp,
    
    // Getters
    hasTreeData,
    rootCharacter,
    allNodes,
    leafNodes,
    branchNodes,
    selectedNodeData,
    treeStatistics,
    
    // Actions
    parseMarkdown,
    selectNode,
    clearSelection,
    toggleNodeExpansion,
    expandNode,
    collapseNode,
    expandAllNodes,
    collapseAllNodes,
    setTreeLayout,
    clearTree,
    getNodePath,
    getNodeSiblings,
    getNodeParent,
    exportAsJson,
    exportAsMarkdown
  }
})
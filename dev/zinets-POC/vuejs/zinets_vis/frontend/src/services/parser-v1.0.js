// services/parser.js - Markdown parser for character networks
// Converts markdown format to ECharts tree structure

/**
 * Markdown Parser for Chinese Character Networks
 * Converts semantic network data in markdown format into tree structure for ECharts
 * Based on the Python parse_markdown_to_tree_data function
 */
export class MarkdownParser {
  /**
   * Parse markdown text to tree data structure
   * @param {string} markdownText - Markdown content
   * @returns {Object} Tree structure for ECharts
   */
  static parseMarkdownToTree(markdownText) {
    if (!markdownText?.trim()) {
      return { name: "", children: [] }
    }

    const lines = markdownText.trim().split('\n')
    
    // Get root name (first line, remove comments)
    const rootLine = lines[0]
    const rootName = this.extractContentBeforeComment(rootLine).trim()
    
    // Initialize tree
    const tree = {
      name: rootName,
      children: []
    }

    // Skip if only one line
    if (lines.length <= 1) {
      return tree
    }

    // Parse remaining lines
    const { indentLevels, processedLines } = this.analyzeIndentation(lines.slice(1))
    
    // Build tree structure
    this.buildTreeFromIndentation(tree, processedLines, indentLevels)
    
    return tree
  }

  /**
   * Extract content before # comment
   * @param {string} line - Text line
   * @returns {string} Content before comment
   */
  static extractContentBeforeComment(line) {
    const commentIndex = line.indexOf('#')
    return commentIndex !== -1 ? line.substring(0, commentIndex) : line
  }

  /**
   * Analyze indentation patterns in the text
   * @param {string[]} lines - Array of lines to analyze
   * @returns {Object} Processed lines and indent levels
   */
  static analyzeIndentation(lines) {
    const lineData = []
    
    // First pass: collect indentation info
    for (const line of lines) {
      const contentLine = this.extractContentBeforeComment(line)
      const trimmed = contentLine.trim()
      
      // Skip empty lines or lines that don't start with dash
      if (!trimmed || !this.isValidListItem(contentLine)) {
        lineData.push(null)
        continue
      }
      
      // Measure indentation
      const indentInfo = this.measureIndentation(contentLine)
      indentInfo.content = trimmed.substring(1).trim() // Remove leading dash
      
      lineData.push(indentInfo)
    }
    
    // Second pass: convert to logical levels
    const logicalLevels = this.convertToLogicalLevels(lineData)
    
    // Filter out null entries
    const processedData = []
    const processedLevels = []
    
    for (let i = 0; i < lineData.length; i++) {
      if (lineData[i] !== null) {
        processedData.push(lineData[i])
        processedLevels.push(logicalLevels[i])
      }
    }
    
    return {
      indentLevels: processedLevels,
      processedLines: processedData
    }
  }

  /**
   * Check if line is a valid list item (starts with dash after optional whitespace)
   * @param {string} line - Line to check
   * @returns {boolean}
   */
  static isValidListItem(line) {
    return line.trimStart().startsWith('-')
  }

  /**
   * Measure indentation of a line
   * @param {string} line - Line to measure
   * @returns {Object} Indentation info
   */
  static measureIndentation(line) {
    let spaces = 0
    let tabs = 0
    
    for (const char of line) {
      if (char === ' ') {
        spaces++
      } else if (char === '\t') {
        tabs++
      } else {
        break
      }
    }
    
    return {
      type: tabs > 0 ? 'tab' : 'space',
      size: tabs > 0 ? tabs : spaces
    }
  }

  /**
   * Convert raw indentation to logical levels
   * @param {Array} lineData - Array of indentation data
   * @returns {Array} Array of logical levels
   */
  static convertToLogicalLevels(lineData) {
    const levels = []
    const nonNullData = lineData.filter(item => item !== null)
    
    if (nonNullData.length === 0) {
      return lineData.map(() => null)
    }
    
    // Determine if using tabs or spaces
    const tabCount = nonNullData.filter(item => item.type === 'tab').length
    const spaceCount = nonNullData.filter(item => item.type === 'space').length
    const usingTabs = tabCount >= spaceCount
    
    if (usingTabs) {
      // Tab-based indentation - each tab is one level
      for (const item of lineData) {
        if (item === null) {
          levels.push(null)
        } else if (item.type === 'tab') {
          levels.push(item.size)
        } else {
          // Convert spaces to tab equivalent (4 spaces = 1 tab)
          levels.push(Math.floor(item.size / 4))
        }
      }
    } else {
      // Space-based indentation - determine increment
      const spaceSizes = nonNullData
        .filter(item => item.type === 'space')
        .map(item => item.size)
        .filter(size => size > 0)
      
      let increment = this.determineSpaceIncrement(spaceSizes)
      
      for (const item of lineData) {
        if (item === null) {
          levels.push(null)
        } else if (item.type === 'space') {
          levels.push(Math.round(item.size / increment))
        } else {
          // Convert tabs to space equivalent
          levels.push(item.size * Math.floor(4 / increment))
        }
      }
    }
    
    return levels
  }

  /**
   * Determine space increment pattern
   * @param {number[]} spaceSizes - Array of space sizes
   * @returns {number} Space increment
   */
  static determineSpaceIncrement(spaceSizes) {
    if (spaceSizes.length === 0) return 4
    
    // Calculate differences between consecutive sizes
    const sortedSizes = [...new Set(spaceSizes)].sort((a, b) => a - b)
    const differences = []
    
    for (let i = 1; i < sortedSizes.length; i++) {
      const diff = sortedSizes[i] - sortedSizes[i - 1]
      if (diff > 0) differences.push(diff)
    }
    
    if (differences.length === 0) {
      // Only one unique size, guess common increments
      const size = spaceSizes[0]
      return size <= 2 ? 2 : size <= 4 ? 4 : 4
    }
    
    // Find most common difference
    const diffCounts = {}
    differences.forEach(diff => {
      diffCounts[diff] = (diffCounts[diff] || 0) + 1
    })
    
    const mostCommonDiff = Object.entries(diffCounts)
      .sort(([,a], [,b]) => b - a)[0][0]
    
    return parseInt(mostCommonDiff)
  }

  /**
   * Build tree from indentation data
   * @param {Object} tree - Root tree node
   * @param {Array} processedLines - Processed line data
   * @param {Array} indentLevels - Indent levels
   */
  static buildTreeFromIndentation(tree, processedLines, indentLevels) {
    const stack = [[0, tree]] // [level, node]
    
    for (let i = 0; i < processedLines.length; i++) {
      const level = indentLevels[i]
      const lineData = processedLines[i]
      
      if (level === null || !lineData) continue
      
      // Parse character name and decomposition
      const content = lineData.content
      const { name, decomposition } = this.parseCharacterLine(content)
      
      // Create new node
      const newNode = {
        name: name,
        children: []
      }
      
      if (decomposition) {
        newNode.decomposition = decomposition
      }
      
      // Find appropriate parent (pop stack until we find correct level)
      while (stack.length > 0 && stack[stack.length - 1][0] >= level) {
        stack.pop()
      }
      
      // Ensure we have a parent
      if (stack.length === 0) {
        stack.push([0, tree])
      }
      
      // Add to parent
      const parent = stack[stack.length - 1][1]
      parent.children.push(newNode)
      
      // Add to stack for potential children
      stack.push([level, newNode])
    }
  }

  /**
   * Parse character line to extract name and decomposition
   * @param {string} content - Line content
   * @returns {Object} Object with name and decomposition
   */
  static parseCharacterLine(content) {
    // Try both Chinese and regular parentheses
    let parts = content.split('（')
    if (parts.length === 1) {
      parts = content.split('(')
    }
    
    const name = parts[0].trim()
    let decomposition = null
    
    if (parts.length > 1) {
      // Remove closing parentheses
      decomposition = parts[1].replace(/[）)]/g, '').trim()
    }
    
    return { name, decomposition }
  }

  /**
   * Extract all unique single characters from tree
   * @param {Object} treeData - Tree structure
   * @returns {string[]} Array of unique characters
   */
  static extractAllCharacters(treeData) {
    const characters = new Set()
    
    const traverse = (node) => {
      // Only include single characters, not multi-character names
      if (node.name && this.isSingleCharacter(node.name)) {
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

  /**
   * Check if string is a single Chinese character
   * @param {string} str - String to check
   * @returns {boolean}
   */
  static isSingleCharacter(str) {
    if (!str || str.length !== 1) return false
    
    // Check if it's a Chinese character (basic range)
    const code = str.charCodeAt(0)
    return (code >= 0x4E00 && code <= 0x9FFF) || // CJK Unified Ideographs
           (code >= 0x3400 && code <= 0x4DBF) || // CJK Extension A
           (code >= 0x20000 && code <= 0x2A6DF)   // CJK Extension B
  }

  /**
   * Validate markdown format
   * @param {string} markdownText - Markdown to validate
   * @returns {Object} Validation result with errors
   */
  static validateMarkdown(markdownText) {
    const errors = []
    const warnings = []
    
    if (!markdownText || !markdownText.trim()) {
      errors.push('Markdown text is empty')
      return { valid: false, errors, warnings }
    }
    
    const lines = markdownText.trim().split('\n')
    
    // Check for root character
    if (lines.length === 0) {
      errors.push('No root character found')
      return { valid: false, errors, warnings }
    }
    
    const rootLine = this.extractContentBeforeComment(lines[0]).trim()
    if (!rootLine) {
      errors.push('Root character line is empty')
    }
    
    // Check for proper list formatting
    let hasValidItems = false
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i]
      const content = this.extractContentBeforeComment(line)
      const trimmed = content.trim()
      
      if (trimmed && !this.isValidListItem(content)) {
        warnings.push(`Line ${i + 1}: "${trimmed}" doesn't start with '-' (might not be parsed)`)
      } else if (trimmed) {
        hasValidItems = true
      }
    }
    
    if (!hasValidItems && lines.length > 1) {
      warnings.push('No valid list items found (lines should start with "-")')
    }
    
    return {
      valid: errors.length === 0,
      errors,
      warnings
    }
  }
}

// Export default instance for convenience
export default MarkdownParser

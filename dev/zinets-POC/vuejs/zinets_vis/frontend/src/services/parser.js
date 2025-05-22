// services/parser.js - Markdown parser for character networks
// Converts markdown format to ECharts tree structure

/**
 * Markdown Parser for Chinese Character Networks
 * Converts semantic network data in markdown format into tree structure for ECharts
 * Based on the Python parse_markdown_to_tree_data function with enhancements
 */
export class MarkdownParser {
  /**
   * Parse markdown text to tree data structure
   * @param {string} markdownText - Markdown content
   * @returns {Object} Tree structure for ECharts
   */
  static parseMarkdownToTree(markdownText) {
    // Input validation
    if (!markdownText || typeof markdownText !== 'string') {
      throw new Error('Invalid markdown text provided')
    }

    const trimmedText = markdownText.trim()
    if (!trimmedText) {
      return { name: "", children: [] }
    }

    const lines = trimmedText.split('\n')
    
    // Get root name (first line, remove comments)
    const rootLine = lines[0]
    const rootName = this.extractContentBeforeComment(rootLine).trim()
    
    if (!rootName) {
      throw new Error('Root character is empty or invalid')
    }

    // Initialize tree
    const tree = {
      name: rootName,
      children: []
    }

    // Skip if only one line
    if (lines.length <= 1) {
      return tree
    }

    try {
      // Parse remaining lines
      const { indentLevels, processedLines } = this.analyzeIndentation(lines.slice(1))
      
      // Build tree structure
      this.buildTreeFromIndentation(tree, processedLines, indentLevels)
      
      // Validate resulting tree
      this.validateTree(tree)
      
    } catch (error) {
      throw new Error(`Failed to parse markdown: ${error.message}`)
    }
    
    return tree
  }

  /**
   * Extract content before # comment
   * @param {string} line - Text line
   * @returns {string} Content before comment
   */
  static extractContentBeforeComment(line) {
    if (!line || typeof line !== 'string') return ''
    
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
    const validLines = []
    
    // First pass: collect indentation info
    for (let i = 0; i < lines.length; i++) {
      const originalLine = lines[i]
      const contentLine = this.extractContentBeforeComment(originalLine)
      const trimmed = contentLine.trim()
      
      // Skip empty lines or lines that don't start with dash
      if (!trimmed || !this.isValidListItem(contentLine)) {
        lineData.push(null)
        continue
      }
      
      try {
        // Measure indentation
        const indentInfo = this.measureIndentation(contentLine)
        indentInfo.content = trimmed.substring(1).trim() // Remove leading dash
        indentInfo.originalLine = originalLine
        indentInfo.lineNumber = i + 2 // +2 because we skipped root line and use 1-based numbering
        
        lineData.push(indentInfo)
        validLines.push(indentInfo)
      } catch (error) {
        console.warn(`Warning: Skipping invalid line ${i + 2}: ${error.message}`)
        lineData.push(null)
      }
    }
    
    // Validate we have at least some valid lines
    if (validLines.length === 0) {
      console.warn('No valid list items found')
      return { indentLevels: [], processedLines: [] }
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
    if (!line || typeof line !== 'string') return false
    return line.trimStart().startsWith('-')
  }

  /**
   * Measure indentation of a line
   * @param {string} line - Line to measure
   * @returns {Object} Indentation info
   */
  static measureIndentation(line) {
    if (!line || typeof line !== 'string') {
      throw new Error('Invalid line for indentation measurement')
    }

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
      const increment = this.determineSpaceIncrement(nonNullData)
      
      for (const item of lineData) {
        if (item === null) {
          levels.push(null)
        } else if (item.type === 'space') {
          levels.push(Math.round(item.size / increment))
        } else {
          // Convert tabs to space equivalent
          levels.push(item.size * Math.ceil(4 / increment))
        }
      }
    }
    
    return levels
  }

  /**
   * Determine space increment pattern
   * @param {Object[]} lineData - Array of line data objects
   * @returns {number} Space increment
   */
  static determineSpaceIncrement(lineData) {
    const spaceSizes = lineData
      .filter(item => item.type === 'space')
      .map(item => item.size)
      .filter(size => size > 0)
    
    if (spaceSizes.length === 0) return 4
    
    // Calculate differences between consecutive sizes
    const sortedSizes = [...new Set(spaceSizes)].sort((a, b) => a - b)
    
    if (sortedSizes.length === 1) {
      // Only one unique size, infer common increments
      const size = sortedSizes[0]
      if (size <= 2) return 2
      if (size <= 4) return 4
      if (size <= 8) return 4
      return size
    }
    
    const differences = []
    for (let i = 1; i < sortedSizes.length; i++) {
      const diff = sortedSizes[i] - sortedSizes[i - 1]
      if (diff > 0) differences.push(diff)
    }
    
    if (differences.length === 0) return 4
    
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
    if (!processedLines || processedLines.length === 0) return
    
    const stack = [[0, tree]] // [level, node]
    
    for (let i = 0; i < processedLines.length; i++) {
      const level = indentLevels[i]
      const lineData = processedLines[i]
      
      if (level === null || !lineData) continue
      
      try {
        // Parse character name and decomposition
        const content = lineData.content
        const { name, decomposition } = this.parseCharacterLine(content)
        
        if (!name) {
          console.warn(`Skipping line ${lineData.lineNumber}: empty character name`)
          continue
        }
        
        // Create new node
        const newNode = {
          name: name,
          children: []
        }
        
        if (decomposition) {
          newNode.decomposition = decomposition
        }
        
        // Add metadata if needed for debugging
        if (process.env.NODE_ENV === 'development') {
          newNode._metadata = {
            lineNumber: lineData.lineNumber,
            originalLine: lineData.originalLine,
            level: level
          }
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
      } catch (error) {
        console.warn(`Skipping line ${lineData.lineNumber}: ${error.message}`)
      }
    }
  }

  /**
   * Parse character line to extract name and decomposition
   * @param {string} content - Line content
   * @returns {Object} Object with name and decomposition
   */
  static parseCharacterLine(content) {
    if (!content || typeof content !== 'string') {
      throw new Error('Invalid content for character line')
    }

    // Try both Chinese and regular parentheses for decomposition
    let parts = content.split('（')
    if (parts.length === 1) {
      parts = content.split('(')
    }
    
    const name = parts[0].trim()
    let decomposition = null
    
    if (parts.length > 1) {
      // Remove closing parentheses and clean up
      decomposition = parts[1]
        .replace(/[）)]/g, '')
        .trim()
      
      // If decomposition is empty after cleaning, set to null
      if (!decomposition) {
        decomposition = null
      }
    }
    
    return { name, decomposition }
  }

  /**
   * Extract all unique single characters from tree
   * @param {Object} treeData - Tree structure
   * @returns {string[]} Array of unique characters
   */
  static extractAllCharacters(treeData) {
    if (!treeData || typeof treeData !== 'object') {
      return []
    }

    const characters = new Set()
    
    const traverse = (node) => {
      // Only include single characters, not multi-character names
      if (node.name && this.isSingleCharacter(node.name)) {
        characters.add(node.name)
      }
      
      if (node.children && Array.isArray(node.children)) {
        for (const child of node.children) {
          traverse(child)
        }
      }
    }
    
    traverse(treeData)
    return Array.from(characters).sort()
  }

  /**
   * Check if string is a single Chinese character
   * @param {string} str - String to check
   * @returns {boolean}
   */
  static isSingleCharacter(str) {
    if (!str || typeof str !== 'string' || str.length !== 1) return false
    
    // Check if it's a Chinese character (comprehensive range)
    const code = str.charCodeAt(0)
    return (code >= 0x4E00 && code <= 0x9FFF) || // CJK Unified Ideographs
           (code >= 0x3400 && code <= 0x4DBF) || // CJK Extension A
           (code >= 0x20000 && code <= 0x2A6DF) || // CJK Extension B
           (code >= 0x2A700 && code <= 0x2B73F) || // CJK Extension C
           (code >= 0x2B740 && code <= 0x2B81F) || // CJK Extension D
           (code >= 0x2B820 && code <= 0x2CEAF) || // CJK Extension E
           (code >= 0xF900 && code <= 0xFAFF) ||   // CJK Compatibility Ideographs
           (code >= 0x2F800 && code <= 0x2FA1F)    // CJK Compatibility Supplement
  }

  /**
   * Validate markdown format
   * @param {string} markdownText - Markdown to validate
   * @returns {Object} Validation result with errors and warnings
   */
  static validateMarkdown(markdownText) {
    const errors = []
    const warnings = []
    
    // Basic input validation
    if (!markdownText || typeof markdownText !== 'string') {
      errors.push('Markdown text must be a non-empty string')
      return { valid: false, errors, warnings }
    }
    
    const trimmedText = markdownText.trim()
    if (!trimmedText) {
      errors.push('Markdown text is empty')
      return { valid: false, errors, warnings }
    }
    
    const lines = trimmedText.split('\n')
    
    // Check for root character
    if (lines.length === 0) {
      errors.push('No root character found')
      return { valid: false, errors, warnings }
    }
    
    const rootLine = this.extractContentBeforeComment(lines[0]).trim()
    if (!rootLine) {
      errors.push('Root character line is empty or contains only comments')
    } else if (!this.isSingleCharacter(rootLine)) {
      warnings.push('Root element is not a single Chinese character')
    }
    
    // Check for proper list formatting
    let hasValidItems = false
    let invalidLineCount = 0
    
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i]
      const content = this.extractContentBeforeComment(line)
      const trimmed = content.trim()
      
      // Skip empty lines
      if (!trimmed) continue
      
      if (!this.isValidListItem(content)) {
        invalidLineCount++
        warnings.push(`Line ${i + 1}: "${trimmed}" doesn't start with '-' (might not be parsed)`)
      } else {
        hasValidItems = true
        
        // Check for valid character in list item
        const { name } = this.parseCharacterLine(trimmed.substring(1).trim())
        if (name && !this.isSingleCharacter(name) && name.length > 1) {
          warnings.push(`Line ${i + 1}: "${name}" is not a single character`)
        }
      }
    }
    
    if (!hasValidItems && lines.length > 1) {
      warnings.push('No valid list items found (lines should start with "-")')
    }
    
    if (invalidLineCount > 0) {
      warnings.push(`${invalidLineCount} lines may not be parsed correctly`)
    }
    
    // Try to parse to catch structural issues
    try {
      this.parseMarkdownToTree(markdownText)
    } catch (error) {
      errors.push(`Parsing error: ${error.message}`)
    }
    
    return {
      valid: errors.length === 0,
      errors,
      warnings,
      stats: {
        totalLines: lines.length,
        validItems: hasValidItems ? 'Yes' : 'No',
        invalidLines: invalidLineCount
      }
    }
  }

  /**
   * Validate tree structure
   * @param {Object} tree - Tree to validate
   * @throws {Error} If tree structure is invalid
   */
  static validateTree(tree) {
    if (!tree || typeof tree !== 'object') {
      throw new Error('Tree must be an object')
    }
    
    if (!tree.name) {
      throw new Error('Tree root must have a name')
    }
    
    if (!tree.children || !Array.isArray(tree.children)) {
      throw new Error('Tree root must have a children array')
    }
    
    // Recursively validate children
    const validateNode = (node, path = '') => {
      if (!node || typeof node !== 'object') {
        throw new Error(`Invalid node at path: ${path}`)
      }
      
      if (!node.name) {
        throw new Error(`Node missing name at path: ${path}`)
      }
      
      if (!node.children || !Array.isArray(node.children)) {
        throw new Error(`Node missing children array at path: ${path}`)
      }
      
      // Validate children recursively
      node.children.forEach((child, index) => {
        validateNode(child, `${path}/${node.name}[${index}]`)
      })
    }
    
    tree.children.forEach((child, index) => {
      validateNode(child, `root[${index}]`)
    })
  }

  /**
   * Get tree statistics
   * @param {Object} tree - Tree structure
   * @returns {Object} Tree statistics
   */
  static getTreeStatistics(tree) {
    if (!tree) return null
    
    let totalNodes = 0
    let maxDepth = 0
    let leafNodes = 0
    const characterCount = new Set()
    
    const traverse = (node, depth = 0) => {
      totalNodes++
      maxDepth = Math.max(maxDepth, depth)
      
      if (this.isSingleCharacter(node.name)) {
        characterCount.add(node.name)
      }
      
      if (!node.children || node.children.length === 0) {
        leafNodes++
      } else {
        node.children.forEach(child => traverse(child, depth + 1))
      }
    }
    
    traverse(tree)
    
    return {
      totalNodes,
      maxDepth,
      leafNodes,
      branchNodes: totalNodes - leafNodes,
      uniqueCharacters: characterCount.size,
      characters: Array.from(characterCount).sort()
    }
  }

  /**
   * Convert tree to different format (for export)
   * @param {Object} tree - Tree structure
   * @param {string} format - Target format ('json', 'text', 'markdown')
   * @returns {string} Converted tree
   */
  static exportTree(tree, format = 'markdown') {
    if (!tree) return ''
    
    switch (format.toLowerCase()) {
      case 'json':
        return JSON.stringify(tree, null, 2)
        
      case 'text':
        return this.treeToText(tree)
        
      case 'markdown':
      default:
        return this.treeToMarkdown(tree)
    }
  }

  /**
   * Convert tree back to markdown format
   * @param {Object} tree - Tree structure
   * @returns {string} Markdown text
   */
  static treeToMarkdown(tree) {
    if (!tree) return ''
    
    const lines = [tree.name]
    
    const traverse = (node, indent = '') => {
      if (node.children && node.children.length > 0) {
        for (const child of node.children) {
          let line = `${indent}- ${child.name}`
          if (child.decomposition) {
            line += `(${child.decomposition})`
          }
          lines.push(line)
          traverse(child, indent + '    ')
        }
      }
    }
    
    traverse(tree)
    return lines.join('\n')
  }

  /**
   * Convert tree to plain text representation
   * @param {Object} tree - Tree structure
   * @returns {string} Text representation
   */
  static treeToText(tree) {
    if (!tree) return ''
    
    const lines = [tree.name]
    
    const traverse = (node, prefix = '', isLast = true) => {
      if (node.children && node.children.length > 0) {
        for (let i = 0; i < node.children.length; i++) {
          const child = node.children[i]
          const isLastChild = i === node.children.length - 1
          const connector = isLastChild ? '└── ' : '├── '
          const nextPrefix = prefix + (isLastChild ? '    ' : '│   ')
          
          let line = `${prefix}${connector}${child.name}`
          if (child.decomposition) {
            line += ` (${child.decomposition})`
          }
          lines.push(line)
          traverse(child, nextPrefix, isLastChild)
        }
      }
    }
    
    traverse(tree)
    return lines.join('\n')
  }
}

// Export default instance for convenience
export default MarkdownParser
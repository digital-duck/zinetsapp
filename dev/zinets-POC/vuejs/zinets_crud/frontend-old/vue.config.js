const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // Configure dev server
  devServer: {
    port: 8080,
    proxy: {
      // Proxy API requests to backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  
  // Configure build output
  outputDir: 'dist',
  assetsDir: 'static',
  
  // Other configuration options
  pages: {
    index: {
      entry: 'src/main.js',
      template: 'public/index.html',
      filename: 'index.html',
      title: 'Chinese Character Manager'
    }
  }
})
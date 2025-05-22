// main.js - Entry point for ZiNets Visualization App
import { createApp } from 'vue'
import App from './App.vue'
import { useSettingsStore } from './stores/settings'

// Import Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// Import Element Plus icons
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Import Pinia for state management (optional, for future use)
import { createPinia } from 'pinia'

// Import custom styles
import './styles/main.css'

// Create Vue app instance
const app = createApp(App)

// Install Element Plus
app.use(ElementPlus)

// Register all Element Plus icons globally
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Install Pinia (state management)
const pinia = createPinia()
app.use(pinia)


// Initialize settings store to load saved settings
app.runWithContext(() => {
  const settingsStore = useSettingsStore()
  settingsStore.loadFromLocalStorage()
})


// Global error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err)
  console.error('Component info:', info)
  
  // You can add error reporting service here
  // For example: reportError(err, instance, info)
}

// Global warning handler (only in development)
if (import.meta.env.DEV) {
  app.config.warnHandler = (msg, instance, trace) => {
    console.warn('Vue warning:', msg)
    console.warn('Component trace:', trace)
  }
}

// Global properties (accessible in all components)
app.config.globalProperties.$appVersion = '1.0.0'
app.config.globalProperties.$appName = 'ZiNets Visualization'

// Mount the app to the DOM
app.mount('#app')

// Enable Vue DevTools in development
if (import.meta.env.DEV) {
  window.__VUE_DEVTOOLS_GLOBAL_HOOK__ = window.__VUE_DEVTOOLS_GLOBAL_HOOK__ || {}
  window.__VUE_DEVTOOLS_GLOBAL_HOOK__.Vue = app
}

// Log app initialization info
console.log(`🚀 ${app.config.globalProperties.$appName} v${app.config.globalProperties.$appVersion} initialized`)
console.log('🔧 Environment:', import.meta.env.MODE)
console.log('🌐 API Base URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')

// Performance monitoring (optional)
if (import.meta.env.PROD) {
  // Measure and log performance metrics in production
  window.addEventListener('load', () => {
    if ('performance' in window) {
      const perfData = performance.getEntriesByType('navigation')[0]
      console.log('📊 App load time:', Math.round(perfData.loadEventEnd - perfData.fetchStart), 'ms')
    }
  })
}

// Service Worker registration (for PWA, optional)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('🔧 SW registered: ', registration)
      })
      .catch((registrationError) => {
        console.log('❌ SW registration failed: ', registrationError)
      })
  })
}

export default app

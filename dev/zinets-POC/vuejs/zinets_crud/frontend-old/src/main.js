// main.js
import { createApp } from 'vue'
import App from './App.vue'

// Import Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// Import Element Plus icons
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Create the Vue app instance
const app = createApp(App)

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// Use Element Plus
app.use(ElementPlus)

// Mount the app to the DOM
app.mount('#app')
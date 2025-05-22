## 📁 ZiNets Vis - Directory Structure Explained

### Root Level Files
```
zinets_vis/
├── package.json       # Dependencies and scripts
├── vite.config.js     # Vite configuration (proxy to backend)
└── README.md          # Project documentation
```

### Public Directory
```
public/
├── index.html         # HTML template
└── favicon.ico        # App icon
```

### Main Source Directory
```
src/
├── main.js            # Vue app initialization
├── App.vue            # Root Vue component
├── components/        # Reusable Vue components
├── services/          # Business logic (API, LLM)
├── stores/            # Pinia state management
└── styles/            # CSS files
```

### Components (src/components/)
```
components/
├── NetworkInput.vue   # Form for entering markdown or uploading files
├── CharacterTree.vue  # ECharts tree visualization component
├── CharacterDetails.vue # Panel showing character details (pinyin, meaning, etc.)
└── SettingsDialog.vue # Modal for API key and app settings
```

### Services (src/services/)
```
services/
├── api.js             # Axios calls to FastAPI backend
├── llm.js             # Google Gemini API integration
├── cache.js           # Character caching logic
└── parser.js          # Convert markdown to tree structure
```

### State Stores (src/stores/)
```
stores/
├── characters.js      # Character data and caching state
├── network.js         # Tree/network structure state
└── settings.js        # User settings (API keys, preferences)
```

### Styles (src/styles/)
```
styles/
├── main.css           # Global app styles
└── components.css     # Component-specific styles
```

## 🔄 Data Flow

1. **Input** → NetworkInput.vue → Markdown parser → Tree structure
2. **Tree** → Extract characters → Check cache → LLM API → Backend cache
3. **Display** → CharacterTree.vue (ECharts) → CharacterDetails.vue
4. **State** → Pinia stores manage all data flow

## 🎯 Similar to zinets_crud

- Same Vue 3 + Element Plus setup
- Same backend proxy configuration
- Same service pattern (api.js)
- Same simple package.json structure
- No complex tooling (ESLint/Prettier optional)

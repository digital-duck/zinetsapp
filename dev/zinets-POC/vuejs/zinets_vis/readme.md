# ZiNets Visualization - Vue.js Frontend

An interactive Vue.js application for visualizing Chinese character networks using ECharts, with integrated LLM API support for fetching character data.

## 🌟 Features

- **Interactive Character Network Visualization** - Tree-based display using ECharts
- **Multiple Input Methods** - Paste markdown, upload files, or use presets
- **LLM Integration** - Fetch character data from Google Gemini API
- **Backend Caching** - Integrated with FastAPI + SQLite caching system
- **Multi-language Support** - Generate content in English, Chinese, Spanish, Korean, Arabic
- **Real-time Character Details** - Click any node to see detailed information
- **External Search Integration** - Quick links to Chinese dictionaries and resources
- **Responsive Design** - Works on desktop and mobile devices

## 🛠️ Tech Stack

- **Vue 3** with Composition API
- **Element Plus** for UI components
- **ECharts & vue-echarts** for data visualization
- **Axios** for HTTP requests
- **Vite** for development and building

## 📋 Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- FastAPI backend running on `http://localhost:8000` (for caching)
- Google Gemini API key (for fetching character data)

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/digital-duck/zinets_vis.git
cd zinets_vis

# backend
cd backend
pip install -r requirements.txt

# frontend
cd ../frontend
npm install
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```env
# Optional: Backend API URL (defaults to http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000

# Optional: Default settings
VITE_DEFAULT_LANGUAGE=English
VITE_DEFAULT_BATCH_SIZE=10
```

### 3. Development Server

```bash
# Start development server

# backend
cd ~/projects/digital-duck/zinets_vis/backend
uvicorn main:app --reload

# test FastAPI at URL= http://localhost:8000/docs

# frontend
cd ~/projects/digital-duck/zinets_vis/frontend
npm run dev --reload

# Access the application
# run app at URL= http://localhost:8081
```

### 4. Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 🎯 Usage

### Getting Started

1. **Launch the app** and click "Load Network"
2. **Configure your Gemini API key** in Settings
3. **Choose input method**:
   - **Paste Text**: Copy markdown network data
   - **Upload File**: Select a .md or .txt file
   - **Use Preset**: Choose from built-in networks

### Input Format

The app accepts semantic networks in markdown format:

```markdown
心
- 想(相+心)
    - 愿(原+心)
    - 惟(忄+隹)
- 情(忄+青)
    - 愛(爫+冖+心+夊)
    - 恋(亦+心)
- 忘(亡+心)
    - 怯(忄+去)
    - 悔(忄+每)
```

### Available Presets

- **Default (藻)**: Algae-based character network
- **Heart (心)**: Mind and emotion characters
- **Water (水)**: Water-related character network

### Character Data Sources

The app fetches character information including:
- **Pinyin** pronunciation with tone marks
- **Meaning** explanations
- **Composition** structural breakdown
- **Phrases** 5 common usage examples

## ⚙️ Configuration

### Settings Panel

Access via the Settings button in the header:

- **Gemini API Key**: Required for fetching new character data
- **Default Language**: Language for character explanations
- **Batch Size**: Number of characters processed per API call (1-20)
- **Auto-fetch Data**: Automatically load character data when importing networks

### Caching System

- **Backend Integration**: Uses FastAPI + SQLite for persistent caching
- **Automatic Caching**: New character data is immediately saved
- **Cache Statistics**: View total cached characters and last update
- **Cache Management**: Clear cache when needed

## 🔍 Character Details

Click any character node to view:

### Overview Tab
- Character meaning and composition explanation
- Structural breakdown of the character

### Phrases Tab
- 5 common phrases with pinyin and English translation
- Usage examples in context

### Search Tab
- Quick links to external Chinese dictionaries:
  - 汉典 (Zdic)
  - 千篇 (Qianp)
  - 文学网 (Hwxnet)
  - 字源 (Hanziyuan)
  - 多功能字庫 (CUHK)
  - Baidu Search

## 🏗️ Project Structure

```
src/
├── App.vue                 # Main application component
├── main.js                 # Application entry point
├── services/
│   ├── llmService.js       # LLM API integration & backend caching
│   └── markdownParser.js   # Markdown to tree parser
├── assets/                 # Static assets
└── styles/                 # Global styles

public/
├── index.html             # HTML template
└── favicon.ico            # Application icon
```

## 🔧 Development

### Key Components

1. **LLMService**: Handles Gemini API calls and backend caching
2. **MarkdownParser**: Converts markdown networks to ECharts tree format
3. **Main App**: Manages UI state and coordinates components

### API Integration

The frontend communicates with the FastAPI backend for:
- Character data caching (`/api/characters/*`)
- Cache statistics (`/api/cache/stats`)
- Cache management (`/api/cache/clear`)

### Adding New Features

#### Custom Presets
Add to `PRESET_NETWORKS` in `App.vue`:

```javascript
const PRESET_NETWORKS = {
  myNetwork: `新字
- 子字1
- 子字2
    - 孙字1`
}
```

#### Additional Search Sites
Add to `SEARCH_SITES` array:

```javascript
{ 
  key: 'mysite', 
  name: 'My Site', 
  url: 'https://mysite.com/search?q=' 
}
```

## 🎨 Customization

### Styling

The app uses Element Plus themes. Customize in `src/styles/`:

```css
/* Override Element Plus variables */
:root {
  --el-color-primary: #your-color;
  --el-color-success: #your-color;
}
```

### Chart Configuration

Modify ECharts options in the `chartOption` computed property:

```javascript
const chartOption = computed(() => ({
  series: [{
    type: 'tree',
    symbolSize: 50,  // Adjust node size
    label: {
      fontSize: 20,  // Adjust font size
      color: '#custom-color'
    }
  }]
}))
```

## 🐛 Troubleshooting

### Common Issues

**Characters not loading:**
- Check if Gemini API key is configured
- Verify backend is running on correct port
- Check browser console for API errors

**Markdown parsing errors:**
- Ensure proper indentation (spaces or tabs, not mixed)
- Verify markdown format matches examples
- Check for special characters in content

**Cache not working:**
- Confirm FastAPI backend is accessible
- Check network tab for failed API calls
- Verify backend database permissions

### Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Android Chrome)

## 📚 Learning Resources

### Vue.js Concepts Demonstrated

- **Composition API**: Modern Vue 3 reactive programming
- **Reactive Data**: `ref()`, `reactive()`, `computed()`
- **Lifecycle Hooks**: `onMounted()`, `watch()`
- **Component Communication**: Props, events, provide/inject
- **State Management**: Centralized app state

### ECharts Integration

- **Vue-ECharts**: Official Vue wrapper for ECharts
- **Tree Charts**: Hierarchical data visualization
- **Interactive Events**: Click handlers and tooltips
- **Responsive Design**: Auto-resize and mobile support

### API Integration Patterns

- **Async/Await**: Modern JavaScript promises
- **Error Handling**: Try-catch and user feedback
- **Caching Strategies**: Backend persistence
- **Batch Processing**: Efficient API usage

## 🔗 Related Projects

- **Chinese Character Manager**: CRUD operations for character data
- **ZiNets Python CLI**: Original command-line visualization tool
- **FastAPI Backend**: Shared API for both applications

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- 📧 Create an issue on GitHub
- 💬 Check existing documentation
- 🔍 Search previous issues for solutions

---

Built with ❤️ for Chinese language learners and character enthusiasts

# Chinese Character Manager - Frontend

A Vue.js 3 application built with Vite for managing Chinese character data. Uses Element Plus for UI components and axios for API communication.

## Features

- **Modern Vue 3** with Composition API
- **Element Plus** for beautiful UI components
- **Vite** for fast development and building
- **Responsive design** that works on desktop and mobile
- **Real-time search** with debounced input
- **Pagination** for large datasets
- **Form validation** with comprehensive error handling
- **Loading states** for better user experience

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next generation frontend build tool
- **Element Plus** - Vue 3 based component library
- **Axios** - Promise based HTTP client
- **ESLint** - JavaScript linter
- **Prettier** - Code formatter

## Project Structure

```
src/
├── App.vue              # Main application component
├── main.js              # Application entry point
├── style.css            # Global styles
└── services/
    └── api.js           # API service layer
```

## Setup and Installation

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn package manager

### Installation

1. **Clone or create the project directory**
   ```bash
   mkdir chinese-character-manager-frontend
   cd chinese-character-manager-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   Navigate to `http://localhost:8080`

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint to check code quality
- `npm run format` - Format code with Prettier

## Configuration

### Environment Variables

Create a `.env` file in the root directory to customize settings:

```env
# API Base URL (defaults to http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000
```

### Vite Configuration

The `vite.config.js` file includes:
- Vue plugin configuration
- Development server with API proxy
- Build optimization settings
- Path aliases (@/ for src/)

## API Integration

The frontend communicates with a FastAPI backend through the API service (`src/services/api.js`). The service includes:

- Axios instance with interceptors
- Error handling
- Request/response logging
- Automatic retries for failed requests

### API Endpoints Used

- `GET /api/characters` - Fetch characters with pagination and filtering
- `POST /api/characters` - Create new character
- `PUT /api/characters/{id}` - Update existing character
- `PATCH /api/characters/{id}/deactivate` - Soft delete character

## Component Features

### Search and Filtering

- Real-time search with 500ms debounce
- Filter by character, meaning, provider, and status
- Auto-search on input changes
- Reset functionality

### Character Table

- Sortable columns
- Clickable rows for editing
- Status indicators with color-coded tags
- Responsive design with overflow handling
- Empty state messaging

### Character Form

- Form validation with real-time feedback
- Toggle switches for boolean values
- Textarea support with HTML preview
- Save/Cancel/Delete actions
- Loading states during operations

### Pagination

- Configurable page sizes (10, 20, 50, 100)
- Jump to page functionality
- Total count display
- Responsive pagination controls

## Styling

The application uses:
- Element Plus default theme
- Custom CSS for layout and spacing
- Responsive design breakpoints
- Print-friendly styles
- Custom scrollbar styling

## Error Handling

- API error interception and user-friendly messages
- Form validation with inline error display
- Loading states for all async operations
- Confirmation dialogs for destructive actions

## Performance Optimization

- Vite's fast HMR for development
- Optimized production builds
- Lazy loading of components (if needed)
- Debounced search to reduce API calls
- Efficient Vue 3 reactivity system

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Tips

1. **Use Vue DevTools** for debugging reactive state
2. **Check Network tab** to monitor API calls
3. **Use ESLint** to maintain code quality
4. **Format with Prettier** before committing
5. **Test on different screen sizes** for responsiveness

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure backend is running on port 8000
   - Check CORS configuration in backend
   - Verify API_BASE_URL in environment

2. **Build Errors**
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check for TypeScript errors if using TS
   - Ensure all imports are correct

3. **Style Issues**
   - Clear browser cache
   - Check for CSS conflicts
   - Verify Element Plus imports

## Contributing

1. Follow Vue 3 composition API patterns
2. Use ESLint and Prettier for code formatting
3. Write descriptive commit messages
4. Test on multiple browsers and screen sizes
5. Update documentation for new features

## License

This project is licensed under the MIT License.

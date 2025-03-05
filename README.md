# ZiNets: A Modern Chinese Character Learning Platform

## Overview

ZiNets is an innovative Chinese character learning platform based on network analysis of character decomposition. Unlike traditional approaches that require memorizing thousands of isolated characters, ZiNets breaks down the Chinese writing system into 422 elemental characters (元字) that combine systematically to form all complex characters.

This approach reveals Chinese characters as a natural, self-organizing system with properties similar to those found in physics, biology, and mathematics. ZiNets makes Chinese character learning more intuitive, systematic, and accessible by focusing on understanding rather than rote memorization.

## Key Features

- **Elemental Character Explorer**: Browse and search the 422 fundamental building blocks of Chinese writing
- **Interactive Decomposition Analysis**: Visualize how characters break down into their constituent parts
- **Character Encyclopedia**: Comprehensive information about each character and its relationships
- **Zi-Matrix Visualization**: Explore character structure through an 11-position spatial model
- **Network Navigation**: Move freely between related characters in an interconnected web of meaning
- **AI-Assisted Learning**: Inline chatbot for personalized explanations and exploration
- **Flashcard System**: Create custom study decks with spaced repetition

## Research Foundation

ZiNets is based on original research that:

1. Identified 422 elemental characters through computational network analysis
2. Developed the Zi-Matrix spatial decomposition model
3. Analyzed character structure across natural categories
4. Discovered organizing principles similar to natural systems
5. Mapped the evolution from concrete to abstract meanings

For more details, see the research paper: [A New Exploration into Chinese Characters: from Simplification to Deeper Understanding](https://arxiv.org/abs/2502.19428)

## Architecture

ZiNets consists of three interconnected components:

1. **Web Frontend**: 
   - Initially built with Streamlit for rapid prototyping
   - Future migration to React.js for scalability and enhanced interactivity
   - Responsive design for accessibility across devices

2. **API Layer**:
   - FastAPI backend serving character data and decomposition logic
   - Endpoints for character retrieval, decomposition, relationships, and search
   - Integration with LLM APIs for chatbot functionality

3. **Database**:
   - SQLite for development/prototype
   - Schema designed to efficiently represent character relationships and properties
   - Future migration path to more scalable database solutions

## Pages Structure

The application consists of three primary interconnected pages:

### 1. Elemental Characters Page (元字)
- Gallery view of all 422 elemental characters
- Filtering by category, stroke count, and frequency
- Detailed information on each character's origin and usage

### 2. Character Decomposition Page (字分解)
- Interactive visualization of character breakdown
- Zi-Matrix display showing component positioning
- Navigation to component characters or characters that use this component
- Save to flashcard functionality

### 3. Character Encyclopedia Page (字典)
- Comprehensive details on meaning, etymology, and usage
- Network visualization showing character relationships
- Examples in context with translations
- Related characters and compounds

## Development Roadmap

### Phase 1: Prototype (Current)
- Streamlit frontend with basic functionality
- SQLite database with core character data
- FastAPI backend with essential endpoints
- Basic character decomposition visualization

### Phase 2: Enhanced Features
- Improved visualizations and interactions
- Integration with LLM for chatbot functionality
- User accounts and progress tracking
- Flashcard system with spaced repetition

### Phase 3: Production Platform
- Migration to React.js frontend
- Expanded character database with comprehensive attributes
- Advanced network visualizations
- Mobile application development
- Multi-language support for native translations

### Phase 4: Educational Integration
- Curriculum alignment features
- Teacher dashboard and student management
- Progress analytics and learning path optimization
- Integration with other learning resources

## Installation

### Prerequisites
- Python 3.11+
- Node.js (for React development)
- SQLite (for development)

### Setup
```bash
# Clone the repository
git clone https://github.com/digital-duck/zinetsapp.git
cd zinets

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Run the development server
streamlit run app.py
```

### API Development
```bash
# Run FastAPI server
uvicorn api.main:app --reload
```

## Contributing

Contributions to ZiNets are welcome! Please see the [contributing guidelines](CONTRIBUTING.md) for more information.

### Areas for Contribution
- Character data enhancement
- Visualization improvements
- User experience refinements
- Educational content development
- Performance optimizations
- Internationalization

## License

This project is licensed under the [Apache License](LICENSE).

## Acknowledgments

- The open-source community providing tools that make this project possible

## Contact

For questions, suggestions, or collaboration opportunities, please open an issue on GitHub or contact the project maintainer at [p2p2learn@outlook.com].

---

*ZiNets: Transforming Chinese character learning from knowledge acquisition to deep understanding.*
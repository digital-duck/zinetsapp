# Chinese Character Network Generator - Setup and Usage

This tool generates an interactive visualization of Chinese character relationships using a semantic network. It uses the ECharts JavaScript library for visualization and the Google Gemini API to fetch character information.

## Prerequisites

1. Python 3.6 or higher
2. An internet connection
3. A Google Gemini API key

## Installation

1. **Install the Google Generative AI library**:
   ```bash
   pip install google-generativeai
   ```

2. **Set up your Google Gemini API key**:
   ```bash
   # On Linux/Mac
   export GEMINI_API_KEY="your-api-key-here"

   # On Windows (Command Prompt)
   set GEMINI_API_KEY=your-api-key-here

   # On Windows (PowerShell)
   $env:GEMINI_API_KEY="your-api-key-here"
   ```

3. **Save the script** as `chinese_network_generator.py`

## Usage

### Basic Usage

```python
from chinese_network_generator import process_semantic_network

# Your semantic network data
semantic_network = """日
- 音(立 + 日)
    - 暗（日 + 音）
    - 意（心 + 音）
- 智（知 + 日）
- 暗（日 + 音）
- 白（丿 + 日）
    - 伯（亻 + 白）
    - 百（一 + 白）
        - 陌（阝 + 百）
        - 宿（亻 + 宀 + 百） 
    - 帛（白 + 巾）
        - 棉（木 + 帛）
        - 锦（钅 + 帛）
- 晶(日 + 日 + 日)
    - 曐(晶 + 生)"""

# Generate the HTML file
output_file = process_semantic_network(semantic_network, output_file="my_network.html")
print(f"Network visualization created at: {output_file}")
```

### Without Gemini API

If you don't have a Gemini API key or prefer not to use it, you can generate the visualization with placeholder data:

```python
output_file = process_semantic_network(semantic_network, output_file="my_network.html", use_gemini=False)
```

### Running the Script Directly

You can also run the script directly:

```bash
python chinese_network_generator.py
```

This will use the example semantic network and generate a file named `character_network.html`.

## Semantic Network Format

The semantic network should be in the following format:

```
ROOT_CHARACTER
- CHILD_CHARACTER1(DECOMPOSITION1)
    - GRANDCHILD_CHARACTER1(DECOMPOSITION1)
    - GRANDCHILD_CHARACTER2(DECOMPOSITION2)
- CHILD_CHARACTER2(DECOMPOSITION2)
    - GRANDCHILD_CHARACTER3(DECOMPOSITION3)
```

Example:
```
日
- 白(丿 + 日)
    - 伯(亻 + 白)
    - 百(一 + 白)
```

## Troubleshooting

### Model Selection Issues

If you encounter errors related to model selection, the script will try to use several different Gemini models in the following order:
1. gemini-1.5-pro
2. gemini-1.5-flash
3. gemini-pro
4. gemini-1.0-pro

If none of these are available, it will fall back to placeholder data.

### JSON Parsing Issues

The script includes multiple fallback methods for parsing the JSON response from Gemini. If you're still encountering issues, you can:

1. Try simplifying your semantic network (use fewer characters)
2. Run with `use_gemini=False` to verify the rest of the functionality works
3. Modify the script to print the raw response from Gemini for debugging

### API Key Issues

If you see "Warning: GEMINI_API_KEY not found in environment variables", make sure you've properly set the environment variable. On Windows, you may need to restart your command prompt or IDE after setting the environment variable.

## How It Works

1. The script parses the semantic network structure from markdown format
2. It extracts all unique characters from the network
3. It calls the Gemini API to get information for each character
4. It generates an HTML file with the visualization using ECharts

The visualization includes:
- An interactive network diagram on the left
- Character information (pinyin, meaning, composition, phrases) on the right
- Click interactions to view details about each character

## Customization

You can customize the appearance of the visualization by modifying the CSS and ECharts options in the `generate_html` function.
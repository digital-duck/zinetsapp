import json
import os
import re
import time
import google.generativeai as genai

def parse_markdown_to_tree_data(markdown_text):
    """
    Parse semantic network data in markdown format into a tree data structure.
    """
    lines = markdown_text.strip().split('\n')
    root_name = lines[0].strip()
    
    # Initialize the root node
    tree_data = {
        'name': root_name,
        'children': []
    }
    
    # Stack to keep track of current parent node at each level
    stack = [(0, tree_data)]  # (indent_level, node)
    
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
            
        # Calculate indentation level (number of tabs or equivalent spaces)
        indent_level = (len(lines[i]) - len(lines[i].lstrip('\t'))) 
        if indent_level == 0 and lines[i].startswith('    '):
            # Handle spaces instead of tabs (4 spaces = 1 tab)
            indent_level = (len(lines[i]) - len(lines[i].lstrip(' '))) // 4
            
        # Extract character name and decomposition if present
        parts = line.split('（')
        if len(parts) == 1:
            parts = line.split('(')
            
        char_name = parts[0].strip('- \t')
        decomposition = None
        if len(parts) > 1:
            decomposition = parts[1].strip('）)')
        
        # Create new node
        new_node = {
            'name': char_name,
            'symbolSize': 25,
            'children': []
        }
        
        if decomposition:
            new_node['decomposition'] = decomposition
        
        # Find the appropriate parent for this node
        while stack and stack[-1][0] >= indent_level:
            stack.pop()
            
        # Add the new node to its parent's children
        parent = stack[-1][1]
        parent['children'].append(new_node)
        
        # Add this node to the stack as a potential parent for subsequent nodes
        stack.append((indent_level, new_node))
    
    return tree_data

def extract_all_characters(tree_data):
    """
    Extract all unique characters from the tree data structure.
    """
    characters = set()
    
    def dfs(node):
        if 'name' in node and len(node['name']) == 1:
            characters.add(node['name'])
        
        if 'children' in node:
            for child in node['children']:
                dfs(child)
    
    dfs(tree_data)
    return list(characters)

def get_character_data_from_gemini(characters):
    """
    Use Google Gemini API to generate character data using the official Python library.
    
    Args:
        characters: A list of Chinese characters
        
    Returns:
        A dictionary with character data
    """

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment variables. Using placeholder data.")
        return {char: generate_placeholder_data(char) for char in characters}
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')  # Or your preferred model
    
    # Construct the prompt for Gemini
    chars_str = ', '.join([f"'{char}'" for char in characters])
    prompt = f"""
    Given a list of Chinese characters [{chars_str}], please generate a JavaScript object called 'characterData' with the following structure for each character:

    {{
      '日': {{
        pinyin: 'rì',
        meaning: 'sun; day; date, day of the month',
        composition: 'Pictograph of the sun',
        phrases: '日出 (rì chū) - sunrise<br>日落 (rì luò) - sunset<br>日子 (rì zi) - day; date; life<br>日常 (rì cháng) - daily; everyday<br>日期 (rì qī) - date'
      }},
      // And so on for each character
    }}

    For each character, include:
    1. The correct pinyin with tone marks
    2. The primary meanings in English
    3. The character composition explanation
    4. At least 5 common phrases or words that use this character, with pinyin and English translation

    Format the phrases with HTML <br> tags between each phrase.
    Only return the JavaScript object with no additional explanation or markdown formatting.
    Ensure JavaScript object key/value are enclosed in double quotes. 
    Ensure the object is valid JavaScript and can be directly used in a script.
    """
    
    # Make the API call using the library
    try:
        response = model.generate_content(prompt)
        
        # Extract the response text
        response_text = response.text
        
        # Parse the JavaScript object from the response
        character_data = parse_js_object(response_text)
        
        # Verify we have data for all characters
        for char in characters:
            if char not in character_data:
                character_data[char] = generate_placeholder_data(char)
        
        return character_data
        
    except Exception as e:
        print(f"Error calling Gemini API with Python library: {e}")
        print("Using placeholder data instead.")
        return {char: generate_placeholder_data(char) for char in characters}

def parse_js_object(text):
    """
    Parse a JavaScript object string into a Python dictionary.
    This is a simplified parser that works for the characterData format.
    """
    # Clean up the text to extract just the object
    # Remove leading and trailing code blocks, comments, etc.
    pattern = r'(?:const\s+characterData\s*=\s*)?(\{[\s\S]*\})'
    match = re.search(pattern, text)
    if match:
        js_obj_str = match.group(1)
    else:
        js_obj_str = text
    
    # Try to convert to valid JSON
    # Replace single quotes with double quotes
    js_obj_str = js_obj_str.replace("'", '"')
    
    # Fix property names without quotes
    js_obj_str = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', js_obj_str)
    
    # Remove trailing commas
    js_obj_str = re.sub(r',\s*([}\]])', r'\1', js_obj_str)
    
    try:
        # Parse as JSON
        return json.loads(js_obj_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JS object: {e}")
        print(f"Object string: {js_obj_str}")
        return {}

def generate_placeholder_data(character):
    """
    Generate placeholder data for characters when API fails.
    """
    return {
        'pinyin': 'Unknown',
        'meaning': 'Meaning not available',
        'composition': 'Composition not available',
        'phrases': f'{character}语 - Example phrase 1<br>{character}文 - Example phrase 2'
    }

def generate_html(tree_data, character_data, title="Chinese Character Network"):
    """
    Generate HTML with the tree data and character data embedded as JavaScript objects.
    """
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
    <style>
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Tahoma, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
        }}
        #chart-container {{
            width: 60%;
            height: 100%;
        }}
        #info-panel {{
            width: 40%;
            padding: 20px;
            background-color: #f5f5f5;
            overflow-y: auto;
            border-left: 1px solid #ddd;
        }}
        .node-tooltip {{
            position: absolute;
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 4px;
            border: 1px solid #ddd;
            pointer-events: none;
            font-size: 14px;
            display: none;
        }}
        .character {{
            font-size: 72px;
            text-align: center;
            margin-bottom: 10px;
        }}
        .pinyin {{
            font-size: 18px;
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 20px;
        }}
        .section h3 {{
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            color: #333;
        }}
        .composition {{
            display: flex;
            align-items: center;
            font-size: 16px;
            margin-bottom: 10px;
        }}
        .phrases {{
            line-height: 1.6;
        }}
        .meaning {{
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div id="chart-container"></div>
    <div id="info-panel">
        <div class="character" id="selected-char">{root_character}</div>
        <div class="pinyin" id="selected-pinyin">{root_pinyin}</div>
        
        <div class="section">
            <h3>Meaning</h3>
            <div class="meaning" id="selected-meaning">
                {root_meaning}
            </div>
        </div>
        
        <div class="section">
            <h3>Composition</h3>
            <div class="composition" id="selected-composition">
                {root_composition}
            </div>
        </div>
        
        <div class="section">
            <h3>Related Phrases</h3>
            <div class="phrases" id="selected-phrases">
                {root_phrases}
            </div>
        </div>
    </div>

    <script>
        // Character data repository
        const characterData = {character_data_json};

        // Initialize ECharts
        const chartContainer = document.getElementById('chart-container');
        const chart = echarts.init(chartContainer);

        // Define the tree structure based on your data
        const treeData = {tree_data_json};

        // Set the option
        const option = {{
            tooltip: {{
                trigger: 'item',
                formatter: function(params) {{
                    if (params.data.decomposition) {{
                        return `<div style="font-size:18px; font-weight:bold; margin-bottom:5px;">${{params.data.name}}</div>
                                <div>${{params.data.decomposition}}</div>`;
                    }} else {{
                        return params.data.name;
                    }}
                }},
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                borderColor: '#ccc',
                borderWidth: 1,
                padding: 10,
                textStyle: {{
                    color: '#333',
                    fontSize: 16
                }}
            }},
            series: [
                {{
                    type: 'tree',
                    data: [treeData],
                    top: '5%',
                    left: '10%',
                    bottom: '5%',
                    right: '20%',
                    symbolSize: 25,
                    orient: 'TB',
                    symbol: 'circle',
                    label: {{
                        position: 'right',
                        distance: 0,
                        fontSize: 35,
                        fontWeight: 'bold'
                    }},
                    leaves: {{
                        label: {{
                            position: 'right',
                            verticalAlign: 'middle',
                            align: 'center'
                        }}
                    }},
                    emphasis: {{
                        focus: 'descendant'
                    }},
                    expandAndCollapse: false,
                    animationDuration: 550,
                    animationDurationUpdate: 750
                }}
            ]
        }};

        // Set the initial option and render
        chart.setOption(option);

        // Handle node click event
        chart.on('click', function(params) {{
            const zi = params.data.name;
            if (zi) {{
                const charData = characterData[zi];
                if (charData) {{
                    // Update info panel
                    document.getElementById('selected-char').textContent = zi;
                    document.getElementById('selected-pinyin').textContent = charData.pinyin;
                    document.getElementById('selected-meaning').textContent = charData.meaning;
                    document.getElementById('selected-composition').textContent = charData.composition;
                    document.getElementById('selected-phrases').innerHTML = charData.phrases;
                }}
            }}
        }});

        // Make chart responsive
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
</body>
</html>
"""

    # Get root character
    root_character = tree_data['name']
    root_data = character_data.get(root_character, {
        'pinyin': 'Unknown',
        'meaning': 'No data available',
        'composition': 'No data available',
        'phrases': 'No phrases available'
    })
    
    # Replace placeholders in HTML template
    html = html_template.format(
        title=title,
        root_character=root_character,
        root_pinyin=root_data['pinyin'],
        root_meaning=root_data['meaning'],
        root_composition=root_data['composition'],
        root_phrases=root_data['phrases'],
        character_data_json=json.dumps(character_data, ensure_ascii=False, indent=4),
        tree_data_json=json.dumps(tree_data, ensure_ascii=False, indent=4)
    )
    
    return html

def process_semantic_network(markdown_text, output_file="character_network.html", use_gemini=True):
    """
    Process semantic network data and generate HTML file.
    
    Args:
        markdown_text: The semantic network data in markdown format
        output_file: Output HTML file path
        use_gemini: Whether to use Gemini API for character data
    """
    # Parse markdown to tree data
    tree_data = parse_markdown_to_tree_data(markdown_text)
    
    # Extract all characters from the tree
    characters = extract_all_characters(tree_data)
    
    # Get character data from Gemini API or generate placeholder data
    character_data = get_character_data_from_gemini(characters) if use_gemini else {
        char: generate_placeholder_data(char) for char in characters
    }
    
    # Generate HTML with embedded JavaScript objects
    html = generate_html(tree_data, character_data)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML file generated successfully: {output_file}")
    return output_file

def main():
    """
    Main function to run the script.
    """
    # Example semantic network data
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
    
    # Process the semantic network with Gemini API and generate HTML
    output_file = process_semantic_network(semantic_network, output_file="character_network.html")
    print(f"Network visualization created at: {output_file}")

if __name__ == "__main__":
    main()
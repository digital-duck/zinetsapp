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
    try:
        import google.generativeai as genai
    except ImportError:
        print("Google Generative AI library not found. Install with 'pip install google-generativeai'")
        return {char: generate_placeholder_data(char) for char in characters}
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment variables. Using placeholder data.")
        return {char: generate_placeholder_data(char) for char in characters}
    
    # Configure the Google Generative AI library with your API key
    genai.configure(api_key=api_key)
    
    # Use the correct model - try a few different models that might be available
    try:
        # Try to use the best available model, falling back to others if needed
        # https://ai.google.dev/gemini-api/docs/models
        models_to_try = [
            "gemini-2.0-flash",
            'gemini-1.5-flash', 
            # "gemini-2.0-flash-lite",
            # 'gemini-1.5-pro', 
        ]
        
        model = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"Using Gemini model: {model_name}")
                break
            except Exception as model_error:
                print(f"Could not use model {model_name}: {model_error}")
                continue
                
        if model is None:
            raise Exception("No Gemini models are available")
            
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        return {char: generate_placeholder_data(char) for char in characters}
    
    # Construct the prompt for Gemini with improved instructions for JSON formatting
    chars_str = ', '.join([f"'{char}'" for char in characters])
    prompt = f"""
    Generate a valid JSON object with information about these Chinese characters: {chars_str}
    
    THIS IS EXTREMELY IMPORTANT: Use valid JSON format without ANY errors!
    
    FORMATTING RULES:
    1. Never use double quotes inside property values, use single quotes or avoid quotes completely
    2. If you must include quotes in text descriptions, use the word 'quote' instead (e.g., "one quote more than white")
    3. Make sure all JSON property names are surrounded by double quotes
    4. Make sure all property values are surrounded by double quotes
    5. Be extremely careful with quotes in descriptions - they must be properly escaped to be valid JSON
    6. Use <br> tags for line breaks in phrases
    7. No trailing commas at the end of JSON objects
    
    For each character, include these properties:
    - "pinyin": with the correct pronunciation and tone marks
    - "meaning": main English meanings 
    - "composition": character components explanation (without using quotes in the explanation)
    - "phrases": 5 common phrases using the character with pinyin and meaning
    
    Format example:
    {{
      "{characters[0]}": {{
        "pinyin": "pronunciation",
        "meaning": "main meanings",
        "composition": "description of components without any quotes",
        "phrases": "phrase1 (pinyin) - meaning<br>phrase2 (pinyin) - meaning"
      }}
    }}
    
    Return ONLY the JSON object. No explanations, code blocks, or other formatting.
    """
    
    # Make the API call using the library
    try:
        # Set safety settings to allow more content through to avoid filtering
        safety_settings = [
            {
                "category": "HARM_CATEGORY_DANGEROUS",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH", 
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
        ]
        
        # Use generation config to get better output
        generation_config = {
            "temperature": 0.2,  # Lower temperature for more predictable output
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        # Generate content with these settings
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Extract the response text
        response_text = response.text
        
        log_header = f"\n\nGemini Model: {model_name}\nDatetime: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        # Save the raw response for debugging
        with open("gemini_response_raw.txt", "a", encoding="utf-8") as f:
            f.write(log_header)
            f.write(response_text)
        print("Gemini API response saved to gemini_response.txt")
        
        # Pre-process the response to fix common issues before parsing
        cleaned_text = clean_gemini_response(response_text)
        
        # Save the cleaned response for debugging
        with open("gemini_response_cleaned.txt", "a", encoding="utf-8") as f:
            f.write(log_header)
            f.write(cleaned_text)
        print("Cleaned Gemini response saved to gemini_response_cleaned.txt")
        
        # Parse the JavaScript object from the cleaned response
        character_data = parse_js_object(cleaned_text)
        
        # Verify we have data for all characters
        for char in characters:
            if char not in character_data:
                character_data[char] = generate_placeholder_data(char)
        
        return character_data
        
    except Exception as e:
        print(f"Error calling Gemini API with Python library: {e}")
        print("Using placeholder data instead.")
        return {char: generate_placeholder_data(char) for char in characters}

def clean_gemini_response(text):
    """
    Apply targeted fixes to common problems in Gemini responses before attempting JSON parsing.
    Handles specific issues with quotes and escapes in Gemini outputs.
    
    Args:
        text: The raw text response from Gemini
        
    Returns:
        Cleaned text that is more likely to parse as valid JSON
    """
    import re
    import json
    
    # Remove markdown code block formatting
    text = re.sub(r'```javascript|```json|```js|```', '', text)
    text = text.strip()
    
    # First, check if the response is already valid JSON
    try:
        json.loads(text)
        # If we can parse it directly, return it as is
        return text
    except json.JSONDecodeError:
        # If not, apply our fixes
        pass
    
    # Fix 1: Check for and remove incorrect backslash escapes
    # This pattern matches \"meaning\" type entries where backslashes shouldn't be
    text = re.sub(r'\\\"([a-zA-Z]+)\\\"', r'"\1"', text)
    
    # Fix 2: Check for specific patterns of incorrectly escaped quotes in property values
    lines = text.split('\n')
    fixed_lines = []
    
    skip_line = False
    for i, line in enumerate(lines):
        if skip_line:
            skip_line = False
            continue
            
        # Check for the specific pattern where a backslash and quote appear at the end of a line
        # followed by a line that starts with a backslash and quote
        if i < len(lines) - 1:
            current_line = line.strip()
            next_line = lines[i+1].strip()
            
            # Pattern: "property": "value\", \
            # \"nextproperty": "nextvalue"
            if current_line.endswith('\\",') and next_line.startswith('\\"'):
                # Remove the incorrect escapes and join the lines
                current_line = current_line.replace('\\",', '",')
                next_line = next_line.replace('\\"', '"')
                fixed_lines.append(current_line)
                fixed_lines.append(next_line)
                skip_line = True
                continue
        
        # Fix standalone property with incorrect escapes
        if "\\\"" in line:
            line = line.replace("\\\"", '"')
        
        fixed_lines.append(line)
    
    text = '\n'.join(fixed_lines)
    
    # Fix 3: Handle embedded quotes in property values
    # This is a more general approach that tries to identify and fix property values with embedded quotes
    try:
        # Try to parse the JSON again to see if our initial fixes worked
        json.loads(text)
        return text
    except json.JSONDecodeError as e:
        # Get error position
        error_info = str(e)
        try:
            line_no = int(error_info.split('line')[1].split()[0])
            col_no = int(error_info.split('column')[1].split()[0])
            
            # Get the problematic line and context
            error_line = lines[line_no-1]
            
            # If the error is about unescaped quotes, try to fix them
            if 'Expecting' in error_info and 'delimiter' in error_info:
                # Split the text into chunks before and after the error position
                before_error = text[:text.index(error_line) + col_no]
                after_error = text[text.index(error_line) + col_no:]
                
                # Try to identify if we're in a property value and fix it
                property_pattern = r'"([^"]+)":\s*"([^"]*)'
                match = re.search(property_pattern, before_error[::-1])
                
                if match:
                    # We found a property value that might be missing a closing quote
                    # or has embedded quotes
                    
                    # Look for the next property or closing brace
                    next_property = re.search(r'",\s*"[^"]+":|"}', after_error)
                    
                    if next_property:
                        # Extract the problematic value
                        value_end = next_property.start() + len(after_error) - len(after_error[next_property.start():])
                        problematic_value = text[len(before_error)-match.end():value_end]
                        
                        # Replace embedded quotes with escaped quotes
                        fixed_value = problematic_value.replace('"', '\\"')
                        
                        # Replace in the original text
                        text = text[:len(before_error)-match.end()] + fixed_value + text[value_end:]
        except:
            # If there's an error in our error handling, just continue with other fixes
            pass
    
    # Fix 4: Another attempt at fixing property values with embedded quotes
    # This uses a more direct approach with regex
    property_value_pattern = r'"([^"]+)":\s*"([^"]*)("(?:[^{},]*)"[^"]*)"'
    
    # Find all instances of the pattern
    matches = list(re.finditer(property_value_pattern, text))
    
    # Process matches from the end to avoid changing positions
    for match in reversed(matches):
        # Extract the parts
        full_match = match.group(0)
        property_name = match.group(1)
        prefix = match.group(2)
        problematic_part = match.group(3)
        
        # Fix the problematic part by escaping quotes
        fixed_part = problematic_part.replace('"', '\\"')
        
        # Replace in the original text
        fixed_match = f'"{property_name}": "{prefix}{fixed_part}'
        text = text[:match.start()] + fixed_match + text[match.end():]
    
    # Fix 5: Ensure all property names are properly quoted
    text = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', text)
    
    # Fix 6: Remove trailing commas before closing braces
    text = re.sub(r',(\s*})', r'\1', text)
    
    # Final simple cleanup
    # Replace any remaining problematic patterns we've seen
    text = text.replace('\\",\n    \\"', '",\n    "')
    
    return text

def parse_js_object(text):
    """
    Parse a JavaScript object string into a Python dictionary.
    This parser is designed to handle both clean and problematic JSON formats.
    
    Args:
        text: The text to parse
        
    Returns:
        A dictionary representation of the parsed object
    """
    import re
    import json
    
    # First, perform basic cleanup
    # Remove any markdown code blocks if present
    text = re.sub(r'```javascript|```json|```js|```', '', text)
    text = text.strip()
    
    # ATTEMPT 1: Try direct JSON parsing first - handles well-formed JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Basic JSON parsing failed: {e}")
        # Continue to more complex parsing methods
    
    # ATTEMPT 2: Try with some basic preprocessing
    try:
        # Ensure all property names are quoted
        js_obj_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', text)
        
        # Replace single quotes with double quotes for string values
        js_obj_str = js_obj_str.replace("'", '"')
        
        # Remove trailing commas before closing braces or brackets
        js_obj_str = re.sub(r',(\s*[}\]])', r'\1', js_obj_str)
        
        # Try parsing again
        return json.loads(js_obj_str)
    except json.JSONDecodeError as e:
        print(f"Preprocessed JSON parsing failed: {e}")
        # Continue to more complex parsing methods
    
    # ATTEMPT 3: Try to extract character data directly using regex
    character_data = {}
    try:
        # Find all character entries - this pattern should match complete character objects
        pattern = r'"([^"]{1,4})"\s*:\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}'
        char_matches = re.finditer(pattern, text)
        
        for match in char_matches:
            char = match.group(1)
            if len(char) == 1 and re.match(r'[\u4e00-\u9fff]', char):  # Check if it's a Chinese character
                properties_text = match.group(2)
                
                # Extract properties
                char_data = {}
                
                # For each property we care about, extract it
                for prop in ["pinyin", "meaning", "composition", "phrases"]:
                    prop_pattern = r'"{}"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'.format(prop)
                    prop_match = re.search(prop_pattern, properties_text)
                    if prop_match:
                        char_data[prop] = prop_match.group(1)
                
                if char_data:  # Only add if we found at least one property
                    character_data[char] = char_data
        
        if character_data:
            print(f"Successfully extracted data for {len(character_data)} characters using regex method.")
            return character_data
            
    except Exception as e:
        print(f"Regex extraction failed: {e}")
    
    # ATTEMPT 4: Try using a direct line-by-line approach
    try:
        # This is a much simpler parser that just looks for patterns in each line
        lines = text.split('\n')
        current_char = None
        current_props = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a character definition
            char_match = re.match(r'["\s]*([^"]{1,4})["\s]*:', line)
            if char_match and '{' in line:
                # If we were processing a character, add it to our data
                if current_char and current_props:
                    character_data[current_char] = current_props
                
                # Start processing a new character
                potential_char = char_match.group(1)
                if len(potential_char) == 1 and re.match(r'[\u4e00-\u9fff]', potential_char):
                    current_char = potential_char
                    current_props = {}
            
            # Check if this is a property
            elif current_char and ':' in line and not line.strip().startswith('{') and not line.strip().startswith('}'):
                try:
                    prop_parts = line.split(':', 1)
                    if len(prop_parts) == 2:
                        prop_name = prop_parts[0].strip(' "\'')
                        prop_value = prop_parts[1].strip()
                        
                        # Clean up the value - remove quotes and commas at end
                        if prop_value.startswith('"') and (prop_value.endswith('"') or prop_value.endswith('",') or prop_value.endswith('",\n')):
                            prop_value = prop_value.strip('"').rstrip(',').rstrip()
                        
                        if prop_name in ["pinyin", "meaning", "composition", "phrases"]:
                            current_props[prop_name] = prop_value
                except Exception as line_error:
                    print(f"Error processing line: {line_error}")
            
            # Check if we're closing a character object
            elif current_char and '}' in line:
                if current_props:
                    character_data[current_char] = current_props
                    current_props = {}
        
        # Add the last character if we were processing one
        if current_char and current_props:
            character_data[current_char] = current_props
        
        if character_data:
            print(f"Successfully extracted data for {len(character_data)} characters using line parser.")
            return character_data
            
    except Exception as e:
        print(f"Line-by-line parser failed: {e}")
    
    # ATTEMPT 5: Direct manual extract of just the keys and values
    try:
        # This is an even more basic approach that just looks for specific patterns in the whole text
        for char in text:
            if re.match(r'[\u4e00-\u9fff]', char):  # If it's a Chinese character
                character_data[char] = {}
                for prop in ["pinyin", "meaning", "composition", "phrases"]:
                    pattern = fr'"?{prop}"?\s*:\s*"([^"]+)"'
                    match = re.search(pattern, text)
                    if match:
                        character_data[char][prop] = match.group(1)
        
        if character_data:
            print(f"Extracted partial data using key-value extraction.")
            return character_data
    
    except Exception as e:
        print(f"All parsing methods failed: {e}")
    
    # If everything fails, return an empty dict (the calling function will use placeholder data)
    print("All parsing methods failed. Using placeholder data.")
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
    output_file = process_semantic_network(semantic_network, output_file="zinet_vis.html")
    print(f"Network visualization created at: {output_file}")

if __name__ == "__main__":
    main()
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
    This function handles specific issues observed in Gemini outputs.
    
    Args:
        text: The raw text response from Gemini
        
    Returns:
        Cleaned text that is more likely to parse as valid JSON
    """
    import re
    
    # Remove markdown code block formatting
    text = re.sub(r'```javascript|```json|```js|```', '', text)
    text = text.strip()
    
    # Fix 1: Handle issue with quotes inside quotes by properly escaping them
    # Problem pattern: "meaning": "text with "quotes" inside"
    
    lines = text.split('\n')
    fixed_lines = []
    
    in_value = False
    for line in lines:
        if not in_value:
            # Check if this line contains a property and a value start
            if re.search(r'"[^"]+"\s*:\s*"', line) and line.count('"') > 2 and not line.strip().endswith('"'):
                # This line starts a multi-line value with quotes
                in_value = True
                # Replace quotes in the value part only
                parts = line.split(':', 1)
                if len(parts) == 2:
                    property_part = parts[0]
                    value_part = parts[1]
                    
                    # Find where the value starts (first quote after colon)
                    value_start = value_part.find('"')
                    if value_start != -1:
                        prefix = value_part[:value_start+1]
                        actual_value = value_part[value_start+1:]
                        # Replace quotes in the actual value
                        actual_value = actual_value.replace('"', '\\"')
                        value_part = prefix + actual_value
                    
                    fixed_line = property_part + ':' + value_part
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
            else:
                # Normal line handling
                if '"' in line:
                    # If it's a complete property-value pair on one line with embedded quotes
                    # Example: "meaning": "hundred; numerous; all kinds of"
                    match = re.match(r'(\s*"[^"]+"\s*:\s*")(.*)(".*)', line)
                    if match:
                        before_value, value, after_value = match.groups()
                        # Replace quotes in the value part only
                        value = value.replace('"', '\\"')
                        line = before_value + value + after_value
                
                fixed_lines.append(line)
        else:
            # We're in the middle of a multi-line value
            if line.strip().endswith('"') or line.strip().endswith('",'):
                # This line ends the value
                in_value = False
                # Replace quotes except the last one
                last_quote_pos = line.rfind('"')
                if last_quote_pos != -1:
                    before_last_quote = line[:last_quote_pos]
                    after_last_quote = line[last_quote_pos:]
                    before_last_quote = before_last_quote.replace('"', '\\"')
                    line = before_last_quote + after_last_quote
            else:
                # Middle of multi-line value
                line = line.replace('"', '\\"')
            
            fixed_lines.append(line)
    
    text = '\n'.join(fixed_lines)
    
    # Fix 2: Specific pattern observed in example: Escape quotes in composition explanations
    # Example: "composition": "One (一) above White (白). Can be thought of as "one" more than "white" to indicate a large quantity."
    text = re.sub(r'(:"[^"]*")([^"]*)"([^"]*)"([^"]*")', r'\1\2\"\3\"\4', text)
    
    # Fix 3: Handle missing quotes or unmatched quotes in property values
    # Check for and fix property values that might be missing end quotes
    lines = text.split('\n')
    for i in range(len(lines)):
        line = lines[i].strip()
        if ':' in line and line.count('"') % 2 == 1 and not line.endswith('"') and not line.endswith('",'):
            # This line has an odd number of quotes and doesn't end with a quote
            # It's likely missing a closing quote
            if line.endswith(','):
                lines[i] = line[:-1] + '",';
            else:
                lines[i] = line + '"';
    
    text = '\n'.join(lines)
    
    # Fix 4: Ensure all property names are properly quoted
    text = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', text)
    
    # Fix 5: Remove trailing commas before closing braces
    text = re.sub(r',(\s*})', r'\1', text)
    
    return text

def parse_js_object(text):
    """
    Parse a JavaScript object string into a Python dictionary.
    Highly robust parser that can handle the actual format returned by Gemini.
    """
    import re
    import json
    
    # Clean up the text
    # Remove any markdown code blocks if present
    text = re.sub(r'```javascript|```json|```js|```', '', text)
    
    # If there's a const declaration, extract just the object
    pattern = r'(?:const\s+characterData\s*=\s*)?(\{[\s\S]*\})'
    match = re.search(pattern, text)
    if match:
        js_obj_str = match.group(1)
    else:
        js_obj_str = text.strip()
    
    # PREPROCESSING: Handle problematic cases
    
    # 1. Save all properly double-quoted strings to protect them
    # Find all strings that are already properly double-quoted
    placeholders = {}
    placeholder_counter = 0
    
    def save_string(match):
        nonlocal placeholder_counter
        placeholder = f"__PLACEHOLDER_{placeholder_counter}__"
        placeholders[placeholder] = match.group(0)
        placeholder_counter += 1
        return placeholder
    
    # Temporarily replace properly double-quoted strings
    pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    js_obj_str = re.sub(pattern, save_string, js_obj_str)
    
    # 2. Fix unquoted property names
    js_obj_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', js_obj_str)
    
    # 3. Replace single quotes with double quotes
    js_obj_str = js_obj_str.replace("'", '"')
    
    # 4. Remove problematic escape sequences
    # Remove backslashes before quotes that aren't properly escaped
    js_obj_str = re.sub(r'(?<!\\)\\(?=")', '', js_obj_str)
    
    # 5. Handle embedded double quotes inside strings
    # Find patterns that look like: "string "with" quotes"
    # This regex finds text between double quotes that contains double quotes
    def fix_embedded_quotes(match):
        # Replace any embedded quotes with &quot;
        text = match.group(1)
        text = text.replace('"', '&quot;')
        return f'"{text}"'
    
    # This pattern finds strings that might have embedded quotes
    pattern = r'"([^"]*"[^"]*"[^"]*)"'
    while re.search(pattern, js_obj_str):
        js_obj_str = re.sub(pattern, fix_embedded_quotes, js_obj_str)
    
    # 6. Handle other common JSON issues
    # Remove trailing commas
    js_obj_str = re.sub(r',\s*([}\]])', r'\1', js_obj_str)
    
    # 7. Restore the properly quoted strings
    for placeholder, original in placeholders.items():
        js_obj_str = js_obj_str.replace(placeholder, original)
    
    # Now try to parse with the standard JSON parser
    try:
        return json.loads(js_obj_str)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        
        # If that fails, try our manual character-by-character parsing approach
        character_data = {}
        
        try:
            # FALLBACK #1: Use regex to extract character data directly
            # First, split the JSON by character entries
            char_entries = re.finditer(r'"([^"]{1,4})"\s*:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', js_obj_str)
            
            for entry in char_entries:
                char = entry.group(1)
                if len(char) == 1 and re.match(r'[\u4e00-\u9fff]', char):  # Verify it's a Chinese character
                    properties_text = entry.group(2)
                    
                    # Extract properties
                    char_data = {}
                    
                    # For each property we care about, try to extract it
                    for prop in ["pinyin", "meaning", "composition", "phrases"]:
                        prop_pattern = r'"{}"\s*:\s*"([^"]*(?:\\.[^"]*)*)"'.format(prop)
                        prop_match = re.search(prop_pattern, properties_text)
                        if prop_match:
                            # Clean up the value - unescape quotes, etc.
                            value = prop_match.group(1)
                            value = value.replace('\\', '')  # Remove escapes
                            value = value.replace('&quot;', '"')  # Replace &quot; with actual quotes
                            char_data[prop] = value
                    
                    if char_data:  # Only add if we found at least one property
                        character_data[char] = char_data
            
            if character_data:
                print(f"Successfully parsed data for {len(character_data)} characters using regex method.")
                return character_data
                
        except Exception as regex_error:
            print(f"Regex parsing method failed: {regex_error}")
        
        try:
            # FALLBACK #2: Simple line-by-line parser
            lines = js_obj_str.split('\n')
            current_char = None
            
            for line in lines:
                line = line.strip()
                
                # Look for character definitions
                char_match = re.match(r'"([^"]{1,4})"\s*:', line)
                if char_match and '{' in line:
                    potential_char = char_match.group(1)
                    if len(potential_char) == 1 and re.match(r'[\u4e00-\u9fff]', potential_char):
                        current_char = potential_char
                        character_data[current_char] = {}
                
                # Look for property definitions
                if current_char and ':' in line:
                    # Try to match property name and value
                    prop_match = re.match(r'"([^"]+)"\s*:\s*"([^"]*)"', line)
                    if prop_match:
                        prop_name, prop_value = prop_match.groups()
                        # Clean the value
                        prop_value = prop_value.replace('\\', '')
                        prop_value = prop_value.replace('&quot;', '"')
                        character_data[current_char][prop_name] = prop_value
            
            if character_data:
                print(f"Successfully parsed data for {len(character_data)} characters using line-by-line method.")
                return character_data
                
        except Exception as line_error:
            print(f"Line-by-line parsing method failed: {line_error}")
        
        # If all methods fail, try one last approach
        try:
            # FALLBACK #3: Use ast.literal_eval for a more flexible (but potentially less safe) parsing
            import ast
            
            # Replace some problematic patterns to make it more like Python literals
            # Replace all property names with Python string literals
            py_obj_str = re.sub(r'"([^"]+)"\s*:', r"'\1':", js_obj_str)
            
            # Replace any remaining double quotes with single quotes
            py_obj_str = py_obj_str.replace('"', "'")
            
            # Try to evaluate as Python literal
            char_dict = ast.literal_eval(py_obj_str)
            
            # Convert to our expected format
            for char, data in char_dict.items():
                if len(char) == 1 and re.match(r'[\u4e00-\u9fff]', char):
                    character_data[char] = {
                        key: str(value).replace('&quot;', '"') 
                        for key, value in data.items()
                    }
            
            if character_data:
                print(f"Successfully parsed data for {len(character_data)} characters using ast.literal_eval.")
                return character_data
                
        except Exception as ast_error:
            print(f"ast.literal_eval parsing method failed: {ast_error}")
        
        # FINAL FALLBACK: Manual character detection and property extraction
        try:
            for char in js_obj_str:
                if re.match(r'[\u4e00-\u9fff]', char):  # If it's a Chinese character
                    # Look for its entry in the response
                    char_pattern = fr'"{re.escape(char)}"\s*:\s*\{{(.*?)\}}'
                    char_match = re.search(char_pattern, js_obj_str, re.DOTALL)
                    
                    if char_match:
                        # Create entry with at least placeholder data
                        character_data[char] = generate_placeholder_data(char)
                        
                        # Try to extract whatever properties we can
                        props_str = char_match.group(1)
                        
                        for prop in ["pinyin", "meaning", "composition", "phrases"]:
                            # More relaxed pattern matching
                            prop_pattern = fr'"{prop}"[^"]*:([^,}}]*)'
                            prop_match = re.search(prop_pattern, props_str)
                            
                            if prop_match:
                                # Extract and clean up the value as best we can
                                value = prop_match.group(1).strip()
                                if value.startswith('"') and value.endswith('"'):
                                    value = value[1:-1]
                                # Clean it up
                                value = value.replace('\\', '')
                                value = value.replace('&quot;', '"')
                                character_data[char][prop] = value
            
            if character_data:
                print(f"Extracted partial data for {len(character_data)} characters using character detection method.")
                return character_data
                
        except Exception as e:
            print(f"All parsing methods failed: {e}")
            
        # If absolutely everything fails, return an empty dict
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
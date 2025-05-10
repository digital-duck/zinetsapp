import json
import os
import re
import time
import click
import sqlite3
from datetime import datetime
from tqdm import tqdm

DEFAULT_NETWORK = """藻
        - 艹
        - 澡
            - 氵
            - 喿
                - 品
                        - 口 
                        - 口 
                        - 口 
                - 木"""

# Database configuration
CACHE_DB = "zinets_cache.sqlite"

def setup_cache_db():
    """
    Set up the SQLite cache database if it doesn't exist.
    """
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    
    # Create character cache table if it doesn't exist
    c.execute('''
    CREATE TABLE IF NOT EXISTS character_cache (
        character TEXT PRIMARY KEY,
        pinyin TEXT,
        meaning TEXT,
        composition TEXT,
        phrases TEXT,
        source TEXT,
        timestamp TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    
def get_cached_character(character):
    """
    Get character data from cache if available.
    
    Args:
        character: The Chinese character to look up
        
    Returns:
        Dict with character data or None if not in cache
    """
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    
    c.execute("SELECT pinyin, meaning, composition, phrases FROM character_cache WHERE character = ?", 
              (character,))
    result = c.fetchone()
    
    conn.close()
    
    if result:
        return {
            'pinyin': result[0],
            'meaning': result[1],
            'composition': result[2],
            'phrases': result[3]
        }
    return None

def cache_character(character, data, source="gemini"):
    """
    Save character data to cache.
    
    Args:
        character: The Chinese character
        data: Dict containing character data
        source: Source of the data (e.g., "gemini", "placeholder")
    """
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    c.execute('''
    INSERT OR REPLACE INTO character_cache 
    (character, pinyin, meaning, composition, phrases, source, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        character, 
        data['pinyin'], 
        data['meaning'], 
        data['composition'], 
        data['phrases'], 
        source,
        timestamp
    ))
    
    conn.commit()
    conn.close()

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

def get_character_data_from_gemini(characters, debug_flag=True, use_cache=True):
    """
    Use Google Gemini API to generate character data using the official Python library.
    With caching support to reduce API calls.
    
    Args:
        characters: A list of Chinese characters
        debug_flag: Whether to save debug information
        use_cache: Whether to use cached data

    Returns:
        A dictionary with character data
    """
    # Set up cache database if using cache
    if use_cache:
        setup_cache_db()
    
    # Initialize result dictionary
    character_data = {}
    
    # Check cache first if enabled
    if use_cache:
        # Create a progress bar for cache lookup
        with tqdm(total=len(characters), desc="Checking cache", disable=len(characters) < 5) as pbar:
            for char in characters:
                cached_data = get_cached_character(char)
                if cached_data:
                    character_data[char] = cached_data
                pbar.update(1)
    
    # Determine which characters we need to fetch from Gemini
    missing_chars = [char for char in characters if char not in character_data]
    
    # If all characters are in cache, return early
    if not missing_chars:
        click.echo("All characters found in cache.")
        return character_data
    
    click.echo(f"Fetching data for {len(missing_chars)} characters not in cache...")
    
    try:
        import google.generativeai as genai
    except ImportError:
        click.echo("Google Generative AI library not found. Install with 'pip install google-generativeai'")
        # Generate placeholder data for missing characters
        for char in missing_chars:
            placeholder = generate_placeholder_data(char)
            character_data[char] = placeholder
            if use_cache:
                cache_character(char, placeholder, source="placeholder")
        return character_data

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        click.echo("[ERROR] GEMINI_API_KEY not found in environment variables. Using placeholder data.")
        # Generate placeholder data for missing characters
        for char in missing_chars:
            placeholder = generate_placeholder_data(char)
            character_data[char] = placeholder
            if use_cache:
                cache_character(char, placeholder, source="placeholder")
        return character_data

    # Configure the Google Generative AI library with your API key
    genai.configure(api_key=api_key)

    # Use the correct model
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
                click.echo(f"Using Gemini model: {model_name}")
                break
            except Exception as model_error:
                click.echo(f"Could not use model {model_name}: {model_error}")
                continue

        if model is None:
            raise Exception("No Gemini models are available")

    except Exception as e:
        click.echo(f"Error initializing Gemini model: {e}")
        # Generate placeholder data for missing characters
        for char in missing_chars:
            placeholder = generate_placeholder_data(char)
            character_data[char] = placeholder
            if use_cache:
                cache_character(char, placeholder, source="placeholder")
        return character_data

    # Generation config for better output
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    # APPROACH 1: Try to get all characters at once first for efficiency
    if len(missing_chars) > 1:
        try:
            click.echo(f"Attempting to get data for all {len(missing_chars)} characters at once...")

            chars_str = ', '.join([f"'{char}'" for char in missing_chars])
            batch_prompt = f"""
            Generate information about these Chinese characters: {chars_str}

            For each character, provide:
            - pinyin: the pronunciation with tone marks
            - meaning: main English meanings
            - composition: character component explanation
            - phrases: 5 common phrases with pinyin and meaning

            Format each character's information like this:

            Character: [character]
            pinyin: [pronunciation]
            meaning: [meanings]
            composition: [explanation]
            phrases: [phrase1]<br>[phrase2]<br>[phrase3]<br>[phrase4]<br>[phrase5]

            Start each character with "Character:" on a new line.
            Do not include any other formatting, explanations, or markdown.
            """

            response = model.generate_content(
                batch_prompt,
                generation_config=generation_config
            )

            response_text = response.text

            # Save response for debugging
            if debug_flag:
                log_header = f"\n\nGemini Model: {model_name}\nDatetime: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                # Save the raw response for debugging
                file_raw = "gemini_response_batch.txt"
                with open(file_raw, "a", encoding="utf-8") as f:
                    f.write(log_header)
                    f.write(response_text)
                click.echo(f"Gemini API response saved to {file_raw}")


            # Parse the non-JSON response format
            batch_character_data = {}
            lines = response_text.split('\n')

            current_char = None
            current_data = {}
            current_field = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for new character section
                if line.startswith('Character:'):
                    # Save previous character if we were processing one
                    if current_char and current_data:
                        batch_character_data[current_char] = current_data
                        # Cache the character data
                        if use_cache:
                            cache_character(current_char, current_data, source="gemini_batch")

                    # Start new character
                    char_parts = line.split(':', 1)
                    if len(char_parts) > 1:
                        potential_char = char_parts[1].strip()
                        # Handle cases where the character might have extra text
                        for c in potential_char:
                            if c in missing_chars:
                                current_char = c
                                break
                        else:
                            # If no known character found, use the first character
                            current_char = potential_char[0] if potential_char else None

                    current_data = {}
                    current_field = None

                # Check for field definitions
                elif ':' in line and not line.startswith('Character:'):
                    field_parts = line.split(':', 1)
                    field_name = field_parts[0].strip().lower()
                    field_value = field_parts[1].strip()

                    if field_name in ['pinyin', 'meaning', 'composition', 'phrases']:
                        current_data[field_name] = field_value
                        current_field = field_name

                # Continuation of previous field
                elif current_field:
                    current_data[current_field] += ' ' + line

            # Add the last character
            if current_char and current_data:
                batch_character_data[current_char] = current_data
                # Cache the character data
                if use_cache:
                    cache_character(current_char, current_data, source="gemini_batch")

            # Update our main character_data dictionary
            character_data.update(batch_character_data)

            # Check if we got data for all characters
            still_missing_chars = [char for char in missing_chars if char not in character_data]

            if not still_missing_chars:
                click.echo(f"Successfully retrieved data for all {len(missing_chars)} characters in batch mode")
                return character_data
            else:
                click.echo(f"Batch retrieval missing data for {len(still_missing_chars)} characters. Filling in...")
                # Continue to one-by-one approach for missing characters
                missing_chars = still_missing_chars

        except Exception as batch_error:
            click.echo(f"Batch retrieval failed: {batch_error}")
            # Continue with individual processing

    # APPROACH 2: Process remaining characters one by one
    if missing_chars:
        click.echo(f"Retrieving data for {len(missing_chars)} characters individually...")
        
        # Create a progress bar for individual character processing
        with tqdm(total=len(missing_chars), desc="Processing characters", disable=len(missing_chars) < 3) as pbar:
            for char in missing_chars:
                try:
                    # Prompt for a single character
                    prompt = f"""
                    Provide information about the Chinese character '{char}' in this EXACT format:

                    pinyin: [pronunciation with tone marks]
                    meaning: [main English meanings]
                    composition: [explanation of character components]
                    phrases: [five common phrases with pinyin and English translation separated by <br>]

                    ONLY return the format above with no other text.
                    """

                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )

                    response_text = response.text.strip()

                    # Simple line-by-line parsing
                    char_data = {}
                    current_field = None

                    for line in response_text.split('\n'):
                        line = line.strip()
                        if not line:
                            continue

                        if ':' in line:
                            parts = line.split(':', 1)
                            field_name = parts[0].strip().lower()
                            field_value = parts[1].strip()

                            if field_name in ['pinyin', 'meaning', 'composition', 'phrases']:
                                char_data[field_name] = field_value
                                current_field = field_name
                        else:
                            # Continuation of previous field
                            if current_field:
                                char_data[current_field] += ' ' + line

                    # Check if we got all the fields
                    if all(field in char_data for field in ['pinyin', 'meaning', 'composition', 'phrases']):
                        character_data[char] = char_data
                        # Cache the character data
                        if use_cache:
                            cache_character(char, char_data, source="gemini_individual")
                    else:
                        click.echo(f"Missing some fields for character {char}. Using placeholder data.")
                        placeholder = generate_placeholder_data(char)
                        character_data[char] = placeholder
                        if use_cache:
                            cache_character(char, placeholder, source="placeholder")

                except Exception as e:
                    click.echo(f"Error generating data for character {char}: {e}")
                    placeholder = generate_placeholder_data(char)
                    character_data[char] = placeholder
                    if use_cache:
                        cache_character(char, placeholder, source="placeholder")
                
                # Update progress bar
                pbar.update(1)

    # Ensure we have data for all requested characters
    for char in characters:
        if char not in character_data:
            placeholder = generate_placeholder_data(char)
            character_data[char] = placeholder
            if use_cache:
                cache_character(char, placeholder, source="placeholder")

    return character_data


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

def generate_html(tree_data, character_data, title="ZiNets Visualization"):
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
        .footer {{
            margin-top: 20px;
            font-size: 12px;
            color: #666;
            text-align: center;
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
        
        <div class="footer">
            Generated by ZiNets on {generation_date}
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

    # Get current date for footer
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Replace placeholders in HTML template
    html = html_template.format(
        title=title,
        root_character=root_character,
        root_pinyin=root_data['pinyin'],
        root_meaning=root_data['meaning'],
        root_composition=root_data['composition'],
        root_phrases=root_data['phrases'],
        character_data_json=json.dumps(character_data, ensure_ascii=False, indent=4),
        tree_data_json=json.dumps(tree_data, ensure_ascii=False, indent=4),
        generation_date=generation_date
    )

    return html

def process_semantic_network(markdown_text, output_file="zi_vis.html", use_gemini=True, use_cache=True, title="ZiNets Visualization", debug=False):
    """
    Process semantic network data and generate HTML file.

    Args:
        markdown_text: The semantic network data in markdown format
        output_file: Output HTML file path
        use_gemini: Whether to use Gemini API for character data
        use_cache: Whether to use character data caching
        title: Title for the visualization page
        debug: Whether to enable debug mode
    """
    # Parse markdown to tree data
    tree_data = parse_markdown_to_tree_data(markdown_text)

    # Extract all characters from the tree
    characters = extract_all_characters(tree_data)
    
    click.echo(f"Found {len(characters)} unique characters in the semantic network.")

    # Get character data from Gemini API or generate placeholder data
    character_data = get_character_data_from_gemini(
        characters, 
        debug_flag=debug, 
        use_cache=use_cache
    ) if use_gemini else {
        char: generate_placeholder_data(char) for char in characters
    }

    # Generate HTML with embedded JavaScript objects
    with tqdm(total=1, desc="Generating HTML", disable=False) as pbar:
        html = generate_html(tree_data, character_data, title=title)
        pbar.update(1)

    # Write to file
    with tqdm(total=1, desc="Writing output file", disable=False) as pbar:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        pbar.update(1)

    click.echo(click.style(f"HTML file generated successfully: {output_file}", fg='green'))
    return output_file

@click.command()
@click.option('--input-file', '-i', type=click.Path(exists=True, readable=True), 
              help='Input markdown file with zi_network data')
@click.option('--output-file', '-o', default='zi_vis.html', 
              help='Output HTML file path (default: zi_vis.html)')
@click.option('--title', '-t', default='ZiNets Visualization',
              help='Title for the visualization page')
@click.option('--use-gemini/--no-gemini', default=True,
              help='Whether to use Gemini API for character data (default: True)')
@click.option('--use-cache/--no-cache', default=True,
              help='Whether to use SQLite cache for character data (default: True)')
@click.option('--debug/--no-debug', default=False,
              help='Enable debug mode to save API responses (default: False)')
@click.option('--cache-stats', is_flag=True, default=False,
              help='Display cache statistics and exit')
def main(input_file, output_file, title, use_gemini, use_cache, debug, cache_stats):
    """
    ZiNets - Chinese Character Network Visualization Tool
    
    This tool takes semantic network data for Chinese characters and generates an
    interactive visualization that displays character relationships and information.
    
    If no input file is provided, it will use a default network for demonstration.
    """
    # Show cache stats if requested
    if cache_stats:
        show_cache_statistics()
        return

    # Get markdown text from file or use default
    if input_file:
        click.echo(f"Reading from file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    else:
        click.echo("No input file provided. Using default network.")
        markdown_text = DEFAULT_NETWORK
    
    # Process the network and generate visualization
    try:
        output_path = process_semantic_network(
            markdown_text, 
            output_file=output_file, 
            use_gemini=use_gemini,
            use_cache=use_cache,
            title=title,
            debug=debug
        )
        click.echo(click.style(f"Success! Visualization saved to: {output_path}", fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        raise click.Abort()

def show_cache_statistics():
    """
    Display statistics about the character cache.
    """
    if not os.path.exists(CACHE_DB):
        click.echo("Cache database does not exist. No statistics available.")
        return
    
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    
    # Get total count
    c.execute("SELECT COUNT(*) FROM character_cache")
    total_count = c.fetchone()[0]
    
    # Get source distribution
    c.execute("SELECT source, COUNT(*) FROM character_cache GROUP BY source")
    source_counts = c.fetchall()
    
    # Get recent entries
    c.execute("SELECT character, timestamp FROM character_cache ORDER BY timestamp DESC LIMIT 5")
    recent_entries = c.fetchall()
    
    conn.close()
    
    # Display statistics
    click.echo("\n=== ZiNets Character Cache Statistics ===")
    click.echo(f"Total characters in cache: {total_count}")
    
    if source_counts:
        click.echo("\nSource distribution:")
        for source, count in source_counts:
            click.echo(f"  - {source}: {count} characters ({count/total_count*100:.1f}%)")
    
    if recent_entries:
        click.echo("\nMost recent cache entries:")
        for char, timestamp in recent_entries:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            click.echo(f"  - '{char}' cached at {formatted_time}")
    
    click.echo("\nUse the following command to use the cache:")
    click.echo(f"python {__file__} --use-cache")
    click.echo("===================================")

if __name__ == "__main__":
    main()
"""
    This script generates a visualization of Chinese characters and their meanings 
    using ECharts. It fetches data from LLM Models such as Google Gemini API and 
    caches it in a SQLite database.

Usages:
1. To visualize default network:
    $ python zinets_vis.py

2. To visualize a specific character network:
    $ python zinets_vis.py -i in_water.md [-o vis_water.html]
    $ python zinets_vis.py -i in_mind.md
    $ python zinets_vis.py -i in_moss.md 
    $ python zinets_vis.py -i in_wood.md 

3. To visualize a specific character network with custom language:
    $ python zinets_vis.py --no-cache -i in_mind.md -l Spanish
    $ python zinets_vis.py --no-cache -i in_mind.md -l Korean
    $ python zinets_vis.py --no-cache -i in_mind.md -l Latin
    $ python zinets_vis.py --no-cache -i in_mind.md -l Arabic

4. show cache statistics:
    $ python zinets_vis.py --cache-stats

"""

import json
import os
import re
import time
import click
import sqlite3
from datetime import datetime
from tqdm import tqdm

DEBUG_FLAG = True

DEFAULT_OUTPUT_HTML = "vis_zi.html"

DEFAULT_NETWORK = """藻
        - 艹
        - 澡(氵+喿)
            - 氵
            - 喿(品+木)
                - 品(口+口+口)
                        - 口 
                        - 口 
                        - 口 
                - 木"""


BASE_PROMPT = """ 
    For each character, provide the following information in this format:
    - pinyin: the pronunciation with tone marks
    - meaning: main meanings
    - composition: how character is structurally composed from radicals and parts
    - phrases: 5 common phrases with pinyin and meaning

    Ensure explanation texts are in the target language of '{language}'

    Format character's information like this:

    Character: [character]
    pinyin: [pronunciation]
    meaning: [meanings]
    composition: [explanation]
    phrases: [phrase1]<br>[phrase2]<br>[phrase3]<br>[phrase4]<br>[phrase5]

    Start each character with "Character:" on a new line.
    Do not include any other formatting, explanations, or markdown.
"""
# Database configuration
CACHE_DB = "zinets_cache.sqlite"

def derive_output_filename(input_filename, language="English"):
    # Split the input filename into its root and extension
    root, _ = os.path.splitext(input_filename)
    root = root.lower()
    
    # Check if the input file follows the expected "in_<tag>" pattern
    if root.startswith("in_"):
        # Extract the <tag> part by removing the "in_" prefix
        tag = root[3:]
        
        # Construct the output filename with the "vis_<tag>.html" format
        output_filename = f"vis_{tag}-{language.lower()}.html"
        return output_filename
    
    else:
        raise ValueError("Input filename does not follow the 'in_<tag>.md' format.")

def setup_cache_db():
    """
    Set up the SQLite cache database if it doesn't exist.
    """
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    
    # Check if table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='character_cache'")
    table_exists = c.fetchone()
    
    if not table_exists:
        # Create new table with the updated schema
        c.execute('''
        CREATE TABLE IF NOT EXISTS character_cache (
            character TEXT,
            pinyin TEXT,
            meaning TEXT,
            composition TEXT,
            phrases TEXT,
            llm_provider TEXT,
            llm_model_name TEXT,
            timestamp TEXT,
            is_active TEXT DEFAULT 'Y',
            is_best TEXT DEFAULT 'Y',
            PRIMARY KEY (character, llm_provider, llm_model_name)
        )
        ''')
    else:
        # Check if we need to migrate from old schema to new schema
        try:
            # Check if the column exists
            c.execute("PRAGMA table_info(character_cache)")
            columns = [info[1] for info in c.fetchall()]
            
            if 'source' in columns and 'llm_provider' not in columns:
                # Need to migrate: create a new table, copy data, drop old table, rename new table
                click.echo("Migrating database schema...")
                
                # Create new table
                c.execute('''
                CREATE TABLE character_cache_new (
                    character TEXT,
                    pinyin TEXT,
                    meaning TEXT,
                    composition TEXT,
                    phrases TEXT,
                    llm_provider TEXT,
                    llm_model_name TEXT,
                    timestamp TEXT,
                    is_active TEXT DEFAULT 'Y',
                    is_best TEXT DEFAULT 'Y',
                    PRIMARY KEY (character, llm_provider, llm_model_name)
                )
                ''')
                
                # Copy data (migrating the 'source' field to 'llm_provider' and 'llm_model_name')
                c.execute('''
                INSERT INTO character_cache_new 
                (character, pinyin, meaning, composition, phrases, llm_provider, llm_model_name, timestamp, is_active, is_best)
                SELECT 
                    character, 
                    pinyin, 
                    meaning, 
                    composition, 
                    phrases, 
                    CASE 
                        WHEN source LIKE 'gemini%' THEN 'Google' 
                        ELSE 'Unknown' 
                    END as llm_provider,
                    CASE 
                        WHEN source LIKE '%batch' THEN 'gemini-batch' 
                        WHEN source LIKE '%individual' THEN 'gemini-individual'
                        ELSE 'unknown'
                    END as llm_model_name,
                    timestamp,
                    'Y',
                    'Y'
                FROM character_cache
                ''')
                
                # Drop old table
                c.execute("DROP TABLE character_cache")
                
                # Rename new table
                c.execute("ALTER TABLE character_cache_new RENAME TO character_cache")
                
                click.echo("Database migration completed.")
        except Exception as e:
            click.echo(f"Error migrating database: {e}")
    
    conn.commit()
    conn.close()
    
def get_cached_character(character):
    """
    Get character data from cache if available.
    Only returns active records marked as best.
    
    Args:
        character: The Chinese character to look up
        
    Returns:
        Dict with character data or None if not in cache
    """
    # Check if cache exists, create if not
    if not os.path.exists(CACHE_DB):
        setup_cache_db()
        return None  # Cache was just created, so no data exists yet

    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    
    c.execute("""
    SELECT pinyin, meaning, composition, phrases 
    FROM character_cache 
    WHERE character = ? AND is_active = 'Y' AND is_best = 'Y'
    ORDER BY timestamp DESC
    LIMIT 1
    """, (character,))
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

def cache_character(character, data, llm_provider="Google", llm_model_name="gemini"):
    """
    Save character data to cache.
    Skip caching if the data is placeholder data.
    
    Args:
        character: The Chinese character
        data: Dict containing character data
        llm_provider: Provider of the LLM (e.g., "Google", "Anthropic", etc.)
        llm_model_name: Name of the LLM model used
    """
    # Don't cache placeholder data
    if data['pinyin'] == 'Unknown' and data['meaning'] == 'Meaning not available':
        return
        
    # Check if cache exists, create if not
    if not os.path.exists(CACHE_DB):
        setup_cache_db()

    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    # Check if this character already has any records marked as 'best'
    c.execute("""
    SELECT COUNT(*) FROM character_cache 
    WHERE character = ? AND is_best = 'Y'
    """, (character,))
    has_best = c.fetchone()[0] > 0
    
    # New records are marked as best only if no existing best record exists
    is_best = 'Y' if not has_best else 'N'
    
    c.execute('''
    INSERT OR REPLACE INTO character_cache 
    (character, pinyin, meaning, composition, phrases, llm_provider, llm_model_name, timestamp, is_active, is_best)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Y', ?)
    ''', (
        character, 
        data['pinyin'], 
        data['meaning'], 
        data['composition'], 
        data['phrases'], 
        llm_provider,
        llm_model_name,
        timestamp,
        is_best
    ))
    
    conn.commit()
    conn.close()

def parse_markdown_to_tree_data(markdown_text):
    """
    Parse semantic network data in markdown format into a tree data structure.
    More robust indentation detection to handle files from different editors.
    Handles comments properly - anything after # is considered a comment and ignored.
    Fixes hierarchy nesting for proper parent-child relationships.

    Notes:
        when working with data from zinets database,
        use `convert_d3graph_to_tree()` from `zinets/app/zadmin/pages/4-字形 Zi Structure.py`
    """
    lines = markdown_text.strip().split('\n')
    if not lines:
        return {"name": "", "children": []}
    
    # Get the root name, ignoring anything after # if present
    root_line = lines[0]
    if '#' in root_line:
        # If there's a comment, extract the content before #
        root_name = root_line.split('#', 1)[0].strip()
    else:
        root_name = root_line.strip()

    # Initialize the root node
    tree_data = {
        'name': root_name,
        'children': []
    }

    # First pass: Analyze indentation patterns in the file
    line_indentations = []  # Store actual indentation for each line
    indent_levels = []      # Store logical level for each line
    
    for i in range(1, len(lines)):
        original_line = lines[i]
        
        # Remove comments - anything after # is ignored
        if '#' in original_line:
            line_without_comment = original_line.split('#', 1)[0]
        else:
            line_without_comment = original_line
            
        line = line_without_comment.strip()
        if not line:
            # Skip empty lines
            line_indentations.append(None)
            indent_levels.append(None)
            continue
            
        # Only process lines that start with dash
        if not line_without_comment.lstrip(' \t').startswith('-'):
            # Skip non-dash lines
            line_indentations.append(None)
            indent_levels.append(None)
            continue
        
        # Measure actual indentation
        leading_spaces = len(line_without_comment) - len(line_without_comment.lstrip(' '))
        leading_tabs = len(line_without_comment) - len(line_without_comment.lstrip('\t'))
        
        # Store raw indentation (we'll convert to logical levels later)
        if leading_tabs > 0:
            # Tab-based
            line_indentations.append(('tab', leading_tabs))
        else:
            # Space-based
            line_indentations.append(('space', leading_spaces))
    
    # Determine indentation pattern from collected data
    tab_counts = {}
    space_counts = {}
    space_sequences = []
    
    for indent in line_indentations:
        if indent is None:
            continue
            
        indent_type, indent_size = indent
        
        if indent_type == 'tab':
            tab_counts[indent_size] = tab_counts.get(indent_size, 0) + 1
        else:
            space_counts[indent_size] = space_counts.get(indent_size, 0) + 1
            if indent_size > 0:
                space_sequences.append(indent_size)
    
    # Determine if we're using tabs or spaces
    using_tabs = sum(tab_counts.values()) > sum(space_counts.values())
    
    # Convert raw indentations to logical levels
    if using_tabs:
        # Tab-based: each tab is one level
        for i, indent in enumerate(line_indentations):
            if indent is None:
                indent_levels.append(None)
            else:
                indent_type, indent_size = indent
                if indent_type == 'tab':
                    indent_levels.append(indent_size)
                else:
                    # Convert spaces to equivalent tabs (assuming 4 spaces = 1 tab)
                    indent_levels.append(indent_size // 4)
    else:
        # Space-based: determine common increment
        space_diffs = []
        sorted_spaces = sorted(list(set(space_sequences)))
        
        if len(sorted_spaces) > 1:
            for i in range(1, len(sorted_spaces)):
                diff = sorted_spaces[i] - sorted_spaces[i-1]
                if diff > 0:
                    space_diffs.append(diff)
        
        # Determine the common indentation unit
        if space_diffs:
            # Use the most common difference
            from collections import Counter
            common_diff = Counter(space_diffs).most_common(1)[0][0]
        else:
            # Default to 2 or 4 spaces based on what appears most
            space_2_count = space_counts.get(2, 0) + space_counts.get(4, 0) + space_counts.get(6, 0) + space_counts.get(8, 0)
            space_4_count = space_counts.get(4, 0) + space_counts.get(8, 0) + space_counts.get(12, 0)
            common_diff = 2 if space_2_count > space_4_count else 4
        
        # Convert spaces to logical levels
        base_indent = min(space_sequences) if space_sequences else common_diff
        
        for i, indent in enumerate(line_indentations):
            if indent is None:
                indent_levels.append(None)
            else:
                indent_type, indent_size = indent
                if indent_type == 'space':
                    # Round to nearest level (to handle inconsistent indentation)
                    indent_levels.append(round(indent_size / common_diff))
                else:
                    # Convert tabs to spaces
                    indent_levels.append(indent_size * (4 // common_diff))
    
    # Second pass: build the tree using determined indent levels
    stack = [(0, tree_data)]  # (level, node)
    
    for i in range(1, len(lines)):
        level = indent_levels[i-1]  # -1 because we started storing from lines[1]
        
        if level is None:
            continue
            
        original_line = lines[i]
        
        # Remove comments
        if '#' in original_line:
            line_without_comment = original_line.split('#', 1)[0]
        else:
            line_without_comment = original_line
            
        line = line_without_comment.strip()
        
        # Extract character name and decomposition
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
            # 'symbolSize': 25,
            'children': []
        }
        
        if decomposition:
            new_node['decomposition'] = decomposition
            
        # Find appropriate parent
        while stack and stack[-1][0] >= level:
            stack.pop()
            
        # Ensure stack is never empty
        if not stack:
            stack = [(0, tree_data)]
            
        # Add node to parent
        parent = stack[-1][1]
        parent['children'].append(new_node)
        
        # Add to stack
        stack.append((level, new_node))
        
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

def get_character_data_from_gemini(characters, debug=DEBUG_FLAG, use_cache=True, chunk_size=10, language='English'):
    """
    Use Google Gemini API to generate character data using the official Python library.
    With caching support to reduce API calls.
    
    Args:
        characters: A list of Chinese characters
        debug: Whether to save debug information
        use_cache: Whether to use cached data
        chunk_size: Maximum number of characters to process in a single batch

    Returns:
        A dictionary with character data
    """
    # Set up cache database if using cache
    if use_cache:
        if not os.path.exists(CACHE_DB):
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
    
    if cached_chars := len(character_data):
        click.echo(f"Found {cached_chars} characters in cache: {list(character_data.keys())} ! ")

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
            character_data[char] = generate_placeholder_data(char)
            # Note: We don't cache placeholder data anymore
        return character_data

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        click.echo("[ERROR] GEMINI_API_KEY not found in environment variables. Using placeholder data.")
        # Generate placeholder data for missing characters
        for char in missing_chars:
            character_data[char] = generate_placeholder_data(char)
            # Note: We don't cache placeholder data anymore
        return character_data

    # Configure the Google Generative AI library with your API key
    genai.configure(api_key=api_key)

    # Use the correct model
    try:
        # Try to use the best available model, falling back to others if needed
        models_to_try = [
            "gemini-2.0-flash",
            'gemini-1.5-flash', 
            # "gemini-2.0-flash-lite",
            # 'gemini-1.5-pro', 
        ]

        model = None
        model_name = None
        for name in models_to_try:
            try:
                model = genai.GenerativeModel(name)
                model_name = name
                click.echo(f"Using Gemini model: {model_name}")
                break
            except Exception as model_error:
                click.echo(f"Could not use model {name}: {model_error}")
                continue

        if model is None:
            raise Exception("No Gemini models are available")

    except Exception as e:
        click.echo(f"Error initializing Gemini model: {e}")
        # Generate placeholder data for missing characters
        for char in missing_chars:
            character_data[char] = generate_placeholder_data(char)
            # Note: We don't cache placeholder data anymore
        return character_data

    # Generation config for better output
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    base_prompt = BASE_PROMPT.format(language=language)
    file_raw = "gemini_response_batch.txt"

    # APPROACH 1: Process characters in chunks for better rate limit handling
    # Initialize a list to track characters that need individual processing
    still_missing_chars = missing_chars.copy()
    
    if missing_chars:
        # Create chunks of characters to process in batches
        char_chunks = [missing_chars[i:i + chunk_size] for i in range(0, len(missing_chars), chunk_size)]
        
        click.echo(f"Processing {len(missing_chars)} characters in {len(char_chunks)} chunks of max size {chunk_size}")
        
        # Process each chunk
        for chunk_index, char_chunk in enumerate(char_chunks):
            try:
                if len(char_chunk) > 1:
                    click.echo(f"Processing chunk {chunk_index+1}/{len(char_chunks)} with {len(char_chunk)} characters...")
                    
                    chars_str = ', '.join([f"'{char}'" for char in char_chunk])

                    batch_prompt = f"""
                    Generate information about these Chinese characters: {chars_str}

                    {base_prompt}

                    """

                    response = model.generate_content(
                        batch_prompt,
                        generation_config=generation_config
                    )

                    response_text = response.text

                    # Save response for debugging
                    if debug:
                        LINE_MARKER = "===" * 80
                        log_header = f"\n\nAI Model: {model_name}\nChunk: {chunk_index+1}/{len(char_chunks)}\nDatetime: {time.strftime('%Y-%m-%d %H:%M:%S')}\n{LINE_MARKER}\n"
                        # Save the raw response for debugging
                        with open(file_raw, "a", encoding="utf-8") as f:
                            f.write(log_header)
                            f.write(batch_prompt)
                            f.write(response_text)
                        click.echo(f"API response saved to {file_raw}")

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
                                if all(field in current_data for field in ['pinyin', 'meaning', 'composition', 'phrases']):
                                    batch_character_data[current_char] = current_data
                                    # Cache the character data
                                    if use_cache and current_data['pinyin'] != 'Unknown':
                                        cache_character(current_char, current_data, llm_provider="Google", llm_model_name=model_name)
                                    
                                    # Remove from still_missing_chars since we successfully processed it
                                    # (This handles all characters except the last one in the response)
                                    if current_char in still_missing_chars:
                                        still_missing_chars.remove(current_char)

                            # Start new character
                            char_parts = line.split(':', 1)
                            if len(char_parts) > 1:
                                potential_char = char_parts[1].strip()
                                # Handle cases where the character might have extra text
                                for c in potential_char:
                                    if c in char_chunk:
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
                        if all(field in current_data for field in ['pinyin', 'meaning', 'composition', 'phrases']):
                            batch_character_data[current_char] = current_data
                            # Cache the character data
                            if use_cache and current_data['pinyin'] != 'Unknown':
                                cache_character(current_char, current_data, llm_provider="Google", llm_model_name=model_name)
                            
                            # Handle the last character in the response (which won't be caught by the Character: line check)
                            if current_char in still_missing_chars:
                                still_missing_chars.remove(current_char)

                    # Update our main character_data dictionary
                    character_data.update(batch_character_data)

                    # Report on processing success
                    processed_chars = list(batch_character_data.keys())
                    if len(processed_chars) == len(char_chunk):
                        click.echo(f"Successfully processed all {len(char_chunk)} characters in chunk {chunk_index+1}")
                    else:
                        missing_count = len(char_chunk) - len(processed_chars)
                        click.echo(f"Chunk {chunk_index+1} processing: got {len(processed_chars)}/{len(char_chunk)} characters. {missing_count} will be processed individually later.")
                
                # Add a small delay between chunks to avoid rate limiting
                if chunk_index < len(char_chunks) - 1:
                    delay_time = 1.0  # 1 second delay between chunks
                    click.echo(f"Waiting {delay_time}s before next chunk to avoid rate limits...")
                    time.sleep(delay_time)
                    
            except Exception as chunk_error:
                click.echo(f"Error processing chunk {chunk_index+1}: {chunk_error}")
                # Characters in this chunk will remain in still_missing_chars for individual processing
    
    # APPROACH 2: Process any remaining characters one by one
    # We're using the still_missing_chars list that was updated during chunk processing
    
    if still_missing_chars:
        click.echo(f"Retrieving data for {len(still_missing_chars)} remaining characters individually...")
        
        # Create a progress bar for individual character processing
        with tqdm(total=len(still_missing_chars), desc="Processing characters individually", disable=len(still_missing_chars) < 3) as pbar:
            for char in still_missing_chars:
                try:
                    # Prompt for a single character
                    prompt = f"""
                    Generate information about this Chinese character '{char}' in this EXACT format:

                    {base_prompt}

                    """

                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config
                    )

                    response_text = response.text.strip()

                    # Save response for debugging
                    if debug:
                        LINE_MARKER = "===" * 80
                        log_header = f"\n\nAI Model: {model_name}\nDatetime: {time.strftime('%Y-%m-%d %H:%M:%S')}\n{LINE_MARKER}\n"
                        # Save the raw response for debugging
                        with open(file_raw, "a", encoding="utf-8") as f:
                            f.write(log_header)
                            f.write(batch_prompt)
                            f.write(response_text)
                        click.echo(f"API response saved to {file_raw}")


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
                        # Cache the character data only if it's not placeholder data
                        if use_cache and char_data['pinyin'] != 'Unknown':
                            cache_character(char, char_data, llm_provider="Google", llm_model_name=model_name)
                    else:
                        click.echo(f"Missing some fields for character {char}. Using placeholder data.")
                        character_data[char] = generate_placeholder_data(char)
                        # Note: We don't cache placeholder data anymore

                except Exception as e:
                    click.echo(f"Error generating data for character {char}: {e}")
                    character_data[char] = generate_placeholder_data(char)
                    # Note: We don't cache placeholder data anymore
                
                # Update progress bar
                pbar.update(1)
                
                # Add a small delay between individual API calls
                if char != still_missing_chars[-1]:  # Skip delay after the last character
                    time.sleep(0.5)  # 0.5 second delay between individual characters
    else:
        click.echo("All characters were successfully processed in batch mode. No need for individual processing.")

    # Ensure we have data for all requested characters
    missing_final = [char for char in characters if char not in character_data]
    if missing_final:
        click.echo(f"Adding placeholder data for {len(missing_final)} characters that couldn't be processed.")
        for char in missing_final:
            character_data[char] = generate_placeholder_data(char)
            # Note: We don't cache placeholder data

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
        <br><br>
        <div class="footer">
            Provided by ZiNets on {generation_date}
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
                borderWidth: 0,
                padding: 2,
                textStyle: {{
                    color: '#333',
                    fontSize: 25
                }}
            }},
            series: [
                {{
                    type: 'tree',
                    data: [treeData],
                    symbolSize: 40,
                    orient: 'TB',
                    symbol: 'rect',
                    label: {{
                        "show": true,
                        "color": "red",
                        "fontSize": 25,
                        "valueAnimation": false
                    }},
                    leaves: {{
                    }},
                    emphasis: {{
                        focus: 'relative',
                        itemStyle: {{
                            shadowBlur: 40,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(10, 10, 10, 0.75)'
                        }}
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

def process_semantic_network(markdown_text, output_file=DEFAULT_OUTPUT_HTML, use_gemini=True, use_cache=True, 
                      title="ZiNets Visualization", debug=DEBUG_FLAG, chunk_size=10, language="English"):
    """
    Process semantic network data and generate HTML file.

    Args:
        markdown_text: The semantic network data in markdown format
        output_file: Output HTML file path
        use_gemini: Whether to use Gemini API for character data
        use_cache: Whether to use character data caching
        title: Title for the visualization page
        debug: Whether to enable debug mode
        chunk_size: Maximum number of characters to process in a single batch
        language: Language for the output (default: English)
    """
    # Parse markdown to tree data
    tree_data = parse_markdown_to_tree_data(markdown_text)
    if debug and tree_data:
        # Save the parsed tree data for debugging
        file_tree = "parsed_tree_data.json"
        with open(file_tree, "w", encoding="utf-8") as f:
            json.dump(tree_data, f, ensure_ascii=False, indent=4)
        click.echo(f"Parsed tree data saved to {file_tree}")

    # Extract all characters from the tree
    characters = extract_all_characters(tree_data)
    
    click.echo(f"Found {len(characters)} unique characters in the semantic network.")

    # Get character data from Gemini API or generate placeholder data
    if use_gemini:
        ts_start = time.time()
        character_data = get_character_data_from_gemini(
            characters, 
            debug=debug, 
            use_cache=use_cache,
            chunk_size=chunk_size,
            language=language
        )
        ts_end = time.time()
        click.echo(f"Gemini API call took {ts_end - ts_start:.2f} seconds.")
    else:
        # When not using Gemini, we still use cache if enabled
        if use_cache:
            character_data = {}
            # Check cache first 
            with tqdm(total=len(characters), desc="Checking cache", disable=len(characters) < 5) as pbar:
                for char in characters:
                    cached_data = get_cached_character(char)
                    if cached_data:
                        character_data[char] = cached_data
                    else:
                        character_data[char] = generate_placeholder_data(char)
                    pbar.update(1)
        else:
            character_data = {char: generate_placeholder_data(char) for char in characters}
    

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
@click.option('--output-file', '-o', default=DEFAULT_OUTPUT_HTML, 
              help=f'Output HTML file path (default: {DEFAULT_OUTPUT_HTML})')
@click.option('--title', '-t', default='ZiNets Visualization',
              help='Title for the visualization page')
@click.option('--use-gemini/--no-gemini', default=True,
              help='Whether to use Gemini API for character data (default: True)')
@click.option('--use-cache/--no-cache', default=True,
              help='Whether to use SQLite cache for character data (default: True)')
@click.option('--debug/--no-debug', default=True,
              help='Enable debug mode to save API responses (default: False)')
@click.option('--cache-stats', is_flag=True, default=False,
              help='Display cache statistics and exit')
@click.option('--chunk-size', default=10, type=int,
              help='Maximum number of characters to process in a single batch (default: 10)')
@click.option('--language', '-l', default='English',
              help='Language for the output (default: English)')
def main(input_file, output_file, title, use_gemini, use_cache, debug, cache_stats, chunk_size, language):
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

        if not output_file or output_file == DEFAULT_OUTPUT_HTML:
            output_file = derive_output_filename(input_file, language)
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
            debug=debug,
            chunk_size=chunk_size,
            language=language
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
    
    try:
        # Check if we have the new schema or old schema
        c.execute("PRAGMA table_info(character_cache)")
        columns = [info[1] for info in c.fetchall()]
        
        has_new_schema = 'llm_provider' in columns
        
        # Get total count of active records
        if has_new_schema:
            c.execute("SELECT COUNT(*) FROM character_cache WHERE is_active = 'Y'")
        else:
            c.execute("SELECT COUNT(*) FROM character_cache")
        total_count = c.fetchone()[0]
        
        # Get count of records marked as "best"
        if has_new_schema:
            c.execute("SELECT COUNT(*) FROM character_cache WHERE is_active = 'Y' AND is_best = 'Y'")
            best_count = c.fetchone()[0]
        else:
            best_count = total_count  # In old schema, all records are considered "best"
        
        # Get provider distribution
        if has_new_schema:
            c.execute("SELECT llm_provider, COUNT(*) FROM character_cache WHERE is_active = 'Y' GROUP BY llm_provider")
            provider_counts = c.fetchall()
        else:
            c.execute("SELECT source, COUNT(*) FROM character_cache GROUP BY source")
            provider_counts = c.fetchall()
        
        # Get model distribution
        if has_new_schema:
            c.execute("SELECT llm_model_name, COUNT(*) FROM character_cache WHERE is_active = 'Y' GROUP BY llm_model_name")
            model_counts = c.fetchall()
        else:
            model_counts = []  # Not available in old schema
        
        # Get recent entries
        if has_new_schema:
            c.execute("""
                SELECT character, llm_provider, llm_model_name, timestamp 
                FROM character_cache 
                WHERE is_active = 'Y'
                ORDER BY timestamp DESC LIMIT 5
            """)
        else:
            c.execute("SELECT character, source, timestamp FROM character_cache ORDER BY timestamp DESC LIMIT 5")
        recent_entries = c.fetchall()
        
    except Exception as e:
        click.echo(f"Error getting cache statistics: {e}")
        conn.close()
        return
    
    conn.close()
    
    # Display statistics
    click.echo("\n=== ZiNets Character Cache Statistics ===")
    click.echo(f"Total active characters in cache: {total_count}")
    click.echo(f"Characters marked as 'best': {best_count}")
    
    if provider_counts:
        click.echo("\nProvider distribution:")
        for provider, count in provider_counts:
            click.echo(f"  - {provider}: {count} characters ({count/total_count*100:.1f}%)")
    
    if model_counts:
        click.echo("\nModel distribution:")
        for model, count in model_counts:
            click.echo(f"  - {model}: {count} characters ({count/total_count*100:.1f}%)")
    
    if recent_entries:
        click.echo("\nMost recent cache entries:")
        for entry in recent_entries:
            if has_new_schema:
                char, provider, model, timestamp = entry
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                click.echo(f"  - '{char}' from {provider}/{model} cached at {formatted_time}")
            else:
                char, source, timestamp = entry
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                click.echo(f"  - '{char}' from {source} cached at {formatted_time}")
    
    click.echo("\nCache Management Commands:")
    click.echo("  - Use cache:    python zinets.py --use-cache")
    click.echo("  - Bypass cache: python zinets.py --no-cache")
    click.echo("=====================================")

if __name__ == "__main__":
    main()
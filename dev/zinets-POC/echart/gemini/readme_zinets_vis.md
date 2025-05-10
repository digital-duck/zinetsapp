# ZiNets CLI - Setup and Usage Instructions

## Installation

To use the improved ZiNets CLI with Click, follow these steps:

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:

```bash
pip install click google-generativeai tqdm
```

3. Save the script as `zinets.py`
4. Make the script executable (on Linux/Mac):

```bash
chmod +x zinets.py
```

## Environment Setup for Gemini API

If you want to use the Gemini API for character data enrichment:

1. Get an API key from Google AI Studio (https://makersuite.google.com/)
2. Set the API key as an environment variable:

```bash
# For Linux/Mac
export GEMINI_API_KEY=your_api_key_here

# For Windows (Command Prompt)
set GEMINI_API_KEY=your_api_key_here

# For Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"
```

## New Features

### Improved Character Data Caching

The tool now supports an enhanced caching system in a local SQLite database to reduce API calls and speed up repeated usage:

- By default, caching is enabled (`--use-cache`)
- Only successful LLM-generated data is cached (placeholder data is not cached)
- The cache maintains multiple versions of data for the same character (different LLM providers/models)
- Each cached record has "active" and "best" status flags for better quality control
- Table includes LLM provider and model information for future analytics and quality comparison

#### Cache Management Features
- Automatically migrates from older cache schemas
- Only returns "active" and "best" character data from cache
- Cache statistics command shows detailed information

### Progress Bars

Added visual progress bars to show:
- Cache checking progress
- Individual character processing 
- HTML generation and file writing

### Cache Statistics

You can view detailed statistics about your cache:

```bash
python zinets.py --cache-stats
```

This shows:
- Total number of active cached characters
- Number of characters marked as "best" 
- Provider and model distribution
- Most recent cache entries with provider/model information
- Usage guidance

## Usage Examples

### Basic Usage (Default Example)

```bash
python zinets.py
```

This will use the default Chinese character network and generate `zi_vis.html` in the current directory, using the cache if available.

### Using a Custom Input File

```bash
python zinets.py --input-file my_network.md --output-file custom_vis.html
```

or with the short form:

```bash
python zinets.py -i my_network.md -o custom_vis.html
```

### Setting a Custom Title

```bash
python zinets.py --title "My Chinese Character Network"
```

### Disabling Gemini API (Use Placeholder Data Only)

```bash
python zinets.py --no-gemini
```

### Disabling Cache (Always Fetch Fresh Data)

```bash
python zinets.py --no-cache
```

### Enable Debug Mode

```bash
python zinets.py --debug
```

### View Help

```bash
python zinets.py --help
```

## Input File Format

The input file should follow this Markdown-like format:

```
字 (Root character)
    - 子 (Child character - one indentation level)
        - 孙 (Grandchild - two indentation levels)
    - 女 (Another child)
        - 妈 (Child of 女)
```

- Each line starts with a dash `-` followed by the character
- Indentation defines the parent-child relationship
- You can add decomposition information in parentheses (optional)

## Example Input File

```
藻
    - 艹
    - 澡
        - 氵
        - 喿
            - 品
                    - 口 
                    - 口 
                    - 口 
            - 木
```

Save this content to a file (e.g., `example.md`) and use it with the tool:

```bash
python zinets.py -i example.md -o my_visualization.html
```


## Advanced Cache Management for ZiNets

The improved caching system in ZiNets allows for more sophisticated data management and quality control. Here are some advanced tips for working with the cache and extending its functionality.

### Understanding the Cache Structure

The cache uses an SQLite database with the following schema:

```sql
CREATE TABLE character_cache (
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
```

This structure allows for:
1. Multiple versions of data for the same character (from different providers/models)
2. Quality control through `is_active` and `is_best` flags
3. Tracking the source of each record

### Manually Managing the Cache

You can use SQLite CLI tools to directly manage the cache:

```bash
sqlite3 zinets_cache.sqlite
```

#### Useful SQLite Commands

##### View all characters in the cache:
```sql
SELECT character, llm_provider, llm_model_name, is_active, is_best FROM character_cache;
```

##### Deactivate a specific character's data:
```sql
UPDATE character_cache SET is_active = 'N' WHERE character = '日' AND llm_provider = 'Google';
```

##### Mark a specific entry as the "best" version:
```sql
-- First, unmark all existing entries for this character
UPDATE character_cache SET is_best = 'N' WHERE character = '日';
-- Then mark the chosen one as best
UPDATE character_cache SET is_best = 'Y' WHERE character = '日' AND llm_provider = 'Google' AND llm_model_name = 'gemini-2.0-flash';
```

##### Delete placeholder or low-quality data:
```sql
DELETE FROM character_cache WHERE pinyin = 'Unknown' OR meaning = 'Meaning not available';
```

### Using Multiple LLM Providers

The cache design supports adding more LLM providers beyond Gemini. You could extend the code to incorporate:

1. **Claude/Anthropic API**: 
   ```python
   def get_character_data_from_claude(characters, use_cache=True):
       # Implementation here
       # Save with cache_character(char, data, llm_provider="Anthropic", llm_model_name="claude-3-opus")
   ```

2. **Qwen/Alibaba**:
   ```python
   def get_character_data_from_qwen(characters, use_cache=True):
       # Implementation here
       # Save with cache_character(char, data, llm_provider="Alibaba", llm_model_name="qwen-1.5")
   ```

3. **Multi-provider aggregation**:
   ```python
   def get_best_character_data(characters, providers=["Google", "Anthropic", "Alibaba"]):
       # Try each provider and select the best data based on completeness, timestamp, etc.
   ```

### Quality Review Workflow

You could implement a quality review workflow:

1. Run with multiple providers:
   ```bash
   python zinets.py -i my_network.md --provider google
   python zinets.py -i my_network.md --provider claude
   python zinets.py -i my_network.md --provider qwen
   ```

2. Review and mark the best data:
   ```bash
   python zinets.py --review-cache
   ```

3. Then use the reviewed data:
   ```bash
   python zinets.py -i my_network.md --use-reviewed-only
   ```

### Creating a Backup/Export System

Add functionality to export the cache to JSON for sharing or backup:

```python
def export_cache_to_json(output_file="zinets_cache_export.json"):
    conn = sqlite3.connect(CACHE_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM character_cache WHERE is_active = 'Y'")
    rows = c.fetchall()
    
    export_data = {}
    for row in rows:
        char = row['character']
        if char not in export_data:
            export_data[char] = []
        
        export_data[char].append({
            'pinyin': row['pinyin'],
            'meaning': row['meaning'],
            'composition': row['composition'],
            'phrases': row['phrases'],
            'provider': row['llm_provider'],
            'model': row['llm_model_name'],
            'is_best': row['is_best'] == 'Y'
        })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
        
    print(f"Cache exported to {output_file}")
```

### Usage with Multiple Visualization Projects

If you're working with multiple character network projects, you might want to maintain separate caches:

```python
@click.option('--cache-db', default=CACHE_DB, 
              help='Custom cache database path (default: zinets_cache.sqlite)')
def main(input_file, output_file, title, use_gemini, use_cache, debug, cache_stats, cache_db):
    # Set global cache DB path
    global CACHE_DB
    CACHE_DB = cache_db
    # ...rest of the function
```

This would allow you to use:
```bash
python zinets.py -i project1.md --cache-db project1_cache.sqlite
python zinets.py -i project2.md --cache-db project2_cache.sqlite
```

### Performance Optimization

For large character sets, you could implement:

1. **Asynchronous processing** to fetch multiple characters in parallel
2. **Batch prioritization** to process the most important characters first
3. **Cache preheating** to proactively cache common characters

These extensions would make ZiNets even more powerful when working with large datasets or multiple LLM providers.
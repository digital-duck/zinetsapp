import os
import time
from typing import List, Dict, Any

# Assuming these are defined elsewhere
# from your_cache_module import setup_cache_db, get_cached_character, cache_character
# from your_placeholder_module import generate_placeholder_data
# import click # Assuming you're using Click for CLI output
# import tqdm # Assuming you're using tqdm for progress bars

# Example placeholder definitions if not defined:
CACHE_DB = "cache.db"
DEBUG_FLAG = False
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash" # Or another model you know works
BASE_PROMPT = """
Provide the following information in a structured format:
Character: <the character itself>
Pinyin: <pinyin with tone marks>
Meaning: <English meaning>
Composition: <breakdown into radicals/components>
Phrases: <comma-separated list of 3 common phrases using the character>

Example:
Character: 你
Pinyin: nǐ
Meaning: you
Composition: 亻 (person radical) + 尔
Phrases: 你好, 你们, 是你吗
"""

# Assuming update_gemini_models is defined as before
from typing import List

# Initial list of models to try, ordered by preference
# This list defines the *order* you want to try models, not necessarily
# what's available. We will filter this based on actual available models.
PREFERRED_MODELS_TO_TRY = [
    "gemini-2.5-pro", # Try the latest best first
    "gemini-2.5-flash", # Then the latest fast model
    "gemini-1.5-pro",   # Fallback to 1.5 Pro
    "gemini-1.5-flash", # Fallback to 1.5 Flash
    "gemini-2.0-flash", # Fallback to 2.0 Flash (if still available/different endpoint)
]

def update_gemini_models(model_name: str, preferred_models: List[str]) -> List[str]:
    """
    Updates the list of preferred models by moving the specified model_name to the
    front if found, or inserting it at the front if not found.

    Args:
        model_name: The name of the model to move or insert.
        preferred_models: The list of preferred model names to update.

    Returns:
        The updated list of preferred model names.
    """
    # Create a mutable copy to avoid modifying the original list unexpectedly
    models = preferred_models[:]
    if model_name in models:
        models.remove(model_name)
    models.insert(0, model_name)
    return models


def get_character_data_from_gemini(characters: List[str], model_name: str = DEFAULT_GEMINI_MODEL, debug: bool = DEBUG_FLAG, use_cache: bool = True, chunk_size: int = 10, language: str = 'English') -> Dict[str, Any]:
    """
    Use Google Gemini API to generate character data using the official Python library.
    With caching support to reduce API calls.

    Gemini models: https://ai.google.dev/gemini-api/docs/models

    Args:
        characters: A list of Chinese characters
        model_name: The name of the Gemini model the user *prefers* to use.
        debug: Whether to save debug information
        use_cache: Whether to use cached data
        chunk_size: Maximum number of characters to process in a single batch
        language: The language for the meaning and phrases.

    Returns:
        A dictionary with character data
    """
    # Set up cache database if using cache
    if use_cache:
        # Ensure your cache setup function is available
        # if not os.path.exists(CACHE_DB):
        #     setup_cache_db()
        pass # Assuming setup_cache_db is handled elsewhere or is conditional

    # Initialize result dictionary
    character_data: Dict[str, Any] = {}

    # Check cache first if enabled
    if use_cache:
        # Create a progress bar for cache lookup
        # with tqdm.tqdm(total=len(characters), desc="Checking cache", disable=len(characters) < 5) as pbar:
        for char in characters:
            # Ensure your get_cached_character function is available
            # cached_data = get_cached_character(char)
            cached_data = None # Placeholder
            if cached_data:
                character_data[char] = cached_data
            # pbar.update(1)
        if len(characters) >= 5:
             print("\nChecking cache: 100%\n") # Simple print if tqdm is not used

    if cached_chars := len(character_data):
        print(f"Found {cached_chars} characters in cache: {list(character_data.keys())} ! ")

    # Determine which characters we need to fetch from Gemini
    missing_chars = [char for char in characters if char not in character_data]

    # If all characters are in cache, return early
    if not missing_chars:
        print("All characters found in cache.")
        return character_data


    print(f"Fetching data for {len(missing_chars)} characters not in cache...")

    try:
        import google.generativeai as genai
    except ImportError:
        print("Google Generative AI library not found. Install with 'pip install google-generativeai'")
        # Ensure your generate_placeholder_data function is available
        for char in missing_chars:
            character_data[char] = {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"} # Placeholder
        return character_data

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in environment variables. Using placeholder data.")
        # Ensure your generate_placeholder_data function is available
        for char in missing_chars:
             character_data[char] = {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"} # Placeholder
        return character_data

    # Configure the Google Generative AI library with your API key
    genai.configure(api_key=api_key)

    # --- Improvement: Get available models and select the best one ---
    available_models = []
    try:
        # List only models that support the generateContent method
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                 available_models.append(m.name)
        print(f"Available models supporting generateContent: {available_models}")

    except Exception as e:
        print(f"Error listing available models: {e}")
        print("Proceeding with preferred list, but expect potential errors.")
        # If listing fails, we'll just rely on the hardcoded list

    # Update the preferred list based on the user's requested model
    current_preferred_models = update_gemini_models(model_name, PREFERRED_MODELS_TO_TRY)

    # Select the first preferred model that is actually available
    model = None
    selected_model_name = None
    for name in current_preferred_models:
        # Check if the model is in the list of available models (if listing was successful)
        if not available_models or f"models/{name}" in available_models:
             try:
                 # model = genai.GenerativeModel(name)
                 # Use genai.get_model(name) which is the recommended way
                 # and can provide more details/error checking.
                 # However, GenerativeModel(name) directly instantiates,
                 # so let's stick with that for minimal code change,
                 # but be aware get_model exists.
                 model = genai.GenerativeModel(name)
                 selected_model_name = name
                 print(f"Using Gemini model: {selected_model_name}")
                 break # Found a usable model, break the loop
             except Exception as model_error:
                 print(f"Could not use model {name}: {model_error}")
                 # If available_models was populated, and this model wasn't in it,
                 # the error is expected. If it *was* in available_models,
                 # the error is more significant.
                 continue # Try the next model in the preferred list

    if model is None:
        print("Error: No suitable Gemini models are available or could be initialized.")
        # Ensure your generate_placeholder_data function is available
        for char in missing_chars:
            character_data[char] = {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"} # Placeholder
        return character_data

    # --- End of Model Selection Improvement ---


    # Generation config for better output
    # Max output tokens might need adjustment based on model capabilities.
    # 8192 is high, might be okay for Pro/Flash 1.5/2.x
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192, # Keep high for batch processing
    }

    # --- Improvement: Use JSON mode if available and reliable ---
    # Parsing raw text can be error-prone. JSON output is much more robust.
    # Gemini 1.5 Pro/Flash and 2.x models support JSON mode.
    # You'll need to update your prompt to explicitly ask for JSON.
    # And update the parsing logic to handle JSON.

    # Check if the selected model supports JSON mode (this check is a simplification;
    # actual support might be tied to API version/client library version)
    # A more robust check might involve inspecting model capabilities if exposed by the API
    supports_json = selected_model_name in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"] # Add other models as they support JSON

    if supports_json:
        print(f"Model {selected_model_name} likely supports JSON mode. Attempting to use JSON.")
        generation_config["response_mime_type"] = "application/json"
        # Update the prompt to request JSON output
        # You'll need to define JSON_BASE_PROMPT with instructions for JSON output
        # Example JSON structure: {"characters": [{"character": "你", "pinyin": "nǐ", ...}, ...]}
        # JSON_BASE_PROMPT = """
        # Generate character information as a JSON object.
        # The JSON object should have a top-level key "characters" which is a list.
        # Each item in the list should be an object with keys: "character", "pinyin", "meaning", "composition", "phrases" (comma-separated string).
        # ... (add more specific instructions for the JSON format)
        # """
        # base_prompt = JSON_BASE_PROMPT.format(language=language) # Use the JSON prompt

        # *** For now, keeping your original text parsing logic, as implementing
        # *** JSON parsing is a significant change. But it's highly recommended.
        # *** If you switch to JSON, you'll need to remove the text parsing logic
        # *** below and add JSON parsing.
        pass # Keep original text parsing for now

    # --- End of JSON Mode Consideration ---


    file_raw = "gemini_response_batch.txt" # Consider making this more specific, e.g., include model name

    # APPROACH 1: Process characters in chunks for better rate limit handling
    # Initialize a list to track characters that need individual processing
    still_missing_chars = missing_chars.copy()

    if missing_chars:
        # Create chunks of characters to process in batches
        char_chunks = [missing_chars[i:i + chunk_size] for i in range(0, len(missing_chars), chunk_size)]

        print(f"Processing {len(missing_chars)} characters in {len(char_chunks)} chunks of max size {chunk_size} using model {selected_model_name}")

        # Process each chunk
        # Wrap with tqdm if available
        # for chunk_index, char_chunk in enumerate(tqdm.tqdm(char_chunks, desc="Processing chunks")):
        for chunk_index, char_chunk in enumerate(char_chunks):
            try:
                # Removed the len(char_chunk) > 1 check here - process single characters in the chunk loop too
                # click.echo(f"Processing chunk {chunk_index+1}/{len(char_chunks)} with {len(char_chunk)} characters...") # Use print if not using click

                chars_str = ', '.join([f"'{char}'" for char in char_chunk])

                # --- Improvement: Make the prompt more explicit for the batch ---
                batch_prompt = f"""
                Generate information about the following Chinese characters. Provide the details for each character individually in the requested format.
                Characters: {chars_str}

                {base_prompt}

                Ensure each character's information starts with 'Character:' followed by the character and then the requested fields (Pinyin, Meaning, Composition, Phrases) on separate lines.
                """
                # --- End of Prompt Improvement ---


                response = model.generate_content(
                    batch_prompt,
                    generation_config=generation_config
                )

                # Check for content in the response
                response_text = ""
                if hasattr(response, 'text') and response.text:
                     response_text = response.text.strip()
                elif response.candidates and response.candidates[0].content.parts:
                    # Handle potential different response structures
                     response_text = "".join(part.text for part in response.candidates[0].content.parts).strip()
                else:
                    print(f"Warning: No text content in response for chunk {chunk_index+1}")
                    # Characters in this chunk remain in still_missing_chars for individual processing
                    # Add a delay and continue to the next chunk
                    if chunk_index < len(char_chunks) - 1:
                        delay_time = 2.0 # Increase delay on error/empty response
                        print(f"Waiting {delay_time}s before next chunk after empty response...")
                        time.sleep(delay_time)
                    continue


                # Save response for debugging
                if debug:
                    LINE_MARKER = "===" * 20 # Adjusted length
                    log_header = f"\n\n--- AI Model: {selected_model_name} ---\n--- Chunk: {chunk_index+1}/{len(char_chunks)} ---\n--- Datetime: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{LINE_MARKER}\nPrompt:\n{batch_prompt}\n{LINE_MARKER}\nResponse:\n"
                    # Save the raw response for debugging
                    # Use a more specific filename for debug
                    debug_file = f"gemini_response_debug_{selected_model_name}.txt"
                    with open(debug_file, "a", encoding="utf-8") as f:
                        f.write(log_header)
                        f.write(response_text)
                    print(f"API response saved to {debug_file}")


                # --- Keep your original text parsing logic for now ---
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

                    # Check for new character section (be more flexible with spacing/punctuation around the character)
                    if line.lower().startswith('character:'):
                         # Save previous character if we were processing one
                         if current_char and current_data:
                             # Check if mandatory fields are present before saving
                             if all(field in current_data and current_data[field] for field in ['pinyin', 'meaning', 'composition', 'phrases']):
                                 batch_character_data[current_char] = current_data
                                 # Cache the character data
                                 # Ensure your cache_character function is available
                                 # if use_cache and current_data.get('pinyin', '') != 'Unknown':
                                 #     cache_character(current_char, current_data, llm_provider="Google", llm_model_name=selected_model_name)

                                 # Remove from still_missing_chars since we successfully processed it
                                 if current_char in still_missing_chars:
                                     still_missing_chars.remove(current_char)
                             else:
                                 # If data is incomplete, don't save/cache and it stays in still_missing_chars
                                 print(f"Warning: Incomplete data for character {current_char} from batch. Will re-attempt individually.")


                         # Start new character
                         char_part = line.split(':', 1)[1].strip() if ':' in line else line.replace('Character', '').strip()
                         # Extract the actual character from the potentially messy start
                         current_char = None
                         for c in char_part:
                             if c in char_chunk: # Check if the character is one we requested in this chunk
                                 current_char = c
                                 break
                         if current_char is None:
                              # Fallback: if we couldn't find the exact character, try the first non-space char
                              current_char = next((c for c in char_part if c.strip()), None)
                              if current_char:
                                   print(f"Warning: Couldn't find exact requested character in 'Character: {char_part}'. Using first character '{current_char}'.")


                         current_data = {}
                         current_field = None

                    # Check for field definitions
                    # Be more flexible with capitalization and trailing punctuation
                    elif ':' in line:
                         field_parts = line.split(':', 1)
                         field_name = field_parts[0].strip().lower().replace(':', '') # Clean up field name
                         field_value = field_parts[1].strip()

                         if field_name in ['pinyin', 'meaning', 'composition', 'phrases']:
                             current_data[field_name] = field_value
                             current_field = field_name
                         else:
                             # Handle cases where the colon might be part of the value,
                             # but the line is a continuation of a previous field.
                             # This simple logic might break if a value legitimately contains a colon
                             # and isn't indented. JSON would solve this.
                             if current_field:
                                 current_data[current_field] += ' ' + line # Append entire line

                    # Continuation of previous field (check for indentation or just assume continuation)
                    elif current_field:
                         current_data[current_field] += ' ' + line # Append entire line


                # Add the last character processed in the response (it won't be caught by the 'Character:' check)
                if current_char and current_data:
                    # Check if mandatory fields are present before saving
                    if all(field in current_data and current_data[field] for field in ['pinyin', 'meaning', 'composition', 'phrases']):
                        batch_character_data[current_char] = current_data
                        # Cache the character data
                        # Ensure your cache_character function is available
                        # if use_cache and current_data.get('pinyin', '') != 'Unknown':
                        #     cache_character(current_char, current_data, llm_provider="Google", llm_model_name=selected_model_name)

                        # Handle the last character in the response
                        if current_char in still_missing_chars:
                             still_missing_chars.remove(current_char)
                    else:
                         # If data is incomplete, don't save/cache and it stays in still_missing_chars
                         print(f"Warning: Incomplete data for last character {current_char} from batch. Will re-attempt individually.")


                # Update our main character_data dictionary
                character_data.update(batch_character_data)

                # Report on processing success for this chunk
                processed_count = len(batch_character_data)
                missing_in_chunk_after_parsing = len(char_chunk) - processed_count # This is not fully accurate because some might be incomplete
                print(f"Chunk {chunk_index+1} processing: Processed {processed_count}/{len(char_chunk)} characters with sufficient data.")
                # Note: still_missing_chars is the most accurate list of what still needs processing

                # Add a small delay between chunks to avoid rate limiting
                if chunk_index < len(char_chunks) - 1:
                    delay_time = 1.0  # 1 second delay between chunks
                    print(f"Waiting {delay_time}s before next chunk to avoid rate limits...")
                    time.sleep(delay_time)

            except Exception as chunk_error:
                print(f"Error processing chunk {chunk_index+1}: {chunk_error}")
                # Characters in this chunk will remain in still_missing_chars for individual processing
                # Consider adding a longer delay here before the next chunk or individual processing

    # APPROACH 2: Process any remaining characters one by one
    # We're using the still_missing_chars list that was updated during chunk processing

    if still_missing_chars:
        print(f"Retrieving data for {len(still_missing_chars)} remaining characters individually using model {selected_model_name}...")

        # Create a progress bar for individual character processing
        # with tqdm.tqdm(total=len(still_missing_chars), desc="Processing characters individually", disable=len(still_missing_chars) < 3) as pbar:
        for char in still_missing_chars:
            try:
                # Prompt for a single character - explicitly ask for the character in the output
                prompt = f"""
                Generate information about the Chinese character '{char}'. Provide the details in this EXACT format:

                Character: <the character itself>
                Pinyin: <pinyin with tone marks>
                Meaning: <English meaning>
                Composition: <breakdown into radicals/components>
                Phrases: <comma-separated list of 3 common phrases using the character>

                {BASE_PROMPT.format(language=language)} # Use the base prompt format instructions

                Ensure the output starts with 'Character: {char}'
                """
                # --- End of Individual Prompt Improvement ---


                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )

                # Check for content in the response
                response_text = ""
                if hasattr(response, 'text') and response.text:
                     response_text = response.text.strip()
                elif response.candidates and response.candidates[0].content.parts:
                    response_text = "".join(part.text for part in response.candidates[0].content.parts).strip()
                else:
                    print(f"Warning: No text content in response for character {char}. Using placeholder.")
                    character_data[char] = {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"} # Placeholder
                    # pbar.update(1) # Update even on placeholder
                    # Add a small delay before the next individual call
                    # time.sleep(0.5) # Delay before next char
                    continue


                # Save response for debugging
                if debug:
                     LINE_MARKER = "===" * 20
                     log_header = f"\n\n--- AI Model: {selected_model_name} ---\n--- Individual Character: {char} ---\n--- Datetime: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{LINE_MARKER}\nPrompt:\n{prompt}\n{LINE_MARKER}\nResponse:\n"
                     debug_file = f"gemini_response_debug_{selected_model_name}.txt"
                     with open(debug_file, "a", encoding="utf-8") as f:
                         f.write(log_header)
                         f.write(response_text)
                     print(f"API response saved to {debug_file}")


                # Simple line-by-line parsing for individual response
                char_data = {}
                current_field = None

                # --- Keep your original text parsing logic for individual response ---
                for line in response_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    if ':' in line:
                        parts = line.split(':', 1)
                        field_name = parts[0].strip().lower().replace(':', '')
                        field_value = parts[1].strip()

                        if field_name in ['character', 'pinyin', 'meaning', 'composition', 'phrases']:
                             # For individual response, update current_char based on output
                             if field_name == 'character':
                                  char_data[field_name] = field_value # Store the character as well
                                  # We already know the requested char, so no need to update current_char here
                             else:
                                 char_data[field_name] = field_value
                             current_field = field_name
                        else:
                            # Continuation
                            if current_field:
                                 char_data[current_field] += ' ' + line
                    else:
                         # Continuation without colon
                         if current_field:
                              char_data[current_field] += ' ' + line
                # --- End of Individual Parsing ---

                # Check if we got all the required fields (including the character itself from output)
                if all(field in char_data and char_data[field] for field in ['character', 'pinyin', 'meaning', 'composition', 'phrases']) and char_data.get('character') == char:
                    # We only need the data, not the repeated character key in the final dict
                    del char_data['character']
                    character_data[char] = char_data
                    # Cache the character data only if it's not placeholder data and successfully parsed
                    # Ensure your cache_character function is available
                    # if use_cache and char_data.get('pinyin', '') != 'Unknown':
                    #      cache_character(char, char_data, llm_provider="Google", llm_model_name=selected_model_name)
                else:
                    print(f"Missing some required fields or incorrect character in response for {char}. Using placeholder data.")
                    character_data[char] = {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"} # Placeholder


            except Exception as e:
                print(f"Error generating data for character {char}: {e}")
                character_data[char] = {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"} # Placeholder

            # Update progress bar
            # pbar.update(1)

            # Add a small delay between individual API calls
            # if char != still_missing_chars[-1]:  # Skip delay after the last character
            #     time.sleep(0.5)  # 0.5 second delay between individual characters
        if len(still_missing_chars) >= 3:
             print("\nProcessing characters individually: 100%\n") # Simple print if tqdm not used

    else:
        print("All characters were successfully processed in batch mode. No need for individual processing.")

    # Ensure we have data for all requested characters
    missing_final = [char for char in characters if char not in character_data]
    if missing_final:
        print(f"Adding placeholder data for {len(missing_final)} characters that couldn't be processed.")
        for char in missing_final:
             character_data[char] = {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"} # Placeholder


    return character_data

# # Example usage (requires setting GEMINI_API_KEY environment variable)
# if __name__ == "__main__":
#      # Define placeholder/mock functions if you're running this standalone for testing
#      def setup_cache_db():
#          print("Setting up cache DB (mock)")
#      def get_cached_character(char):
#          print(f"Checking cache for {char} (mock)")
#          return None # Always miss cache for demo
#      def cache_character(char, data, llm_provider, llm_model_name):
#          print(f"Caching data for {char} (mock)")
#      def generate_placeholder_data(char):
#          print(f"Generating placeholder for {char} (mock)")
#          return {"pinyin": "Unknown", "meaning": "Unknown", "composition": "Unknown", "phrases": "Unknown"}

#      import tqdm # Need to import tqdm if you want progress bars
#      import click # Need to import click if you want click.echo/print

#      # Set a dummy API key for the code to run without error,
#      # but replace with your actual key or environment variable setup
#      # os.environ['GEMINI_API_KEY'] = 'YOUR_ACTUAL_API_KEY'

#      test_characters = ["人", "口", "手", "大", "小", "山", "水", "火", "石", "日", "月", "田", "力", "男", "女"]

#      # Try with a preferred model
#      print("\n--- Attempting with gemini-2.5-flash ---")
#      data_2_5_flash = get_character_data_from_gemini(test_characters, model_name="gemini-2.5-flash", debug=True, use_cache=False, chunk_size=3)
#      print(f"\nResulting data (gemini-2.5-flash attempt): {data_2_5_flash}")

#      # Try with a known working model as fallback (if 2.5-flash failed)
#      print("\n--- Attempting with gemini-2.0-flash ---")
#      data_2_0_flash = get_character_data_from_gemini(test_characters, model_name="gemini-2.0-flash", debug=True, use_cache=False, chunk_size=3)
#      print(f"\nResulting data (gemini-2.0-flash attempt): {data_2_0_flash}")
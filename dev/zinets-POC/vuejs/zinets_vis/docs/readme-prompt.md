can you help me prototype a vue.js app to manage chinese character data,

Here are detailed requirements:
"""
# Simple Vue.js to manage character data 

Functionality: basic CRUD operations:
Search: Find characters based on specific criteria
Filter characters based on criteria (e.g., word in meaning, llm_provider, active, best)
Read: Retrieve character information from the database
upper panel: Display list of characters in a table with pagination
lower panel: Display character details in a form when a character is selected in upper panel
upper panel and lower panel are connected as parent-child
Update: Modify existing character information
upper panel: Select a character from the list
lower panel: Update/revise character details in the form
Update character details in the database
Create: Add a new character to the database
upper panel: no selection
lower panel: Add a new character with all details in the form
Save new character to the database
Soft-Delete: Update character status to inactive
upper panel: Select a character from the list
lower panel: Update character status to inactive
Update character status in the database
Frontend: Vue.js with Element Plus
backend: FastAPI to access SQLite database
## Database: SQLite

DB File: "zinets_cache.sqlite"
table character_cache schema sql
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
"""

Here is a screenshot with sample character data


# Extra session on zinets_vis app 
https://claude.ai/chat/c631d9dd-45aa-4b54-bf12-0cbe871236b2

I notice you're asking me to continue generating a `stores/character.js` file for a `zinets_vis` app while ignoring the `zinets_crud` app context. However, I don't see any previous chat history or project context in our current conversation that would allow me to understand what the `zinets_vis` app is or what the character store should contain.

To help you create the `stores/character.js` file, I would need more information about:

1. What framework you're using (Vue.js with Pinia, React with Redux, vanilla JavaScript, etc.)
2. What the character store should manage (character data, state, actions)
3. The structure of your character objects
4. Any specific functionality you need

Could you provide some context about the `zinets_vis` app and what you'd like the character store to accomplish? Then I can help generate the appropriate store file for your project.


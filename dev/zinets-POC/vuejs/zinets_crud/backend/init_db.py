import sqlite3
import datetime

# Sample data
sample_data = [
    {
        "character": "噪",
        "pinyin": "zào",
        "meaning": "noisy; chirping of birds",
        "composition": "Four '口' (mouth) characters, representing noisy sounds",
        "phrases": "喧噪 (xuān zào) - noisy<br>噪宗 (zào zōng) - a noisy crowd",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "澡",
        "pinyin": "zǎo",
        "meaning": "to bathe; to wash",
        "composition": "'氵' (water radical) + '澡' (noise/wash)",
        "phrases": "洗澡 (xǐ zǎo) - to take a bath/shower<br>淋浴澡 (lín yù zǎo) - to take a shower",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "氵",
        "pinyin": "shuǐ",
        "meaning": "water (radical)",
        "composition": "A simplified form of the character '水' (water)",
        "phrases": "(This is a radical, not a standalone character)",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "艹",
        "pinyin": "cǎo",
        "meaning": "grass (radical)",
        "composition": "Represents grass or plants.",
        "phrases": "(This is a radical, not a standalone character)",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "藻",
        "pinyin": "zǎo",
        "meaning": "algae; seaweed",
        "composition": "'艹' (grass radical) + '澡' (noise/wash)",
        "phrases": "海藻 (hǎi zǎo) - seaweed<br>藻类 (zǎo lèi) - algae",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "品",
        "pinyin": "pǐn",
        "meaning": "product; commodity; grade; rank; to taste",
        "composition": "Three '口' (mouth) characters stacked vertically",
        "phrases": "产品 (chǎn pǐn) - product<br>品质 (pǐn zhì) - quality",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "口",
        "pinyin": "kǒu",
        "meaning": "mouth; entrance; measure word (for people or actions)",
        "composition": "A simple pictograph representing a mouth",
        "phrases": "人口 (rén kǒu) - population<br>门口 (mén kǒu) - doorway",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "木",
        "pinyin": "mù",
        "meaning": "tree; wood",
        "composition": "A simple pictograph representing a tree",
        "phrases": "木头 (mù tou) - wood; log; blockhead<br>木材 (mù cái) - lumber",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "浪",
        "pinyin": "làng",
        "meaning": "wave, surge, billow, unrestrained, dissipated",
        "composition": "'氵 (water radical) + 良 (liáng, good)",
        "phrases": "浪花 (làng huā) - wave, spray<br>浪漫 (làng màn) - romantic",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "江",
        "pinyin": "jiāng",
        "meaning": "river (long); the Yangtze River",
        "composition": "'氵 (water radical) + 工 (gōng, work)",
        "phrases": "江河 (jiāng hé) - rivers<br>长江 (cháng jiāng) - the Yangtze River",
        "llm_provider": "Google",
        "llm_model_name": "gemini-pro",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    # Add some OpenAI examples
    {
        "character": "日",
        "pinyin": "rì",
        "meaning": "sun; day",
        "composition": "Pictograph of the sun",
        "phrases": "日本 (rì běn) - Japan<br>日记 (rì jì) - diary",
        "llm_provider": "OpenAI",
        "llm_model_name": "gpt-4",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    },
    {
        "character": "月",
        "pinyin": "yuè",
        "meaning": "moon; month",
        "composition": "Pictograph of the moon",
        "phrases": "月亮 (yuè liang) - moon<br>月份 (yuè fèn) - month",
        "llm_provider": "OpenAI",
        "llm_model_name": "gpt-4",
        "timestamp": datetime.datetime.now().isoformat(),
        "is_active": "Y",
        "is_best": "Y"
    }
]

def init_db():
    # Connect to SQLite database
    conn = sqlite3.connect('zinets_cache.sqlite')
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
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
    
    # Insert sample data
    for data in sample_data:
        try:
            cursor.execute('''
            INSERT INTO character_cache 
            (character, pinyin, meaning, composition, phrases, llm_provider, llm_model_name, timestamp, is_active, is_best)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data["character"], data["pinyin"], data["meaning"], data["composition"],
                data["phrases"], data["llm_provider"], data["llm_model_name"],
                data["timestamp"], data["is_active"], data["is_best"]
            ))
        except sqlite3.IntegrityError:
            print(f"Character {data['character']} with provider {data['llm_provider']} already exists. Skipping.")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized with sample data.")

if __name__ == "__main__":
    init_db()

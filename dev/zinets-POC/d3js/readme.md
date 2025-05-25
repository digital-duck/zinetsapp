# Zinets POC D3.js Frontend

- [Qwen](https://chat.qwen.ai/c/7c2e9ddd-8220-4e4f-9a1d-3c1cde1049bc)
- [Claude](https://claude.ai/chat/a22251d9-1aeb-4ce4-ac06-a78b76d5ff8f)


## local HTTP server
```
python -m http.server 3000

# URL = http://localhost:3000/index.html
```

## markdown to D3 data

### Markdown

```markdown
子 - Child
    - Humans
        - 子女 - Children
        - 父子 - Father/Son
        - 弟子 - Disciple
        - 子孙 - Descendants
    - Honorifics
        - 老子 - Laozi
        - 孔子 - Confucius
        - 君子 - Gentleman
    - Physics
        - 原子 - Atom
        - 光子 - Photon
        - 量子 - Quantum
    - Animals
        - 兔子 - Rabbit
        - 蚊子 - Mosquito
        - 狮子 - Lion
```

### D3.js

```javascript
const data = {
    "nodes": [
    {"id": "A", "name": "子 - Child", "group": 0, "url": "https://en.wiktionary.org/wiki/子"},
    
    {"id": "B", "name": "Humans", "group": 1, "url": "https://en.wikipedia.org/wiki/Chinese_kinship"},
    {"id": "C", "name": "Honorifics", "group": 2, "url": "https://en.wikipedia.org/wiki/Chinese_philosophy"},
    {"id": "E", "name": "Physics", "group": 4, "url": "https://en.wikipedia.org/wiki/Physics"},
    {"id": "H", "name": "Animals", "group": 7, "url": "https://en.wikipedia.org/wiki/Animal"},

    {"id": "B1", "name": "子女 - Children", "group": 1, "url": "https://en.wiktionary.org/wiki/子女"},
    {"id": "B2", "name": "父子 - Father/Son", "group": 1, "url": "https://en.wikipedia.org/wiki/Father"},
    {"id": "B3", "name": "弟子 - Disciple", "group": 1, "url": "https://en.wikipedia.org/wiki/Disciple"},
    {"id": "B4", "name": "子孙 - Descendants", "group": 1, "url": "https://en.wikipedia.org/wiki/Kinship"},

    {"id": "C2", "name": "老子 - Laozi", "group": 2, "url": "https://en.wikipedia.org/wiki/Laozi"},
    {"id": "C1", "name": "孔子 - Confucius", "group": 2, "url": "https://en.wikipedia.org/wiki/Confucius"},
    {"id": "C4", "name": "君子 - Gentleman", "group": 2, "url": "https://en.wikipedia.org/wiki/Junzi"},

    {"id": "E1", "name": "原子 - Atom", "group": 4, "url": "https://en.wikipedia.org/wiki/Atom"},
    {"id": "E3", "name": "光子 - Photon", "group": 4, "url": "https://en.wikipedia.org/wiki/Photon"},
    {"id": "E4", "name": "量子 - Quantum", "group": 4, "url": "https://en.wikipedia.org/wiki/Quantum"},

    {"id": "H1", "name": "兔子 - Rabbit", "group": 7, "url": "https://en.wikipedia.org/wiki/Rabbit"},
    {"id": "H2", "name": "蚊子 - Mosquito", "group": 7, "url": "https://en.wikipedia.org/wiki/Mosquito"},
    {"id": "H3", "name": "狮子 - Lion", "group": 7, "url": "https://en.wikipedia.org/wiki/Lion"}

    ],
    "links": [
    {"source": "A", "target": "B"},
    {"source": "A", "target": "C"},
    {"source": "A", "target": "E"},
    {"source": "A", "target": "H"},

    {"source": "B", "target": "B1"},
    {"source": "B", "target": "B2"},
    {"source": "B", "target": "B3"},
    {"source": "B", "target": "B4"},

    {"source": "C", "target": "C1"},
    {"source": "C", "target": "C2"},
    {"source": "C", "target": "C4"},


    {"source": "E", "target": "E1"},
    {"source": "E", "target": "E3"},
    {"source": "E", "target": "E4"},

    {"source": "H", "target": "H1"},
    {"source": "H", "target": "H2"},
    {"source": "H", "target": "H3"}

    ]
};

```



## Dev

### Mindscope

- Prompt to Claude Sonnet 4 
```text 
can you package your javascript logic in the standalone HTML app we had before?

1) keep "exampleMarkdown" as default markdown text input

2) allow user to specify their own network data in markdown format, then convert it into D3.js data object, then render it is D3 chart

3) when creating URL for a node, first lookup "urlMappings", if missing, use google search URL as default
```

- HTML standalone app
`mindscope.html`
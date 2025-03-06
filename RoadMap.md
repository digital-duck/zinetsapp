### 2025-03-05

#### FastAPI at backend:

- /ele_zis/  # return all elemental Zi (done)
- /ele_zis/query?sun  # find Sun related elemental characters
- /ele_zis/日   # query-by-id: zi='日'

- /zi_matrix/日  # find compound Zi containing 日 at any position
- /zi_matrix/zi_left=日&zi_right=月   # return 明

- /zi_dict/   # return all Zi's with pagination
- /zi_dict/日   # query-by-id: zi='日'
- /zi_dict/query?sun  # find Sun related characters 
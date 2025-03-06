### 2025-03-05

#### FastAPI at backend:

- /ele_zis/  # return all elemental Zi (done)
- /ele_zis_search/sun  # find Sun related elemental characters
- /ele_zis/日   # query-by-id: zi='日'

return
```
[{"zi":"日","pinyin":"rì","phono":"ri","n_strokes":4,"n_frequency":125,"meaning":"sun","category":"天文-日","sub_category":"","examples":"旦、旨、早","variant":"","notes":"","is_radical":"Y","is_neted":"Y","u_id":"89","is_active":"Y"}]
```

- /zi_matrix/日  # find compound Zi containing 日 at any position
- /zi_matrix/zi_left=日&zi_right=月   # return 明

- /zi_dict/   # return all Zi's with pagination
- /zi_dict/日   # query-by-id: zi='日'
- /zi_dict_search/sun  # find Sun related characters 
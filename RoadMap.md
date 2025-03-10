### 2025-03-08

- support semantic search (multilingual)
    - use postgresql which can do SQL search and vector search
    - use pgVector to vectorize t_ele_zi table data
    - `/ele_zi_search/人` search should do both
        - 


### 2025-03-05

#### FastAPI at backend 

##### pagination (DONE)

##### tester (DONE)
http://127.0.0.1:8000/docs


- /ele_zi_list/  # return all elemental Zi (done)
- /ele_zi/日   # query-by-id: zi='日'

return
```
[{"zi":"日","pinyin":"rì","phono":"ri","n_strokes":4,"n_frequency":125,"meaning":"sun","category":"天文-日","sub_category":"","examples":"旦、旨、早","variant":"","notes":"","is_radical":"Y","is_neted":"Y","u_id":"89","is_active":"Y"}]
```
- /ele_zi_search/sun  # find Sun related elemental characters
- /ele_zi_search/人


- /zi_matrix_search/差  # find compound Zi containing 日 at any position

return
```
[
  {
    "zi": "傞",
    "zi_left_up": "",
    "zi_left": "亻",
    "zi_left_down": "",
    "zi_up": "",
    "zi_mid": "差",
    "zi_down": "",
    "zi_right_up": "",
    "zi_right": "",
    "zi_right_down": "",
    "zi_mid_out": "",
    "zi_mid_in": "",
    "desc_cn": "醉舞皃。从人差聲。《詩》曰：“屢舞傞傞。”",
    "desc_en": "",
    "hsk_note": ""
  },
]
```

- /zi_matrix/zi_up=⺶&zi_mid=工   # return 差  (ToDo)
- /zi_matrix/zi_up=⺶
- /zi_matrix/zi_mid=工

- /zi_dict_list/   # return all Zi's with pagination
- /zi_dict_list/skip=0&limit=10   # pagination
- /zi_dict/日2
- /zi_dict/日   # query-by-id: zi='日'

return 
```
[{"zi":"日","u_id":"8884","unicode":"","pinyin":"ri4","nstrokes":"4","alias":"","traditional":"","as_part":"Y","is_radical":"Y","layer":"HSK_1-Common-01","desc_cn":"","zi_en":"","desc_en":"sun/day/date, day of the month","ts":"2024-09-08 22:51:41","sort_val":113.0,"is_active":"Y","notes":"","is_picto":"Y","set_id":"2","category":"天文-日","baidu_url":"https://baike.baidu.com/item/%E6%97%A5/35262","fib_num":"2"}]
```
- /zi_dict_search/sun  # find Sun related characters 
import time
import functools
from typing import Any, Callable, Dict, Optional, Tuple, Union
from fastapi import FastAPI, UploadFile, Query
import pandas as pd
import sqlite3

app = FastAPI()

CFG = {
    "DEBUG_FLAG" : True, # False, # 
    "SQL_EXECUTION_FLAG" : True, #  False, #   control SQL

    "DB_FILENAME" : r"C:\Users\p2p2l\projects\wgong\zistory\zinets\app\zadmin\zi.sqlite",

    # assign table names
    "TABLE_ZI" : "t_zi",            # all Zi 字
    "TABLE_ELEZI" : "t_ele_zi",     # 元字 
    "TABLE_ZI_PART" : "t_zi_part",  # decomposed Zi 字子 

}
TABLE_ELEZI = CFG["TABLE_ELEZI"]
TABLE_ZI_PART = CFG["TABLE_ZI_PART"]
TABLE_ZI = CFG["TABLE_ZI"]
limit_by_size = 20  # -1 for all
LIMIT_BY_CLAUSE = " " if limit_by_size < 0 else f" limit {limit_by_size} "
ZI_MATRIX_COLS = ("zi_left_up", "zi_left", 'zi_left_down', 'zi_up', 'zi_mid', 'zi_down', 'zi_right_up', 'zi_right', 'zi_right_down', 'zi_mid_out', 'zi_mid_in')

#############################
class DBConn(object):
    def __init__(self, db_file=CFG["DB_FILENAME"]):
        self.conn = sqlite3.connect(db_file)

    def __enter__(self):
        return self.conn

    def __exit__(self, type, value, traceback):
        self.conn.close()


def db_run_sql(sql_stmt, conn=None, debug=CFG["DEBUG_FLAG"]):
    """handles both select and insert/update/delete
    """
    if not sql_stmt or conn is None:
        return None
    
    debug_print(sql_stmt, debug=debug)

    if sql_stmt.lower().strip().startswith("select"):
        return pd.read_sql(sql_stmt, conn)
    
    cur = conn.cursor()
    cur.executescript(sql_stmt)
    conn.commit()
    # conn.close()
    return None


def db_execute(sql_statement, 
               debug=CFG["DEBUG_FLAG"], 
               execute_flag=CFG["SQL_EXECUTION_FLAG"],):
    """handles insert/update/delete
    """
    with DBConn() as _conn:
        debug_print(sql_statement, debug=debug)
        if execute_flag:
            _conn.execute(sql_statement)
            _conn.commit()
        else:
            print("[WARN] SQL Execution is off ! ")   

def debug_print(msg, debug=CFG["DEBUG_FLAG"]):
    if debug and msg:
        # st.write(f"[DEBUG] {str(msg)}")
        print(f"[DEBUG] {str(msg)}")

def cache_func_with_ttl(ttl: int = 3600):
    """
    A decorator that caches function results with a time-to-live (TTL) in seconds.
    
    Args:
        ttl (int): Time-to-live in seconds. Default is 3600 (1 hour).
    
    Returns:
        A decorator function that caches the results of the decorated function.
    """
    cache: Dict[Tuple, Dict[str, Any]] = {}
    
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from the function arguments
            key = (func.__name__, tuple(args), tuple(sorted(kwargs.items())))
            
            # Check if we have a cached result and it's still valid
            if key in cache:
                result, timestamp = cache[key]['result'], cache[key]['timestamp']
                if time.time() - timestamp < ttl:
                    return result
            
            # No cache hit or expired cache, call the function
            result = func(*args, **kwargs)
            
            # Store the result in cache
            cache[key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            return result
        return wrapper
    return decorator

@cache_func_with_ttl(ttl=3600)  # Cache for 60 minutes
def count_table(table_name: str = TABLE_ZI):
    """
    Get the total count of characters in the t_zi table.
    Returns the count as an integer.
    """
    with DBConn() as _conn:
        cursor = _conn.cursor()
        sql_stmt = f"""
            select 
                count(*)
            from {table_name}
            where is_active = 'Y'
            ;
        """
        cursor.execute(sql_stmt)
        total_count = cursor.fetchone()[0]
        return total_count

@app.get("/")
def read_root():
    return {"Hello": "Welcome to ZiNets World"}

@app.get("/ele_zi_list/")
def ele_zi_list():
    """Return all Elemental Zi's
    """
    res = {}
    with DBConn() as _conn:
        sql_stmt = f"""
            select 
                zi
                , pinyin
                , phono
                , n_strokes
                , n_frequency
                , meaning
                , category
                , sub_category
                , examples
                , variant
                , notes
                , is_radical
                , is_neted
                , u_id
                , is_active
            from {TABLE_ELEZI}
            where 1=1
                and is_active = 'Y'
            order by n_strokes, zi
            {LIMIT_BY_CLAUSE}
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            # print(df.shape[0])
            res = df.to_dict(orient="records")

    return res

@app.get("/ele_zi/{zi_value}")
def ele_zi_query_by_id(zi_value: str):
    """Return Elemental Zi by specific value
    """
    res = {}

    zi_value = zi_value.strip()
    if not zi_value:
        return res 
        
    with DBConn() as _conn:
        sql_stmt = f"""
            select 
                zi
                , pinyin
                , phono
                , n_strokes
                , n_frequency
                , meaning
                , category
                , sub_category
                , examples
                , variant
                , notes
                , is_radical
                , is_neted
                , u_id
                , is_active
            from {TABLE_ELEZI}
            where 1=1
                and is_active = 'Y'
                and trim(zi) = '{zi_value}'
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            res = df.to_dict(orient="records")
            print(res)

    return res

@app.get("/ele_zi_search/{key_word}")
def ele_zi_search(key_word: str):
    """Search Elemental Zi table by key_word
    """
    res = {}

    key_word = key_word.strip().lower()  # case-insensitive match
    if not key_word:
        return res 
    
    with DBConn() as _conn:
        sql_stmt = f"""
            select 
                zi
                , pinyin
                , phono
                , n_strokes
                , n_frequency
                , meaning
                , category
                , sub_category
                , examples
                , variant
                , notes
                , is_radical
                , is_neted
                , u_id
                , is_active
            from {TABLE_ELEZI}
            where 1=1
                and is_active = 'Y'
                and (zi like '%{key_word}%'
                    OR lower(phono) like '%{key_word}%'
                    OR lower(meaning) like '%{key_word}%'
                    OR lower(category) like '%{key_word}%'
                    OR lower(sub_category) like '%{key_word}%'
                    OR lower(examples) like '%{key_word}%'
                    OR lower(variant) like '%{key_word}%'
                    OR lower(notes) like '%{key_word}%'
                )
            order by n_strokes, zi
            {LIMIT_BY_CLAUSE}
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            # print(df.shape[0])
            res = df.to_dict(orient="records")

    return res


@app.get("/zi_matrix_search/{key_word}")
def zi_matrix_search(key_word: str):
    """Search Zi parts table by key_word
    """
    res = {}
    key_word = key_word.strip()
    if not key_word:
        return res 
    
    with DBConn() as _conn:
        sql_stmt = f"""
            select distinct
                zp.zi
                , zp.zi_left_up
                , zp.zi_left
                , zp.zi_left_down
                , zp.zi_up
                , zp.zi_mid
                , zp.zi_down
                , zp.zi_right_up
                , zp.zi_right
                , zp.zi_right_down
                , zp.zi_mid_out
                , zp.zi_mid_in
            from {TABLE_ZI_PART} zp
            where 1=1
                and zp.is_active = 'Y'
                and (  trim(zp.zi) = '{key_word}'
                    OR trim(zp.zi_left_up) = '{key_word}'
                    OR trim(zp.zi_left) = '{key_word}'
                    OR trim(zp.zi_left_down) = '{key_word}'
                    OR trim(zp.zi_up) = '{key_word}'
                    OR trim(zp.zi_mid) = '{key_word}'
                    OR trim(zp.zi_down) = '{key_word}'
                    OR trim(zp.zi_right_up) = '{key_word}'
                    OR trim(zp.zi_right) = '{key_word}'
                    OR trim(zp.zi_right_down) = '{key_word}'
                    OR trim(zp.zi_mid_out) = '{key_word}'
                    OR trim(zp.zi_mid_in) = '{key_word}'
                )
            order by zp.zi
            {LIMIT_BY_CLAUSE}
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            # print(df.shape[0])
            res = df.to_dict(orient="records")

    return res

# https://claude.ai/chat/26a2a410-89d7-42e1-89e9-4ef29f261d69
@app.get("/zi_matrix/{query_str}")
def zi_matrix_query(query_str: str):
#     zi_left_up: str = Query(None, description="Left Up part"),
#     zi_left: str = Query(None, description="Left part"),
#     zi_left_down: str = Query(None, description="Left Down part"),
#     zi_up: str = Query(None, description="Up part"),
#     zi_mid: str = Query(None, description="Mid part"),
#     zi_down: str = Query(None, description="Down part"),
#     zi_right_up: str = Query(None, description="Right Up part"),
#     zi_right: str = Query(None, description="Right part"),
#     zi_right_down: str = Query(None, description="Right Down part"),
#     zi_mid_in: str = Query(None, description="Mid-In part"),
#     zi_mid_out: str = Query(None, description="Mid-Out part")                
# ):
    """Query Zi parts table by position 
    """
    res = {}
    query_str = query_str.strip()
    if not query_str:
        return res
    
    # prepare SQL where clause
    where_clauses = []
    for k,v in [i.split("=") for i in query_str.split("&")]:
        if k not in ZI_MATRIX_COLS:
            continue
        where_clauses.append(f" trim(zp.{k}) = '{v}' ")

    if len(where_clauses) < 1:
        return res 
    
    where_clause_str = " AND ".join(where_clauses)
    with DBConn() as _conn:
        sql_stmt = f"""
            select distinct
                zp.zi
                , zp.zi_left_up
                , zp.zi_left
                , zp.zi_left_down
                , zp.zi_up
                , zp.zi_mid
                , zp.zi_down
                , zp.zi_right_up
                , zp.zi_right
                , zp.zi_right_down
                , zp.zi_mid_out
                , zp.zi_mid_in
                , zp.desc_cn
                , zp.desc_en
                , zp.hsk_note
            from {TABLE_ZI_PART} zp
            where 1=1
                and zp.is_active = 'Y'
                and ( {where_clause_str} )
            order by zp.zi
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            # print(df.shape[0])
            res = df.to_dict(orient="records")

    return res


@app.get("/zi_dict_list/{query_str}")
def zi_dict_list(query_str: str):
    """Return all Zi's
    """
    v_skip, v_limit = 0, 10

    query_str = query_str.strip()
    if not query_str: 
        limit_clause = " "
    else:
        for k, v in [i.split("=") for i in query_str.split("&")]:
            if k == "skip":
                v_skip = v 
            elif k == "limit":
                v_limit = v
        limit_clause = f" LIMIT {v_limit} OFFSET {v_skip} "
        
    res = {
        "total": 0,
        "offset": v_skip,
        "limit": v_limit,
    }
    with DBConn() as _conn:
        total_count = count_table(table_name=TABLE_ZI)
        if total_count < 1:
            return res 
        
        res.update({"total": total_count})

        sql_stmt = f"""
            select 
                *
            from {TABLE_ZI}
            where 1=1
                and is_active = 'Y'
            order by zi
            {limit_clause}
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            res.update({"data": df.to_dict(orient="records")})

    return res

@app.get("/zi_dict/{zi_value}")
def zi_dict_query_by_id(zi_value: str):
    """Return Zi by id
    """
    res = {}
    zi_value = zi_value.strip()
    if not zi_value:
        return res 
        
    with DBConn() as _conn:
        sql_stmt = f"""
            select 
                *
            from {TABLE_ZI}
            where 1=1
                and is_active = 'Y'
                and trim(zi) = '{zi_value}'
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            # print(df.shape[0])
            res = df.to_dict(orient="records")

    return res

@app.get("/zi_dict_search/{key_word}")
def zi_dict_search(key_word: str):
    """Search Zi dictionary by key_word
    """
    res = {}
    key_word = key_word.strip().lower()  # case-insensitive match
    if not key_word:
        return res 
        
    with DBConn() as _conn:
        sql_stmt = f"""
            select *
            from {TABLE_ZI}
            where 1=1
                and is_active = 'Y'
                and (zi like '%{key_word}%'
                    OR lower(pinyin) like '%{key_word}%'
                    OR lower(alias) like '%{key_word}%'
                    OR lower(traditional) like '%{key_word}%'
                    OR lower(desc_cn) like '%{key_word}%'
                    OR lower(zi_en) like '%{key_word}%'
                    OR lower(desc_en) like '%{key_word}%'
                    OR lower(notes) like '%{key_word}%'
                    OR lower(category) like '%{key_word}%'
                )
            order by zi
            {LIMIT_BY_CLAUSE}
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            # print(df.shape[0])
            res = df.to_dict(orient="records")

    return res

###======================================================
### Donot use
# @app.get("/<end_point>/")
# def end_point():
#     """Return 
#     """
#     res = {}

#     return res


from typing import Union, Dict
from fastapi import FastAPI, UploadFile
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
TABLE_ZIPART = CFG["TABLE_ZI_PART"]
TABLE_ZI = CFG["TABLE_ZI"]
limit_by_size = 20  # -1 for all
LIMIT_BY_CLAUSE = " " if limit_by_size < 0 else f" limit {limit_by_size} "


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


@app.get("/")
def read_root():
    return {"Hello": "Welcome to ZiNets World"}

@app.get("/ele_zis/")
def query_ele_zi():
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

@app.get("/ele_zis_search/{key_word}")
def search_ele_zi(key_word: str):
    """Search Elemental Zi table by key_word
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
                and (zi like '%{key_word}%'
                    or phono like '%{key_word}%'
                    or meaning like '%{key_word}%'
                    or category like '%{key_word}%'
                    or sub_category like '%{key_word}%'
                    or examples like '%{key_word}%'
                    or variant like '%{key_word}%'
                    or notes like '%{key_word}%'
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

@app.get("/ele_zis/{zi_value}")
def query_ele_zi_by_id(zi_value: str):
    """Return Elemental Zi by specific value
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
                and zi = '{zi_value.strip()}'
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            res = df.to_dict(orient="records")
            print(res)

    return res

@app.get("/zi_dict/{zi_value}")
def query_zi_by_id(zi_value: str):
    """Return Zi by id
    """
    res = {}
    with DBConn() as _conn:
        sql_stmt = f"""
            select 
                *
            from {TABLE_ZI}
            where 1=1
                and is_active = 'Y'
                and zi = '{zi_value.strip()}'
            ;
        """
        debug_print(sql_stmt)
        df = pd.read_sql(sql_stmt, _conn).fillna("")
        if df is not None and not df.empty:
            # print(df.shape[0])
            res = df.to_dict(orient="records")

    return res

@app.get("/zi_dict_search/{key_word}")
def search_zi(key_word: str):
    """Search Zi dictionary by key_word
    """
    res = {}
    with DBConn() as _conn:
        sql_stmt = f"""
            select *
            from {TABLE_ZI}
            where 1=1
                and is_active = 'Y'
                and (zi like '%{key_word}%'
                    or pinyin like '%{key_word}%'
                    or alias like '%{key_word}%'
                    or traditional like '%{key_word}%'
                    or desc_cn like '%{key_word}%'
                    or zi_en like '%{key_word}%'
                    or desc_en like '%{key_word}%'
                    or notes like '%{key_word}%'
                    or category like '%{key_word}%'
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


### Donot use
@app.get("/<endpoint>/")
def query_1():
    """Return all Elemental Zi's
    """
    res = {}

    return res


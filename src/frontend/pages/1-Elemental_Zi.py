import streamlit as st
import pandas as pd
from utils import fetch_data

st.set_page_config(
    page_title="Elemental Zi",
    page_icon="🔤",
    layout="wide"
)

st.title("Elemental Zi")
st.markdown("""
Elemental Zi are basic Chinese characters that cannot be further divided into smaller meaningful components.
These characters form the foundation of the Chinese writing system.
""")


df = fetch_data(endpoint="/ele_zis/")

if df is not None and not df.empty:
    st.subheader(f"Showing {len(df)} Elemental Characters")
    st.dataframe(df)
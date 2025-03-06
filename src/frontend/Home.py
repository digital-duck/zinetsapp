import streamlit as st
import requests
import pandas as pd
# from utils import fetch_data

st.set_page_config(
    page_title="ZiNets App",
    page_icon="📚",
    layout="wide"
)

st.title("ZiNets App")
st.markdown("""
This application allows you to explore Chinese characters (Zi).

### Navigation:
- **Elemental Zi**: basic characters as building blocks
- **Compound Zi**: Characters that are composed of elemental characters
- **Zi Dictionary**: Search and browse the full dictionary
""")
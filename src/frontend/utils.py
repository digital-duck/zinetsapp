import streamlit as st
import requests
import pandas as pd

# Base URL for the FastAPI backend
API_BASE_URL = "http://localhost:8000"

# @st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_data(endpoint="/ele_zis/", limit=20, filters=None):
    """
    Fetch data from the FastAPI backend
    
    Parameters:
    - endpoint: API endpoint to call
    - limit: Number of records to fetch (optional)
    - filters: Dictionary of filter parameters (optional)
    
    Returns:
    - pandas DataFrame with the fetched data
    """
    url = f"{API_BASE_URL}{endpoint}"
    
    params = {}
    if limit:
        params["limit"] = limit
    
    if filters:
        params.update(filters)
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Convert JSON response to DataFrame
        data = response.json()
        df = pd.DataFrame(data)
        
        return df
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error
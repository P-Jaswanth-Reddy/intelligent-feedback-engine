import streamlit as st
from sentence_transformers import SentenceTransformer

@st.cache_resource
def load_model():
    # Switched from 'all-mpnet-base-v2' to 'all-MiniLM-L6-v2' to save ~340MB of RAM
    # This prevents EasyOCR from throwing an out-of-memory error when it loads.
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_model()
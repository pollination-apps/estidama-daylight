"""A module to collect helper functions for the simscale outdoor comfort app."""

import streamlit as st


def local_css(file_path: str):
    """Inject styles to the streamlit app using a local CSS file.

    Args:
        file_path: String path to the CSS file.
    """
    with open(file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

"""Collection of Helper functions."""

import json
import streamlit as st
from pathlib import Path
from honeybee.model import Model as HBModel


def get_hbjson_path(temp_folder: Path, hb_model: HBModel) -> Path:
    hbjson_path = temp_folder.joinpath(f'{hb_model.identifier}.hbjson')
    hbjson_path.write_text(json.dumps(hb_model.to_dict()))

    return hbjson_path


def local_css(file_name):
    """Load local css file."""
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

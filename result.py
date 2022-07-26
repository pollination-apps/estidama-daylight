"""Result tab of the Estidama daylight app."""

import streamlit as st
from pathlib import Path
from typing import Dict, List


def result(sim_dict: Dict[str, str], res_dict: Dict[str, List[Path]]):
    """UI to visualize the results of the simulation."""
    st.write(res_dict, 'ok')

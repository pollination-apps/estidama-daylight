"""Pollination outdoor comfort app."""

import tempfile
import streamlit as st

from pathlib import Path

from pollination_streamlit_io import get_host

from model import sensor_grids
from introduction import introduction
from occupied_area import select, validate

st.set_page_config(
    page_title='Estidama Daylight',
    page_icon='https://app.pollination.cloud/favicon.ico',
    layout='centered',
    initial_sidebar_state='collapsed'
)


def main():

    tab0, tab1, tab2, tab3 = st.tabs(
        ["Introduction", "Occupied Areas", "Submit", "Results"])

    with tab0:
        st.session_state.host = get_host()
        if not st.session_state.host:
            st.session_state.host = 'web'

        if 'temp_folder' not in st.session_state:
            st.session_state.temp_folder = Path(
                tempfile.mkdtemp(prefix=f'{st.session_state.host}_'))

        # TODO: Expose this on UI and get this info from CAD environment
        st.session_state.tolerance = 0.01

        program, hb_model = introduction(
            st.session_state.temp_folder, st.session_state.host)

        if hb_model:
            st.session_state.program = program
            st.session_state.hb_model = hb_model

    with tab1:
        if 'hb_model' not in st.session_state:
            st.error('Go back to the Introduction tab and load an HBJSON first.')
            return

        occupied_rooms = select(st.session_state.hb_model)

        validate(occupied_rooms, st.session_state.program, st.session_state.tolerance)

        hbjson_with_grids = sensor_grids(
            st.session_state.hb_model, occupied_rooms, st.session_state.temp_folder,
            st.session_state.host, st.session_state.tolerance)

        st.session_state.hbjson_path = hbjson_with_grids

    with tab2:
        if 'hbjson_path' not in st.session_state:
            st.error(
                'Go back to the Occupied Areas tab and add grids to selected'
                ' occupied areas.')
            return

    with tab3:
        pass


if __name__ == '__main__':
    main()

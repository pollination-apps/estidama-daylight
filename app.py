"""Estidama-daylight app."""

import tempfile
import streamlit as st

from pathlib import Path

from pollination_streamlit_io import get_host

from model import sensor_grids
from introduction import introduction
from occupied_area import select, validate
from simulation import simulation
from visualization import visualization
from result import result

st.set_page_config(
    page_title='Estidama Daylight',
    page_icon='https://app.pollination.cloud/favicon.ico',
    layout='centered',
    initial_sidebar_state='collapsed'
)


def main():

    tab0, tab1, tab2, tab3, tab4 = st.tabs(
        ["Introduction", "Occupied Areas", "Simulation", "Visualization", "Results"])

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

        if not hb_model:
            return
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

        if hbjson_with_grids:
            st.session_state.hbjson_path = hbjson_with_grids

    with tab2:
        if 'hbjson_path' not in st.session_state:
            st.error(
                'Go back to the Occupied Areas tab and add grids to the selected'
                ' occupied areas.')
            return

        job_url, api_client = simulation(
            st.session_state.temp_folder, st.session_state.hbjson_path)

        if job_url and api_client:
            st.session_state.job_url = job_url
            st.session_state.api_client = api_client

    with tab3:
        if 'job_url' not in st.session_state:
            st.error('Go back to the Simulation tab and submit the job.')
            return

        sim_dict, res_dict = visualization(st.session_state.job_url,
                                           st.session_state.api_client,
                                           st.session_state.temp_folder)
        if sim_dict and res_dict:
            st.session_state.sim_dict = sim_dict
            st.session_state.res_dict = res_dict

    with tab4:
        if 'res_dict' not in st.session_state:
            st.error('Go back to the Visualization tab and make sure all the'
                     ' six visualizations are loaded.')
            return

        result(st.session_state.sim_dict, st.session_state.res_dict)


if __name__ == '__main__':
    main()

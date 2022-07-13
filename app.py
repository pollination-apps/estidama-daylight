"""Pollination outdoor comfort app."""

import tempfile
import json
import streamlit as st
import pandas as pd

from enum import Enum
from pathlib import Path
from typing import List, Dict

from honeybee.model import Model as HBModel
from pollination_streamlit_io import get_host, get_hbjson

from estidama import OccupiedArea, get_occupied_rooms, select_program, validate_rooms
from web import show_model
from helper import get_hbjson_path


st.set_page_config(
    page_title='Estidama Daylight',
    page_icon='https://app.pollination.cloud/favicon.ico',
    layout='centered',
    initial_sidebar_state='collapsed'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba'
    '_pollination_brandmark-p-500.png',
    use_column_width=True
)


def main():

    st.title('Estidama Daylight')
    st.markdown('An app to check compliance for the Pearl Building Rating'
                ' System(PBRS) LBi-7 Daylight & Glare credit.'
                ' This app uses version 1.0, April 2010 of PBRS that can be'
                ' accessed'
                ' [here](https://pages.dmt.gov.ae/en/Urban-Planning/'
                'Pearl-Building-Rating-System). ')

    st.subheader('Definitions:')
    st.markdown(
        '1. Occupied area: Any internal space intended for sedentary occupancy.'
    )
    st.markdown(
        '2. Mixed-use-development: A development that includes more than occupancy type'
        ' - such as residential,'
        'commercial, industrial, public or semi-public - within the same building, project'
        'or site . The most common examples are a project with both commercial and'
        'residential uses, or commercial and industrial uses. '
    )

    # program
    program = select_program()

    # host
    host = get_host()
    if not host:
        host = 'web'

    # tempfolder
    if 'temp_folder' not in st.session_state:
        st.session_state.temp_folder = Path(tempfile.mkdtemp())

    data = get_hbjson('upload-model')

    if data:

        model_data = data['hbjson']
        hb_model = HBModel.from_dict(model_data)

        if len(hb_model.rooms) == 0:
            st.error('The uploaded model does not have any rooms (zones).')
            return

        if host == 'web':
            st.markdown('Visually inspect the model to see if this is what you'
                        ' wish to simulate.')

            hbjson_path = get_hbjson_path(st.session_state.temp_folder, hb_model)
            st.session_state.hbjson_path = hbjson_path

            show_model(hbjson_path)

        occupied_rooms = get_occupied_rooms(hb_model)

        validate_rooms(occupied_rooms, program)


if __name__ == '__main__':
    main()

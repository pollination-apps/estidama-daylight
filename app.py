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

from estidama import OccupiedArea, get_occupied_rooms
from web import show_model


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


class Programs(Enum):
    general = 'General'
    retail = 'Retail'
    residential = 'Residential'
    school = 'School'


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
    st.subheader('Program')
    st.markdown('The program type will determine the threshold for compliance analysis.')
    program = st.radio('Select program', options=[
        name.value for name in Programs])

    if program == 'Retail':
        st.warning('All retail areas are excluded from achieving this credit.'
                   ' If this is a mixed development project involving retail spaces,'
                   ' make sure to NOT include those zones in your selection of'
                   ' occupied areas.')

    st.session_state.program = program

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

        hbjson_path = st.session_state.temp_folder.joinpath(
            f'{hb_model.identifier}.hbjson')
        hbjson_path.write_text(json.dumps(hb_model.to_dict()))
        st.session_state.hbjson_path = hbjson_path

        if host == 'web':
            st.markdown('Visually inspect the model to see if this is what you'
                        ' wish to simulate.')
            show_model(hbjson_path)

        occupied_rooms = get_occupied_rooms(hb_model)

        col1, col2 = st.columns(2)

        with col1:
            checked = st.checkbox('Validate Occupied Areas')

        with col2:
            st.markdown(
                'The app will check each occupied area for windows and shades (manual glare control devices).')

        if checked:
            tolerance = st.number_input('Tolerance', value=0.01)

            table_dict = {'name': [], 'has_windows': [], 'has_shades': []}
            for room in occupied_rooms:
                occupied_area = OccupiedArea(room, tolerance)
                table_dict['name'].append(occupied_area.name)
                table_dict['has_windows'].append(occupied_area.has_windows)
                table_dict['has_shades'].append(occupied_area.has_shades)

            df = pd.DataFrame.from_dict(table_dict)
            st.write(df)


if __name__ == '__main__':
    main()

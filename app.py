"""Pollination outdoor comfort app."""

import tempfile
import streamlit as st
from pathlib import Path
from PIL import Image

from honeybee.model import Model as HBModel
from pollination_streamlit_io import get_host, get_hbjson

from estidama import get_occupied_rooms, select_program, validate_rooms,\
    relevant_definitions
from web import show_model
from helper import write_hbjson
from model import visualize_model_with_grids


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

    col1, col2 = st.columns([1, 5])

    with col1:
        image = Image.open('assets/images/estidama.png')
        st.image(image, width=100)

    with col2:
        st.title('Estidama Daylight')

    st.markdown('An app to check compliance for the Pearl Building Rating'
                ' System(PBRS) LBi-7 Daylight & Glare credit.'
                ' This app uses version 1.0, April 2010 of PBRS that can be'
                ' accessed'
                ' [here](https://pages.dmt.gov.ae/en/Urban-Planning/'
                'Pearl-Building-Rating-System). ')

    relevant_definitions()

    program = select_program()

    host = get_host()
    if not host:
        host = 'web'

    # TODO: Expose this on UI and get this info from CAD environment
    tolerance = 0.01

    if 'temp_folder' not in st.session_state:
        st.session_state.temp_folder = Path(tempfile.mkdtemp(prefix=f'{host}_'))

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

            hbjson_path = write_hbjson(st.session_state.temp_folder, hb_model)
            show_model(hbjson_path, st.session_state.temp_folder, key='model')

        occupied_rooms = get_occupied_rooms(hb_model)

        validate_rooms(occupied_rooms, program, tolerance)

        hbjson_with_grids = visualize_model_with_grids(
            hb_model, occupied_rooms, st.session_state.temp_folder, host, tolerance)

        st.session_state.hbjson_path = hbjson_with_grids


if __name__ == '__main__':
    main()

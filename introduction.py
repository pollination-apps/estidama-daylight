"""Introduction tab of the Estidama-daylight tab."""

import streamlit as st
from PIL import Image

from pathlib import Path
from typing import Tuple, Union

from honeybee.model import Model as HBModel
from pollination_streamlit_io import get_hbjson

from helper import write_hbjson
from web import show_model
from estidama import Program, ProgramName


def relevant_definitions() -> None:
    """Add relevant definitions from the Pearl Building Rating System."""

    st.subheader('Relevant Definitions:')
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


def select_program() -> Union[Program, None]:
    """Select and get the selected building program."""

    st.subheader('Select Program')
    st.markdown('The program type will determine the thresholds for compliance analysis.')

    name = st.radio('Select program', options=[name.value for name in ProgramName])

    if name == ProgramName.general.value:
        program = Program(ProgramName.general, 250, 0.5, 0.75,
                          'Install occupancy sensors in all rooms intended for'
                          ' individual occupancy, conferencing or meeting rooms'
                          ', open plan offices spaces and hallways or corridors.')

    elif name == ProgramName.retail.value:
        st.error('All retail areas are excluded from achieving this credit.'
                 ' If this is a mixed development project involving retail spaces,'
                 ' you can use "General" program. Also, make sure to NOT include'
                 ' those zones in your selection of occupied areas.')
        return

    elif name == ProgramName.residential.value:
        program = Program(ProgramName.residential, 200, 0.5, 0.75,
                          'Install occupancy sensors in all communal spaces'
                          ' of the building including hallways.')

    elif name == ProgramName.school.value:
        program = Program(ProgramName.school, 300, 0.75, 0.9,
                          'Install occupancy sensors in all rooms intended'
                          ' for individual occupancy, classrooms, open plan offices'
                          ' spaces and hallways.')

    return program


def introduction(host: str, target_folder: Path,
                 ) -> Union[Tuple[None, None], Tuple[Program, Union[HBModel, None]]]:
    """UI for the Introduction tab of the Estidama app.

    args:
        target_folder: Path to the folder where all the data will be written.
        host: A string conveying the environment inside which the app is running.

    returns:
        A tuple of two items;

        -   program: A Program object representing the building type selected by the user.

        -   hb_model: A Honeybee model object.
    """

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
    if not program:
        return None, None

    data = get_hbjson('upload-model')

    if data:

        model_data = data['hbjson']
        hb_model = HBModel.from_dict(model_data)

        if len(hb_model.rooms) == 0:
            st.error('The uploaded model does not have any rooms (zones).')
            return None, None

        if host == 'web':
            st.markdown('Visually inspect the model to see if this is what you'
                        ' wish to simulate.')

            hbjson_path = write_hbjson(target_folder, hb_model)
            show_model(hbjson_path, target_folder, key='model')
    else:
        hb_model = None

    return program, hb_model

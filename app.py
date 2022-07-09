"""Pollination outdoor comfort app."""

import tempfile
import json
import streamlit as st

from enum import Enum
from pathlib import Path
from typing import List, Dict
from pollination_streamlit_io import get_host, get_hbjson
from honeybee.model import Model as HBModel
from honeybee.room import Room

from helper import local_css
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


def checked_apertures_and_shades(rooms: List[Room]) -> List[Room]:

    checked_rooms = []
    for room in rooms:
        if room.exterior_aperture_area < 1:
            st.error(
                f'Zone {room.display_name} has not windows. If this is an occupied'
                ' area you wish to be part of this analysis then make sure'
                ' it has windows to outside.')
            return

        for face in room.faces:
            if face.apertures:
                for aperture in face.apertures:
                    if len(aperture.indoor_shades) == 0 and len(aperture.outdoor_shades) == 0:
                        st.warning(
                            f'Zone {room.display_name} has no internal or external glare control'
                            'devices.')
        checked_rooms.append(room)

    return checked_rooms


@st.cache(hash_funcs={
    HBModel: (lambda model: len(model.rooms)),
    Room: (lambda room: {'volume': room.volume,
           'area': room.floor_area, 'faces': len(room.faces)})},
          allow_output_mutation=True)
def get_room_dict(hb_model: HBModel) -> Dict[str, Room]:
    print("I am called")
    return {room.display_name.lower(): room for room in hb_model.rooms}


def get_occupied_rooms(room_dict: Dict[str, Room]) -> List[Room]:

    st.subheader('Choose Occupied Areas')

    if 'occupied_room_names' not in st.session_state:
        st.session_state.occupied_room_names = []
    if 'unique_occupied_room_names' not in st.session_state:
        st.session_state.unique_occupied_room_names = []

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input('Search areas')
        if name:
            searched_room_names = [room_name for room_name in room_dict
                                   if room_name.find(name) == 0]
        else:
            searched_room_names = []

    with col2:
        selected_room_names = st.multiselect('Select areas.',
                                             options=list(room_dict.keys()))

    staged_room_names: List[str] = searched_room_names + selected_room_names
    st.write('Areas staged to be added to the occupied areas.')
    st.write(staged_room_names)

    col3, col4 = st.columns(2)
    with col3:
        add_names = st.button('Add to occupied areas', key='add rooms',
                              help='Add staged areas to the occupied areas.')

    with col4:
        clear_names = st.button(
            'Clear occupied areas', key='clear occupied areas',
            help='Reset occupied areas.')

    if add_names:
        st.session_state.occupied_room_names.extend(staged_room_names)

    st.session_state.unique_occupied_room_names = list(
        set(st.session_state.occupied_room_names))

    if clear_names:
        st.session_state.occupied_room_names = []
        st.session_state.unique_occupied_room_names = []

    st.write(f'Occupied areas.')
    st.write(st.session_state.unique_occupied_room_names)

    return [room_dict[room_name] for room_name in
            st.session_state.unique_occupied_room_names]


def main():
    local_css('style.css')

    st.title('Estidama Daylight')
    st.markdown('An app to check compliance for the Pearl Building Rating'
                ' System(PBRS) LBi-7 Daylight & Glare credit.'
                ' This app uses version 1.0, April 2010 of PBRS that can be'
                ' accessed'
                ' [here](https://pages.dmt.gov.ae/en/Urban-Planning/'
                'Pearl-Building-Rating-System). ')

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

    # program
    st.subheader('Choose Program')
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

        hbjson_path = st.session_state.temp_folder.joinpath(
            f'{hb_model.identifier}.hbjson')
        hbjson_path.write_text(json.dumps(hb_model.to_dict()))
        st.session_state.hbjson_path = hbjson_path

        if host == 'web':
            st.markdown('Visually inspect the model to see if this is what you'
                        ' wish to simulate.')
            show_model(hbjson_path)

        room_dict = get_room_dict(hb_model)
        occupied_rooms = get_occupied_rooms(room_dict)


if __name__ == '__main__':
    main()

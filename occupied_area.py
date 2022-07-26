"""Occupied areas tab of the Estidama-daylight tab."""

import streamlit as st
import pandas as pd

from typing import List, Dict

from honeybee.model import Model as HBModel
from honeybee.room import Room

from introduction import Program
from estidama import OccupiedArea
from helper import hash_room


def get_room_dict(hb_model: HBModel) -> Dict[str, Room]:
    """Get a dictionary of Room name to Room structure."""
    return {room.display_name.lower(): room for room in hb_model.rooms}


@st.cache(max_entries=1, hash_funcs={Room: hash_room})
def set_session_state_vals(room_dict: Dict[str, Room]):
    """Set Session State variables.

    This functions is created to take advantage of the the cache hit and cache miss
    features of Streamlit. The function re-assigns two session state variables when
    the list of argument changes.

    args:
        room_dict: A dictionary of Honeybee room names to Honeybee room structure.
    """
    st.session_state.occupied_areas = []
    st.session_state.unique_occupied_areas = []


def select(hb_model: HBModel) -> List[Room]:
    """UI to Select Rooms in the Honeybee model to be treated as Estidama Occupied Areas.

    UI for Select. This function offers a UI for the users to select the Honeybee
    rooms to be treated as occupied ares in the context of this app.

    args:
        hb_model: A Honeybee model.

    returns:
        A list of Honeybee Room objects.
    """

    room_dict = get_room_dict(hb_model)

    st.subheader('Select')
    st.write('Either search using keywords or select the areas from'
             ' the dropdown menu and add the occupied areas. Here, examples of'
             ' a keyword are "meeting", "classroom", "corridor", etc.')

    set_session_state_vals(room_dict)

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input('Search areas')
        if name:
            searched_areas = [room_name for room_name in room_dict
                              if room_name.find(name) == 0]
        else:
            searched_areas = []

    with col2:
        chosen_areas = st.multiselect('Choose areas.',
                                      options=list(room_dict.keys()))

    staged_areas: List[str] = searched_areas + chosen_areas
    st.write('Areas staged to be added to the occupied areas.')
    st.write(staged_areas)

    col3, col4 = st.columns(2)
    with col3:
        add_areas = st.button('Add to occupied areas', key='add rooms',
                              help='Add staged areas to the occupied areas.')

    with col4:
        clear_areas = st.button(
            'Clear occupied areas', key='clear occupied areas',
            help='Reset occupied areas.')

    if add_areas:
        st.session_state.occupied_areas.extend(staged_areas)

    st.session_state.unique_occupied_areas = list(
        set(st.session_state.occupied_areas))

    if clear_areas:
        st.session_state.occupied_areas = []
        st.session_state.unique_occupied_areas = []

    st.write('Selected occupied areas')
    st.write(st.session_state.unique_occupied_areas)

    return [room_dict[room]
            for room in st.session_state.unique_occupied_areas]


def validate(rooms: List[Room], program: Program,
             tolerance: float) -> None:
    """UI to validate the Honeybee Rooms selected as occupied areas.

    UI for Validate. The function will validate the room by looking at their 
    apertures and shades. The function validates the following:

    1)  The room has apertures.

    2)  The room has external or internal shades.

    3)  If the room has internal shades, the width is less than four meters.

    args:
        rooms: A list of Honeybee rooms to be treated as Occupied areas.
        program : Selcted building program.
        tolerance: A float representing the tolerance.
    """

    st.subheader('Validate')
    col1, col2 = st.columns(2)

    with col1:
        validate = st.checkbox('Validate')

    with col2:
        st.markdown(
            'The app will check each occupied area for windows and shades'
            ' (manual glare control devices).')

    if validate:

        if not rooms:
            st.error('Add to occupied areas first.')
            return

        col3, col4 = st.columns(2)

        with col3:
            table_dict = {'Name': [], 'Windows': [], 'Shades': [], 'Warnings': []}
            details = {}
            for room in rooms:
                occupied_area = OccupiedArea(room, program, tolerance)
                table_dict['Name'].append(occupied_area.name)
                table_dict['Windows'].append(occupied_area.has_windows)
                table_dict['Shades'].append(occupied_area.has_shades)
                table_dict['Warnings'].append(len(occupied_area.warnings))
                details[occupied_area.name] = occupied_area.to_dict()

            df = pd.DataFrame.from_dict(table_dict)
            st.dataframe(df)

        with col4:
            name = st.text_input('Enter name to see warnings.')
            if name:
                if name not in details:
                    st.error('Invalid name')
                    return
                st.write(details[name])

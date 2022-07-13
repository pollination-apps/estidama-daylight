"""Module capturing estidama checks."""

from __future__ import annotations
import streamlit as st

from typing import List, Dict

from honeybee.room import Room
from honeybee.aperture import Aperture
from honeybee.shade import Shade
from honeybee.model import Model as HBModel


class OccupiedArea:
    def __init__(self, room: Room, tolerance) -> None:
        self._room = room
        self._name = self._room.display_name
        self._tolerance = tolerance
        self._has_windows = False
        self._has_shades = False
        self._windows = []
        self._status = []
        self._extract_windows()

    @property
    def name(self) -> str:
        return self._name

    @property
    def has_windows(self) -> bool:
        return self._has_windows

    @property
    def has_shades(self) -> bool:
        return self._has_shades

    def _extract_windows(self) -> None:
        if self._room.exterior_aperture_area == 0:
            return

        self._has_windows = True
        for face in self._room.faces:
            if face.apertures:
                for aperture in face.apertures:
                    window = Window(aperture, self._tolerance)
                    self._windows.append(window.to_dict())
                    self._status.append(window.status)

        if all(self._status):
            self._has_shades = True

    def to_dict(self) -> dict:
        return {
            'name': self._room.display_name,
            'has_windows': self._has_windows,
            'has_shades': self._has_shades,
            'windows': self._windows
        }


def check_shade_width(shade: Shade, tolerance: float) -> bool:
    left_edge, right_edge = shade.geometry.get_left_right_vertical_edges(tolerance)
    closest_point = right_edge.closest_point(left_edge.midpoint)
    distance = left_edge.midpoint.distance_to_point(closest_point)

    if distance <= 4.0:
        return True
    return False


class Window:
    def __init__(self, aperture: Aperture, tolerance: float) -> None:
        self._aperture = aperture
        self._tolerance = tolerance
        self._has_external_shades = False
        self._has_internal_shades = False
        self._status = False
        self._warning = None
        self._process_aperture()

    def _process_aperture(self):
        if len(self._aperture.outdoor_shades) > 0:
            self._has_external_shades = True

        if len(self._aperture.indoor_shades) > 0:
            width_check = [check_shade_width(shade, self._tolerance)
                           for shade in self._aperture.indoor_shades]
            if all(width_check):
                self._has_internal_shades = True
            else:
                self._warning = 'One or more of the internal shades are wider than 4 meters.'

        if self._has_external_shades or self._has_internal_shades:
            self._status = True

    @property
    def has_external_shades(self) -> bool:
        return self._has_external_shades

    @property
    def has_internal_shades(self) -> bool:
        return self._has_internal_shades

    @property
    def status(self) -> bool:
        return self._status

    def to_dict(self) -> dict:
        output = {
            'name': self._aperture.display_name,
            'has_external_shades': self._has_external_shades,
            'has_internal_shades': self._has_internal_shades,
            'warning': self._warning
        }
        if not self._warning:
            output.pop('warning')

        return output


def get_room_dict(hb_model: HBModel) -> Dict[str, Room]:
    return {room.display_name.lower(): room for room in hb_model.rooms}


@st.cache()
def set_session_state_vals(room_names: List[str]):
    """Set Session State variables.

    This functions is created to take advantage of the the cache hit and cache miss
    features of Streamlit. The function re-assigns two session state variables when
    the list of argument changes.

    args:
        room_names: A list of strings representing the room names in the Honeybee model.
    """
    st.session_state.occupied_areas = []
    st.session_state.unique_occupied_areas = []


def get_occupied_rooms(hb_model: HBModel) -> List[Room]:

    room_dict = get_room_dict(hb_model)

    set_session_state_vals(list(room_dict.keys()))

    st.subheader('Occupied Areas')
    st.write('Either search using keywords or select the areas from the dropdown menu and add the occupied areas. Here, examples of a keyword are "meeting", "classroom", "corridor", etc.')

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input('Search areas')
        if name:
            searched_areas = [room_name for room_name in room_dict
                              if room_name.find(name) == 0]
        else:
            searched_areas = []

    with col2:
        selected_areas = st.multiselect('Select areas.',
                                        options=list(room_dict.keys()))

    staged_areas: List[str] = searched_areas + selected_areas
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

    st.write('Chosen Occupied areas')
    st.write(st.session_state.unique_occupied_areas)

    return [room_dict[room]
            for room in st.session_state.unique_occupied_areas]

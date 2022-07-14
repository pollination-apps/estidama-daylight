"""Module capturing Estidama related objects and functions."""

from __future__ import annotations
import streamlit as st

import pandas as pd
from typing import List, Dict, Tuple
from enum import Enum

from honeybee.room import Room
from honeybee.aperture import Aperture
from honeybee.shade import Shade
from honeybee.model import Model as HBModel


class Program(Enum):
    """Building programs."""
    general = 'General'
    retail = 'Retail'
    residential = 'Residential'
    school = 'School'


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


def select_program() -> Program:
    """Select and get the selected building program."""

    st.subheader('Select Program')
    st.markdown('The program type will determine the threshold for compliance analysis.')

    program = st.radio('Select program', options=[
        name.value for name in Program])

    for member in Program.__members__.values():
        if member.value == program:
            program = member
            break

    if program == Program.retail:
        st.warning('All retail areas are excluded from achieving this credit.'
                   ' If this is a mixed development project involving retail spaces,'
                   ' make sure to NOT include those zones in your selection of'
                   ' occupied areas.')

    return program


class OccupiedArea:
    """The OccupiedArea object to be used in Estidama calculations.

    This object represents an area in design design that used for sedentary occupancy.
    All the Estidama analysis in the app is done on these objects only.

    args:
        room: A Honeybee room.
        program: Selected building program.
        tolerance: A float representing the tolerance.
    """

    def __init__(self, room: Room, program: Program, tolerance: float) -> None:
        self._room = room
        self._program = program
        self._tolerance = tolerance
        self._name = self._room.display_name
        self._has_windows = False
        self._has_shades = False
        self._windows = []
        self._warnings = []
        self._evaluate()

    @property
    def name(self) -> str:
        """Name of the OccupiedArea object."""
        return self._name

    @property
    def has_windows(self) -> bool:
        """Whether the OccupiedArea has any windows."""
        return self._has_windows

    @property
    def has_shades(self) -> bool:
        """Whether the OccupiedArea has any shades."""
        return self._has_shades

    @property
    def warnings(self) -> List[str]:
        """A list of warnings associated with the OccupiedArea."""
        return self._warnings

    def _evaluate(self) -> None:
        """Evaluate the Apertures and Shades in the Room added to the object.

        This function looks at all the aperture and in the Room added to the object
        and also the shades attached to those apertures. The functions the updates the
        property of this object based on this evaluation.
        """
        if self._room.exterior_aperture_area == 0:
            return

        self._has_windows = True

        has_shades = []
        for face in self._room.faces:
            if face.apertures:
                for aperture in face.apertures:
                    window = Window(aperture, self._program, self._tolerance)
                    self._windows.append(window.to_dict())
                    self._warnings.extend(window.warnings)
                    has_shades.append(window.has_shades)

        if all(has_shades):
            self._has_shades = True

    def to_dict(self) -> dict:
        """Get a dictionary representing certain properties of this object."""

        return {
            'name': self._room.display_name,
            'has_windows': self._has_windows,
            'has_shades': self._has_shades,
            'windows': self._windows
        }


def check_shade_width(shade: Shade, tolerance: float) -> Tuple[bool, str]:
    """Check that internal shade is not wider than 4 meters.

    This check comes from Estidama.

    args:
        shade: The Honeybee shade object to run this check on.
        tolerance: Tolerance for geometry calculation.

    returns:
        A tuple of two elements:

        -   True if the check passes. False otherwise.

        -   A warning message as a string.
    """
    geo = shade.geometry

    def _warning_1(shade: Shade):
        return False, f'Shade {shade.display_name} is wider than 4 meters.'

    def _warning_2(shade: Shade):
        return False, f'The app could not validate shade {shade.display_name}.'\
            ' Make sure the width is less than 4 meters wide.'

    if len(geo.vertices) <= 4:
        for line in geo.boundary_segments:
            dis = round(geo.center.distance_to_point(line.midpoint), 1)
            if dis > 2.0:
                return _warning_1(shade)
    else:
        if not shade.geometry.is_horizontal(tolerance):
            output = shade.geometry.get_left_right_vertical_edges(tolerance)
            if output:
                left_edge, right_edge = output
                closest_point = right_edge.closest_point(left_edge.midpoint)
                distance = left_edge.midpoint.distance_to_point(closest_point)
                if distance > 4.0:
                    return _warning_1(shade)
            else:
                return _warning_2(shade)
        else:
            return _warning_2(shade)

    return True, ''


class Window:
    """The Window object to be used in OccupiedArea object.

    This object resembles the Honeybee Aperture object in some aspects.

    args:
        aperture: A Honeybee Aperture object.
        program: Selected building program.
        tolerance: A float representing the tolerance.
    """

    def __init__(self, aperture: Aperture, program: Program, tolerance: float) -> None:
        self._aperture = aperture
        self._program = program
        self._tolerance = tolerance
        self._has_external_shades = False
        self._has_internal_shades = False
        self._has_shades = False
        self._warnings = []
        self._evaluate()

    @property
    def has_external_shades(self) -> bool:
        """Whether the Window has outdoor shades."""
        return self._has_external_shades

    @property
    def has_internal_shades(self) -> bool:
        """Whether the Window has indoor shades."""
        return self._has_internal_shades

    @property
    def has_shades(self) -> bool:
        """Whether the Window has shades."""
        return self._has_shades

    @property
    def warnings(self) -> List[str]:
        """All the warnings associated with this Window object."""
        return self._warnings

    def _evaluate(self):
        """Evaluate all the shades and collect warnings."""
        if len(self._aperture.outdoor_shades) > 0:
            self._has_external_shades = True

        if len(self._aperture.indoor_shades) > 0:
            checks, warnings = [], []

            for shade in self._aperture.indoor_shades:
                width_check, warning = check_shade_width(shade, self._tolerance)
                checks.append(width_check)
                warnings.append(warning)

            if all(checks):
                self._has_internal_shades = True
            else:
                for warning in warnings:
                    if warning:
                        self._warnings.append(warning)

        if self._has_external_shades or self._has_internal_shades:
            self._has_shades = True
        else:
            if self._program == Program.school:
                self._warnings.append(
                    'For the program type of "School" shades are required.')

    def to_dict(self) -> dict:
        """Get a dictionary representing certain properties of this object."""

        output = {
            'name': self._aperture.display_name,
            'has_external_shades': self._has_external_shades,
            'has_internal_shades': self._has_internal_shades,
            'warning': self._warnings
        }
        if not self._warnings:
            output.pop('warning')

        return output


def get_room_dict(hb_model: HBModel) -> Dict[str, Room]:
    """Get a dictionary of Room name to Room structure."""
    return {room.display_name.lower(): room for room in hb_model.rooms}


def hash_room(room: Room) -> dict:
    """Function to help Streamlit hash a Honeybee Room."""
    return {'name': room.display_name, 'volume': room.volume}


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


def get_occupied_rooms(hb_model: HBModel) -> List[Room]:
    """Get Rooms in the Honeybee model to be treated as Estidama Occupied Areas.

    This function offers a UI for the users to select the Honeybee rooms to be treated
    as occupied ares in the context of this app.

    args:
        hb_model: A Honeybee model.

    returns:
        A list of Honeybee Room objects.
    """

    room_dict = get_room_dict(hb_model)

    st.subheader('Select Occupied Areas')
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


def validate_rooms(rooms: List[Room], program: Program,
                   tolerance: float) -> None:
    """Validate the Honeybee Rooms selected as occupied areas.

    The function will validate the room by looking at their apertures and shades.

    args:
        rooms: A list of Honeybee rooms to be treated as Occupied areas.
        program : Selcted building program.
        tolerance: A float representing the tolerance.
    """

    st.subheader('Validate Occupied Areas')
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

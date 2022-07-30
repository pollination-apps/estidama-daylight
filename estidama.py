"""Module capturing Estidama objects."""

from __future__ import annotations

from enum import Enum
from typing import List, Tuple, Union

from honeybee.room import Room
from honeybee.aperture import Aperture
from honeybee.shade import Shade


class ProgramName(Enum):
    """Building programs."""
    general = 'General'
    retail = 'Retail'
    residential = 'Residential'
    school = 'School'


class Program:
    """The Program object to be used in Estidama calculations.

    args:
        name: Text string representing the name of the program.
        min_threshold: Minimum illuminance in lux to be received at the sensor point
            as required by Estidama.
        credit_1_threshold: Minimum percentage of compliant area to receive 1 credit
            from Estidama.
        credit_2_threshold: Minimum percentage of compliant area to receive 2 credits
            from Estidama.
    """

    def __init__(self, name: ProgramName, min_threshold: int, credit_1_threshold: float,
                 credit_2_threshold: float, occupancy_sensor_requirement: str) -> None:
        self._name = name
        self._min_threshold = min_threshold
        self._credit_1_threshold = credit_1_threshold
        self._credit_2_threshold = credit_2_threshold
        self._occupancy_sensor_requirement = occupancy_sensor_requirement

    @property
    def name(self) -> ProgramName:
        """Name of the program."""
        return self._name

    @property
    def min_threshold(self) -> int:
        """Minimum lux threshold."""
        return self._min_threshold

    @property
    def credit_1_threshold(self) -> float:
        return self._credit_1_threshold

    @property
    def credit_2_threshold(self) -> float:
        return self._credit_2_threshold

    @property
    def occupancy_sensor_requirement(self) -> str:
        return self._occupancy_sensor_requirement


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

    This check comes from Estidama. If the internal shade has four or less vertices
    the function finds the radial distance between the center of the face and the
    mid-points of each of the edges. If the shade is vertical, the function find the
    distance between the left most and the right most edges. The functions currently
    does not validate a more complex shade geometry.

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
            if self._program.name == ProgramName.school:
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


class PointInTime:
    """Object to represent Estidama simulation time as a point in time.

    This object represents a point in time at which a simulation will be run to see
    how much daylight the occupied area gets.

    args:
        month: Month as a number between 1 and 12.
        day: Day as a number between 1 and 31.
        hour: Hour as a number between 0 and 23.
    """

    def __init__(self, month: int, day: int, hour: int) -> None:
        self._month = month
        self._day = day
        self._hour = hour

    @property
    def month(self) -> int:
        return self._month

    @property
    def day(self) -> int:
        return self._day

    @property
    def hour(self) -> int:
        return self._hour

    def description(self) -> Union[None, str]:
        if self._day == 21:
            if self._month == 9:
                return 'Equinox'
            elif self._month == 6:
                return 'Summer Solstice'

    def __str__(self) -> str:
        return f'{self._month}_{self._day}_{self._hour}'

    def __repr__(self) -> str:
        return f'{self.description()} @ {self._hour}:00'


SIM_TIMES = [PointInTime(9, 21, 10), PointInTime(9, 21, 12), PointInTime(9, 21, 14),
             PointInTime(6, 21, 10), PointInTime(6, 21, 12), PointInTime(6, 21, 14)]

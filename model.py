"""A module capturing functions to edit the Honeybee model."""


import streamlit as st

from pathlib import Path
from typing import List, Union

from ladybug_geometry.geometry3d import Vector3D
from honeybee.room import Room
from honeybee.model import Model as HBModel
from honeybee_radiance.sensorgrid import SensorGrid
from honeybee.facetype import Floor
from honeybee_vtk.vtkjs.schema import SensorGridOptions

from pollination_streamlit_io import send_hbjson

from helper import write_hbjson
from web import show_model


def generate_room_grid(room: Room, grid_size: float, tolerance: float) -> SensorGrid:
    """Generate Sensorgrid from the floor of the room.

    args:
        room: A Honeybee Room object to generate SensorGrid for.
        grid_size: Distance between two adjacent Sensors.
        tolerance: A float representing the tolerance.

    Returns:
        A SensorGrid object.
    """
    for face in room.faces:
        if isinstance(face.type, Floor):
            floor = face
            break

    if not floor.normal.normalize().is_equivalent(Vector3D(0, 0, 1), tolerance):
        geo = floor.geometry.flip()
    else:
        geo = floor.geometry

    return SensorGrid.from_face3d(identifier=f'grid_{room.display_name}', faces=[
                                  geo], x_dim=grid_size, y_dim=grid_size, offset=0.762)


def add_sensor_grids(hb_model: HBModel, rooms: List[Room],
                     grid_size: float, tolerance: float) -> HBModel:
    """Add SensorGrids to a Honeybee model.

    This function will generate SensorGrids from the floor of each of the rooms. It will
    then add those grids to the copy of the Honeybee model provided to the function and
    will return the new model with grids added to it.

    args:
        hb_model: The Honeybee model to which SensorGrids are to be added.
        rooms: List of Honeybee rooms for which SensorGrids will be generated.
        grid_size: Distance between two adjacent Sensors.
        tolerance: A float representing the tolerance.

    returns:
        Honeybee model with SensorGrids added.
    """
    grids = [generate_room_grid(room, grid_size, tolerance) for room in rooms]

    model = hb_model.duplicate()
    model.properties.radiance.add_sensor_grids(grids)

    return model


def sensor_grids(hb_model: HBModel, rooms: List[Room],
                 target_folder, host: str,
                 tolerance: float) -> Union[Path, None]:
    """Add sensor grids to model and visualize it.

    UI for the Sensor Grids. The functions adds the sensor grids to the rooms in the
    model based on the rooms provided in the rooms parameter. The function also
    visualizes the model after the grids are added.

    args:
        hb_model: The Honeybee model to add grids it.
        room: List of Honeybee rooms for which grids will be generated.
        target_folder: Path to the folder where the HBJSON will be written.
        host: A string representing the environment the app is running inside.
        tolerance: A float representing the tolerance.

    returns:
        Path to the written HBJSON file with grids.
    """

    st.subheader("Sensor Grids")

    col1, col2 = st.columns(2)

    with col1:
        add_grids = st.checkbox('Add grids')

    with col2:
        st.markdown('Visually inspect the model to see if grids are added correctly.')

    if add_grids:

        if not rooms:
            st.error('Add to occupied areas first.')
            return

        grid_size = st.number_input('Select grid size', min_value=0.0, value=0.6)
        hb_model_with_grids = add_sensor_grids(hb_model, rooms, grid_size, tolerance)

        hbjson_with_grids = write_hbjson(target_folder, hb_model_with_grids,
                                         name=f'{hb_model_with_grids.identifier}_with_grids')

        if host == 'web':
            show_model(hbjson_with_grids, target_folder, key='model-grids',
                       grid_options=SensorGridOptions.Mesh, recreate_vtkjs=True)
        else:
            send_hbjson(key='model-grids', hbjson=hb_model_with_grids.to_dict())

        return hbjson_with_grids

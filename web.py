"""Functions to help visualize HBJSON in a browser."""


import streamlit as st
from pathlib import Path
from honeybee_vtk.model import Model as VTKModel
from pollination_streamlit_viewer import viewer
from honeybee_vtk.vtkjs.schema import SensorGridOptions


def write_vtkjs(hbjson_path: Path, grid_options: SensorGridOptions,
                target_folder: Path) -> Path:
    """Write a vtkjs file.

    args:
        hbjson_path: Path to the HBJSON file to be converted to vtkjs.
        grid_options: a SensorGridOptions object to indicate what to do with the grids
            found in HBJSON.
        target_folder: Path to the folder where the vtkjs file will be written.

    returns:
        Path to the written vtkjs file.
    """
    if not hbjson_path:
        return

    model = VTKModel.from_hbjson(hbjson_path.as_posix(), load_grids=grid_options)

    vtkjs_folder = target_folder.joinpath('vtkjs')

    if not vtkjs_folder.exists():
        vtkjs_folder.mkdir(parents=True, exist_ok=True)

    vtkjs_file = vtkjs_folder.joinpath(f'{hbjson_path.stem}.vtkjs')
    model.to_vtkjs(
        folder=vtkjs_folder.as_posix(),
        name=hbjson_path.stem
    )

    return vtkjs_file


def show_model(hbjson_path: Path, target_folder: Path, key: str = '3d_viewer',
               grid_options: SensorGridOptions = SensorGridOptions.Ignore,
               recreate_vtkjs: bool = False, subscribe: bool = False) -> None:
    """Show HBJSON in a browser.

    If not done already, this function will conver the HBJSON to vtkjs and write to
    a folder first. This is done so that the next time a call is made to visualize the
    same HBJSON, the function will simply visualize the already created vtkjs file 
    rather than creating it again.

    args:
        hbjson_path: Path to the HBJSON file you'd like to visualize in the browser.
        target_folder: Path to the folder where the vtkjs file will be written.
        key: A unique string for this instance of the viewer.
        grid_options: A SensorGridOptions object to indicate what to do with the grids
            found in HBJSON. Defaults to ignoring the grids found in the model.
            Alternatives are Mesh, Sensors, and RadialGrid.
        recreate_vtkjs: A boolean to indicate whether to recreate a new vtkjs
            file every time the function is called. Defaults to False. This is
            useful to show visualize changes being made to the model dynamically.
        subscribe: A boolean to subscribe or unsubscribe the VTKJS camera
             and renderer content. If you don't know what you're doing, it's best to
             keep this to False.
    """

    if recreate_vtkjs:
        vtkjs = write_vtkjs(hbjson_path, grid_options, target_folder)
    else:
        vtkjs_name = f'{hbjson_path.stem}_vtkjs'

        if vtkjs_name not in st.session_state:
            vtkjs = write_vtkjs(hbjson_path, grid_options, target_folder)
            st.session_state[vtkjs_name] = vtkjs
        else:
            vtkjs = st.session_state[vtkjs_name]

    viewer(content=vtkjs.read_bytes(),
           key=key, subscribe=subscribe)

"""Visualize HBJSON model in a web browser."""


import streamlit as st
from pathlib import Path
from honeybee_vtk.model import Model as VTKModel
from pollination_streamlit_viewer import viewer


def create_vtkjs(hbjson_path: Path) -> Path:
    if not hbjson_path:
        return

    model = VTKModel.from_hbjson(hbjson_path.as_posix())

    vtkjs_folder = st.session_state.temp_folder.joinpath('vtkjs')
    if not vtkjs_folder.exists():
        vtkjs_folder.mkdir(parents=True, exist_ok=True)

    vtkjs_file = vtkjs_folder.joinpath(f'{hbjson_path.stem}.vtkjs')
    if not vtkjs_file.is_file():
        model.to_vtkjs(
            folder=vtkjs_folder.as_posix(),
            name=hbjson_path.stem
        )

    return vtkjs_file


def show_model(hbjson_path: Path, key='3d_viewer', subscribe=False):
    """Render HBJSON."""

    vtkjs_name = f'{hbjson_path.stem}_vtkjs'

    if vtkjs_name not in st.session_state:
        vtkjs = create_vtkjs(hbjson_path)
        viewer(content=vtkjs.read_bytes(),
               key=key, subscribe=subscribe)
        st.session_state[vtkjs_name] = vtkjs
    else:
        viewer(content=st.session_state[vtkjs_name].read_bytes(),
               key=key, subscribe=subscribe)

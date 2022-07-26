"""Collection of Helper functions."""

import json
import streamlit as st
from pathlib import Path
from honeybee.model import Model as HBModel
from honeybee.room import Room


def write_hbjson(target_folder: Path, hb_model: HBModel, name: str = None) -> Path:
    """Write a Honeybee model as an HBJSOn file.

    args:
        target_folder: Path to the folder where the HBJSON file will be written.
        hb_model: The honeybee model to write as HBJSON.
        name: Name of the HBJSON file. Defaults to the identifier of the Honeybee model.

    returns:
        Path to the written HBJSON file.
    """
    if not name:
        hbjson_name = hb_model.identifier
    else:
        hbjson_name = name

    hbjson_path = target_folder.joinpath(f'{hbjson_name}.hbjson')
    hbjson_path.write_text(json.dumps(hb_model.to_dict()))

    return hbjson_path


def local_css(file_path: Path):
    """Inject a local CSS file in the Streamlit app.

    args:
        file_path: Path to the local CSS file.
    """

    with open(file_path.as_posix()) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def hash_model(hb_model: HBModel) -> dict:
    """Help Streamlit hash a Honeybee model object."""
    return {'name': hb_model.identifier, 'rooms': len(hb_model.rooms)}


def hash_room(room: Room) -> dict:
    """Help Streamlit hash a Honeybee room object."""
    return {'name': room.identifier, 'volume': room.volume, 'faces': len(room.faces)}

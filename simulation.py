"""Simulation tab of the Estidama daylight app."""


import streamlit as st
import time
import folium

from streamlit_folium import st_folium
from typing import Union, Tuple
from pathlib import Path
from streamlit.uploaded_file_manager import UploadedFile

from ladybug.epw import EPW
from ladybug.location import Location
from honeybee_radiance.lightsource.sky.cie import CIE
from pollination_streamlit.api.client import ApiClient
from pollination_streamlit.interactors import NewJob, Recipe

from estidama import PointInTime


def get_epw(epw_data: UploadedFile, target_folder: Path) -> Union[EPW, None]:
    """Get Ladybug EPW object from the Streamlit UploadedFile object.

    args:
        epw_data: A Streamlit UploadedFile object for an EPW file.
        target_folder: Path to the folder where the EPW file will be written.

    returns:
        A Ladybug EPW object for the uploaded EPW file.
    """
    epw_path = target_folder.joinpath('sample.epw')
    epw_path.write_bytes(epw_data.read())
    epw = EPW(epw_path)
    return epw


def cie_sky(latitude: float, longitude: float, month: int,
            day: int, hour: int, north_angle: int, ground_reflectance: float) -> str:
    """Get representation of the CIE sky as a string.

    args:
        location: A Ladybug location object.
        month: Month in a year. Acceptable numbers are between 1 to 12.
        day: Day in the month. Acceptable numbers are between 1 to 31.
        hour: Hour in the day. Acceptable numbers are between 0 to 23.
        north: The angle in degrees from positive Y.

    returns:
        A string representation of the CIE clear sky with sun.
    """
    cie = CIE.from_lat_long(latitude, longitude, 4, month,
                            day, hour, 0, north_angle, ground_reflectance)
    return f'cie -alt {cie.altitude} -az {cie.azimuth} -type 0 -g 0.2'


def create_job(hbjson_path: Path, api_client: ApiClient, owner: str, project: str,
               name: str, description: str, latitude: float, longitude: float,
               north_angle: int, ground_reflectance: float = 0.2) -> NewJob:
    """Create a Job to run a simulation on Pollination.

    args:
        hbjson_path: Path to the HBJSON file with grids.
        api_client: ApiClient object with Pollination API key.
        owner: Username as a string.
        project: Project name as a string.
        name: Name of the simulation as a string.
        description: Description of the simulation as a string.
        north: The angle in degrees from positive Y.
        epw: A Ladybug EPW object.

    returns:
        A NewJob object to schedule a simulation on Pollination.
    """

    recipe = Recipe('ladybug-tools', 'point-in-time-grid', 'latest', api_client)

    times = [PointInTime(6, 21, 10), PointInTime(6, 21, 12), PointInTime(
        6, 21, 14), PointInTime(9, 21, 14), PointInTime(9, 21, 12),
        PointInTime(9, 21, 10)]

    new_job = NewJob(owner, project, recipe, name=name,
                     description=description, client=api_client)

    arguments = []

    for point in times:
        argument = {}
        model_path = new_job.upload_artifact(hbjson_path, '.')
        argument['model'] = model_path
        argument['metric'] = 'illuminance'
        argument['radiance-parameters'] = '-ab 7'
        argument['sky'] = cie_sky(latitude, longitude, point.month,
                                  point.day, point.hour, north_angle, ground_reflectance)
        arguments.append(argument)
        argument['month_day_hour'] = point.as_string()

    new_job.arguments = arguments

    return new_job


def show_map(latitude: float, longitude: float, zoom: float) -> None:
    """Create a Folium map to show the selected location.

    args:
        latitude: Latitude of the selected location.
        longitude: Longitude of the selected location.
        zoom: Zoom level of the map.
    """

    m = folium.Map(location=[latitude, longitude], zoom_start=zoom)

    folium.Marker([latitude, longitude], popup="Liberty Bell",
                  tooltip='Selected location').add_to(m)

    st_folium(m, width=725)


def simulation(hbjson_path: Path) -> Union[Tuple[str, ApiClient],
                                           Tuple[None, None]]:
    """UI for the simulation tab of the Estidama app."""

    latitude = st.number_input('Latitude', value=24.453766,
                               help='Enter the latitude of the site.')
    longitude = st.number_input('Longitude', value=54.377375,
                                help='Enter the longitude of the site.')

    zoom = st.number_input('Zoom level', value=14)

    st.write('Visually check location on the map.')
    show_map(latitude, longitude, zoom)

    api_key = st.text_input('Pollination API key', type='password')
    owner = st.text_input('Project owner')
    project = st.text_input('Project name')
    study_name = st.text_input('Study name', value='Estidama-daylight')
    study_description = st.text_input(
        'Study description', value='PBRS LBi-7 Daylight & Glare compliance')

    north_angle = st.number_input('North angle', value=0, min_value=0, max_value=360)
    ground_reflectance = st.number_input(
        'Ground reflectance', value=0.2, help='Enter a decimal number to indicate'
        ' the percentage of light being reflected back by the ground.')

    submit = st.button('Submit')

    if submit:
        if not all([api_key, owner, project, latitude, longitude]):
            st.error('Make sure to fill all the fields first.')
            return None, None

        api_client = ApiClient(api_token=api_key)
        job = create_job(hbjson_path, api_client, owner, project,
                         study_name, study_description, latitude, longitude,
                         north_angle, ground_reflectance)

        running_job = job.create()

        time.sleep(2)
        job_url = f'https://app.pollination.cloud/{running_job.owner}/projects/{running_job.project}/jobs/{running_job.id}'
        st.success('Job submitted to Pollination. Move to the next tab.')
        return job_url, api_client

    return None, None

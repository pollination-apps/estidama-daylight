"""Module to schedule a job on Pollination."""


import streamlit as st
import time

from typing import Union
from pathlib import Path
from streamlit.uploaded_file_manager import UploadedFile

from ladybug.epw import EPW
from ladybug.location import Location
from honeybee_radiance.lightsource.sky.cie import CIE
from pollination_streamlit.api.client import ApiClient
from pollination_streamlit.interactors import NewJob, Recipe

from estidama import PointInTime


def get_epw(epw_data: UploadedFile, target_folder: Path) -> Union[EPW, None]:
    epw_path = target_folder.joinpath('sample.epw')
    epw_path.write_bytes(epw_data.read())
    epw = EPW(epw_path)
    return epw


def cie_sky(location: Location, month: int, day: int, hour: int, north: int) -> str:
    cie = CIE.from_location(location, month, day, hour, north_angle=north)
    return f'cie -alt {cie.altitude} -az {cie.azimuth} -type 0 -g 0.2'


def get_job(hbjson_path: Path, api_client: ApiClient, owner: str, project: str,
            study_name: str, study_description: str,
            north: int, epw: EPW) -> NewJob:

    recipe = Recipe('ladybug-tools', 'point-in-time-grid', 'latest', api_client)

    times = [PointInTime(6, 21, 10), PointInTime(6, 21, 12), PointInTime(
        6, 21, 14), PointInTime(9, 21, 10), PointInTime(9, 21, 12),
        PointInTime(9, 21, 14)]

    new_job = NewJob(owner, project, recipe, name=study_name,
                     description=study_description, client=api_client)

    arguments = []

    for point in times:
        argument = {}
        model_path = new_job.upload_artifact(hbjson_path, '.')
        argument['model'] = model_path
        argument['metric'] = 'illuminance'
        argument['radiance-parameters'] = '-ab 7'
        argument['sky'] = cie_sky(
            epw.location, point.month, point.day, point.hour, north)
        arguments.append(argument)

    new_job.arguments = arguments

    return new_job


def submit(target_folder: Path, hbjson_path: Path) -> Union[str, None]:

    st.subheader('Pollination Credentials')

    with st.form('pollination-request'):
        api_key = st.text_input('Enter Pollination API key', type='password')
        owner = st.text_input('Project owner')
        project = st.text_input('Project name')
        study_name = st.text_input('Study name', value='Estidama-daylight')
        study_description = st.text_input(
            'Study description', value='PBRS LBi-7 Daylight & Glare compliance')
        north = st.number_input('North angle', value=0, min_value=0, max_value=360)
        epw_data = st.file_uploader('Load Abu Dhabi EPW file', type='epw')

        submitted = st.form_submit_button('Submit')

        if submitted:
            if not all([api_key, owner, project, epw_data]):
                st.error('Make sure to fill all the fields first.')
                return

            api_client = ApiClient(api_token=api_key)
            epw = get_epw(epw_data, target_folder)
            job = get_job(hbjson_path, api_client, owner, project,
                          study_name, study_description, north, epw)

            running_job = job.create()

            time.sleep(2)
            job_url = f'https://app.pollination.cloud/{running_job.owner}/projects/{running_job.project}/jobs/{running_job.id}'
            st.success('Job submitted to Pollination. Move to the next tab.')
            return job_url

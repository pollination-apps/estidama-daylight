"""Visualization tab of the Estidama daylight app."""


import zipfile
import shutil
import streamlit as st

from enum import Enum
from typing import Dict, Tuple, Union
from pathlib import Path

from pollination_streamlit_viewer import viewer
from pollination_streamlit.api.client import ApiClient
from pollination_streamlit.interactors import Job
from queenbee.job.job import JobStatusEnum

from estidama import SIM_TIMES


class SimStatus(Enum):
    NOTSTARTED = 0
    INCOMPLETE = 1
    COMPLETE = 2
    FAILED = 3
    CANCELLED = 4


def request_status(job: Job) -> SimStatus:
    """Request status of a Job on Pollination.

    args:
        job: A Pollination Job object.

    returns:
        Status of a job on Pollination.
    """

    if job.status.status in [
            JobStatusEnum.pre_processing,
            JobStatusEnum.running,
            JobStatusEnum.created,
            JobStatusEnum.unknown]:
        return SimStatus.INCOMPLETE

    elif job.status.status == JobStatusEnum.failed:
        return SimStatus.FAILED

    elif job.status.status == JobStatusEnum.cancelled:
        return SimStatus.CANCELLED

    else:
        return SimStatus.COMPLETE


def create_job(job_url: str, api_client: ApiClient) -> Job:
    """Create a Job object from a job URL.

    args:
        job_url: Valid URL of a job on Pollination as a string.
        api_client: ApiClient object containing Pollination credentials.

    returns:
        A Pollination Job object created using the job_url and ApiClient.
    """
    url_split = job_url.split('/')
    job_id = url_split[-1]
    project = url_split[-3]
    owner = url_split[-5]

    return Job(owner, project, job_id, api_client)


def download(job: Job, target_folder: Path, folder_name: str,
             output_name: str) -> Dict[str, Path]:
    """Download output from a finished Job on Pollination and get a dictionary.

    args:
        job: A Pollination Job object.
        target_folder: Path to the folder where the output will be downloaded.
        folder_name: Name of the sub-folder that will be created at the target folder to
            write the output.
        output_name: Name of the output file as a string.

    returns:
        A dictionary with structure of run id to path to the folder where the output is
            downloaded for the run.
    """
    viz_folder = target_folder.joinpath(folder_name)

    if not viz_folder.exists():
        viz_folder.mkdir(parents=True, exist_ok=True)
    else:
        shutil.rmtree(viz_folder)
        viz_folder.mkdir(parents=True, exist_ok=True)

    runs = job.runs

    output = {}

    for count, run in enumerate(runs):
        res_zip = run.download_zipped_output(output_name)
        file_path = viz_folder.joinpath(f'{count}')
        with zipfile.ZipFile(res_zip) as zip_folder:
            zip_folder.extractall(file_path)
        output[run.id] = file_path

    return output


@st.cache
def generate_dicts(job: Job, target_folder: Path) -> Tuple[Dict[str, str],
                                                           Dict[str, Path],
                                                           Dict[str, Path]]:
    """Generate dictionaries to use later.

    This function will download 'visualization' and 'results' output from a finished
    job on pollination in the target folder. The function will then return dictionaries
    to tie the simulation time, run id and output results.

    args:
        job: A Pollination job object for a job finished on Pollination.
        target_folder: Path to the target folder where outputs from the finished job
            will be downloaded.

    returns:
        A tuple of three items;

        -   sim_dict: A dictionary that ties simulation_times with the run id.

        -   viz_dict: A dictionary that ties run id with the path to the
                folder where the .vtkjs file is downloaded.

        -   res_file_dict: A dictionary that ties run id with the path to the folder
                where the result files are downloaded.
    """

    df = job.runs_dataframe.dataframe
    sim_ids = list(df.index.values)
    sim_times = list(df['month_day_hour'].values)
    sim_dict = dict(zip(sim_times, sim_ids))

    viz_dict = download(job, target_folder, 'viz', 'visualization')

    res_file_dict = download(job, target_folder, 'result', 'results')

    return sim_dict, viz_dict, res_file_dict


def visualization(job_url: str,
                  api_client: ApiClient,
                  target_folder: Path) -> Tuple[Union[None, Dict[str, str]],
                                                Union[None, Dict[str, Path]]]:
    """UI of visualization tab of the Estidama-daylight app.

    args:
        job_url: Valid URL of a job on Pollination as a string.
        api_client: ApiClient object containing Pollination credentials.
        target_folder: Path to the target folder where outputs from the finished job
            will be downloaded.

    returns:
        A tuple of two items;

        -   sim_dict: A dictionary that ties simulation_times with the run id.

        -   res_file_dict: A dictionary that ties run id with the path to the folder
                where the result files are downloaded.
    """

    job = create_job(job_url, api_client)

    if request_status(job) != SimStatus.COMPLETE:
        clicked = st.button('Refresh to download results')
        if clicked:
            status = request_status(job)
            st.warning(f'Simulation is {status.name}.')

    else:
        sim_dict, viz_dict, res_file_dict = generate_dicts(job, target_folder)

        st.write('See how much daylight the occupied areas receive on selected points'
                 ' in time during the year.')

        col0, col1 = st.columns(2)

        with col0:
            for sim_time in SIM_TIMES[:3]:
                print(sim_time.as_string())
                id = sim_dict[sim_time.as_string()]
                viz = viz_dict[id].joinpath('point_in_time.vtkjs')
                st.write(
                    f'Daylight levels on {sim_time.description()} @ {sim_time.hour}:00')
                viewer(key=f'{sim_time.as_string()}_viewer',
                       content=viz.read_bytes(), style={'height': '344px'})

        with col1:
            for sim_time in SIM_TIMES[3:]:
                id = sim_dict[sim_time.as_string()]
                viz = viz_dict[id].joinpath('point_in_time.vtkjs')
                st.write(
                    f'Daylight levels on Summer {sim_time.description()} @ {sim_time.hour}:00')
                viewer(key=f'{sim_time.as_string()}_viewer',
                       content=viz.read_bytes(), style={'height': '344px'})

        st.write('Go to the next tab to see the results.')

        return sim_dict, res_file_dict

    return None, None

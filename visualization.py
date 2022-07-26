"""Visualization tab of the Estidama daylight app."""


import zipfile
import shutil
import streamlit as st

from enum import Enum
from typing import List, Dict, Tuple, Union
from pathlib import Path

from pollination_streamlit_viewer import viewer
from pollination_streamlit.api.client import ApiClient
from pollination_streamlit.interactors import Job
from queenbee.job.job import JobStatusEnum


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
             output_name: str, extension: str) -> Dict[str, List[Path]]:
    """Download output from a finished Job on Pollination and get a dictionary.

    args:
        job: A Pollination Job object.
        target_folder: Path to the folder where the output will be downloaded.
        folder_name: Name of the sub-folder that will be created at the target folder to
            write the output.
        output_name: Name of the output file as a string.
        extension: The extension of the files you are interested in from the downloaded
            output files. Examples are; txt, res. Make sure to name the extension
            without the '.'.

    returns:
        A dictionary with structure of run id to a list of paths to the files with the
            requested extension.
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
        output[run.id] = list(file_path.glob(f'**/*.{extension}'))

    return output


def percentage_complied(res: Path, threshold: float) -> float:
    """Calculate the percentage of sensor points meeting the threshold.

    args:
        res: Path to the result file
        threshold: A number. A sensor point receiving illuminance greater than or equal
            to this number will be considered compliant.

    returns:
        Percentage of the sensor points complying with the threshold.
    """

    check = []
    with open(res.as_posix(), 'r') as file:
        for row in file:
            num = float(row.rstrip('\n'))
            if num >= threshold:
                check.append(True)
            else:
                check.append(False)

    return check.count(True)*100 / len(check)


@st.cache
def generate_dicts(job: Job, target_folder: Path) -> Tuple[Dict[str, str],
                                                           Dict[str, List[Path]],
                                                           Dict[str, List[Path]]]:
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

        -   viz_dict: A dictionary that ties run id with downloaded .vtkjs files for
                visualization.

        -   res_dict: A dictionary that ties run id with downloaded result files.
    """

    df = job.runs_dataframe.dataframe
    sim_ids = list(df.index.values)
    sim_times = list(df['month_day_hour'].values)
    sim_dict = dict(zip(sim_times, sim_ids))

    viz_dict = download(job, target_folder, 'viz', 'visualization', 'vtkjs')

    res_dict = download(job, target_folder, 'result', 'results', 'res')

    return sim_dict, viz_dict, res_dict


def visualization(job_url: str,
                  api_client: ApiClient,
                  target_folder: Path) -> Tuple[Union[None, Dict[str, str]],
                                                Union[None, Dict[str, List[Path]]]]:
    """UI of visualization tab of the Estidama-daylight app.

    args:
        job_url: Valid URL of a job on Pollination as a string.
        api_client: ApiClient object containing Pollination credentials.
        target_folder: Path to the target folder where outputs from the finished job
            will be downloaded.

    returns:
        A tuple of two items;

        -   sim_dict: A dictionary that ties simulation_times with the run id.

        -   res_dict: A dictionary that ties run id with downloaded result files.
    """

    job = create_job(job_url, api_client)

    if request_status(job) != SimStatus.COMPLETE:
        clicked = st.button('Refresh to download results')
        if clicked:
            status = request_status(job)
            st.warning(f'Simulation is {status.name}.')

    else:
        sim_dict, viz_dict, res_dict = generate_dicts(job, target_folder)

        st.write('See how much daylight the occupied areas receive on selected points'
                 ' in time during the year.')

        col0, col1 = st.columns(2)

        with col0:
            # case-0
            case_0_id = sim_dict['9_21_10']
            case_0_viz = viz_dict[case_0_id]

            st.write('Daylight levels On Equinox @ 10:00')
            viewer(key='case_0', content=case_0_viz[0].read_bytes())

            # case-1
            case_1_id = sim_dict['9_21_12']
            case_1_viz = viz_dict[case_1_id]

            st.write('Daylight levels On Equinox @ 12:00')
            viewer(key='case_1', content=case_1_viz[0].read_bytes())

            # case-2
            case_2_id = sim_dict['9_21_14']
            case_2_viz = viz_dict[case_2_id]

            st.write('Daylight levels On Equinox @ 14:00')
            viewer(key='case_2', content=case_2_viz[0].read_bytes())

        with col1:
            # case-3
            case_3_id = sim_dict['6_21_10']
            case_3_viz = viz_dict[case_3_id]

            st.write('Daylight levels On Summer Solstice @ 10:00')
            viewer(key='case_3', content=case_3_viz[0].read_bytes())

            # case-4
            case_4_id = sim_dict['6_21_12']
            case_4_viz = viz_dict[case_4_id]

            st.write('Daylight levels On Summer Solstice @ 12:00')
            viewer(key='case_4', content=case_4_viz[0].read_bytes())

            # case-5
            case_5_id = sim_dict['6_21_14']
            case_5_viz = viz_dict[case_5_id]

            st.write('Daylight levels On Summer Solstice @ 14:00')
            viewer(key='case_5', content=case_5_viz[0].read_bytes())

        st.write('Go to the next tab to see the results.')

        return sim_dict, res_dict

    return None, None

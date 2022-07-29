"""Result tab of the Estidama daylight app."""

import streamlit as st
import pandas as pd

from statistics import mean
from pathlib import Path
from typing import Dict, List
from honeybee.room import Room
from estidama import Program
import plotly.graph_objects as go


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

    return check.count(True) / len(check)


def figure_height(occupied_rooms: List[Room]) -> float:
    """Calculate the height of the figure in pixels."""

    header_row_1_2 = 28
    header_row_3 = 62.2
    table_row = 20
    table_last_row = 31
    extra = 5

    return header_row_1_2*2+header_row_3+table_row*len(occupied_rooms)+table_last_row+extra


def additional_notes(program: Program) -> None:

    st.subheader('Additional notes')
    st.write('Make sure to also do the following;')
    st.write('1. Install daylight sensors to light fittings that receive'
             ' sufficient daylight illuminance.')
    st.write('2. If fixed glare control devices (shades) are not provide to'
             ' any of the windows, demonstrate that automated glare control devices'
             ' are provide and they are connected to the building management system.')
    st.write(f'3. {program.occupancy_sensor_requirement}')


def simulation_parameters(program: Program) -> None:

    st.subheader('Simulation parameters')
    st.write('As per Estidama requirements following parameters were used to conduct'
             ' this simulation;')

    st.write('1. CIE Clear sky was used.')
    st.write('2. 7 ambient bounces were used to calculate the diffused daylight'
             ' contribution.')
    st.write('3. Grid was placed at 0.762 meters above the floor.')
    st.write(f'4. {program.min_threshold} lux was used as the minium illuminance'
             ' to be received at the sensor point for it to qualify under this credit.')


def result(program: Program, occupied_rooms: List[Room],
           sim_dict: Dict[str, str], res_file_dict: Dict[str, List[Path]]):
    """UI to visualize the results of the simulation."""

    index_tuple = [(room.display_name, room.floor_area) for room in occupied_rooms]
    multi_index = pd.MultiIndex.from_tuples(index_tuple, names=['names', 'areas'])

    cols = pd.MultiIndex.from_tuples(
        [
            ("", "", "Occupied Area Names"),
            ("", "", "Total Area"),

            ("Equinox", "10am", "Compliant Area"),

            ("Equinox", "12pm", "Compliant Area"),

            ("Equinox", "2pm", "Compliant Area"),

            ("Solstice", "10am", "Compliant Area"),

            ("Solstice", "12pm", "Compliant Area"),

            ("Solstice", "2pm", "Compliant Area"),
            ("", "", "Average Compliant Area")
        ]

    )
    data = [
        [100, 300, 900, 400, 33, 23, 222, 100, 300, ], [
            200, 500, 300, 600, 33, 45, 44, 200, 500]]

    data = {
        'names': [],
        'areas': [],
        '9_21_10': [],
        '9_21_12': [],
        '9_21_14': [],
        '6_21_10': [],
        '6_21_12': [],
        '6_21_14': [],
        'average': []
    }

    sim_times = ['9_21_10', '9_21_12', '9_21_14', '6_21_10', '6_21_12', '6_21_14']

    area = 0
    average_area = 0
    for i in range(len(occupied_rooms)+1):
        if i < len(occupied_rooms):
            room = occupied_rooms[i]
            data['names'].append(room.display_name)
            data['areas'].append(room.floor_area)
            area += room.floor_area

            compliant_areas = []
            file_name = f'grid_{room.display_name}.res'
            for sim_time in sim_times:
                sim_id = sim_dict[sim_time]
                res_file_path = res_file_dict[sim_id].joinpath(file_name)
                compliant_area = room.floor_area*percentage_complied(
                    res_file_path, program.min_threshold)
                data[sim_time].append(compliant_area)
                compliant_areas.append(compliant_area)

            average_compliant_area = mean(compliant_areas)
            data['average'].append(average_compliant_area)
            average_area += average_compliant_area
        else:
            data['names'].append('<b>Total</b>')
            data['areas'].append(f'<b>{area}</b>')
            for sim_time in sim_times:
                data[sim_time].append('')
            data['average'].append(f'<b>{average_area}</b>')

    data_df = pd.DataFrame.from_dict(data)

    df = pd.DataFrame(data, columns=cols, index=multi_index)

    fig = go.Figure(
        data=[go.Table(
            header=dict(values=list(df.columns),
                        align='left'),
            cells=dict(values=[data_df['names'], data_df['areas'], data_df['9_21_10'],
                               data_df['9_21_12'], data_df['9_21_14'], data_df['6_21_10'],
                               data_df['6_21_12'], data_df['6_21_14'], data_df['average']],
                       align='left'),
            columnwidth=[10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]

        )
        ]
    )

    fig.update_layout(margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
                      height=figure_height(occupied_rooms))

    simulation_parameters(program)

    st.subheader('Simulation results')
    st.plotly_chart(fig, use_container_width=True)

    compliant_area_percentage = average_area / area

    if compliant_area_percentage >= program.credit_2_threshold:
        st.success(f'{compliant_area_percentage*100}% area complies with the'
                   ' requirements. Therefore, 2 Credit points can be claimed.')
        additional_notes(program)
        st.balloons()

    elif compliant_area_percentage >= program.credit_1_threshold:
        st.success(f'{compliant_area_percentage*100}% area complies with the'
                   ' requirements. Therefore, 1 Credit point can be claimed.')
        additional_notes(program)
        st.balloons()
    else:
        st.write(
            f'Only {compliant_area_percentage*100}% area complies with the requirements.'
            ' Hence, no credit point can be claimed.')

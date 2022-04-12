"""
Scripts related to dataset PhysioNet Challenge 2012.

For more information please refer to:
https://github.com/WenjieDu/Time_Series_Database/tree/main/datasets/PhysioNet-2012

"""

# Created by Wenjie Du <wenjay.du@gmail.com>
# License: GLP-v3

import os

import pandas as pd


def load_physionet2012(local_path):
    """ Load dataset PhysioNet Challenge 2012, which is a time-series classification dataset.

    Parameters
    ----------
    local_path : str,
        The local path of dir saving the raw data of PhysioNet Challenge 2012.

    Returns
    -------
    data : dict
        A dictionary contains X and y:
            X : pandas.DataFrame,
                Time-series feature vectors.
            y : pandas.Series,
                Classification labels.

    Notes
    -----
    The preprocessing workflow is the same with the one used in paper :cite:`du2022SAITS`.
    All samples contain 48 time steps. Truncated if the sample has more than 48 steps. Padded if
    the sample has less than 48 steps. Static features such as 'Age', 'Gender', 'ICUType', 'Height',
    are removed. Column 'Time' also gets removed. Following 12 samples are dropped because of containing
    no time-series information at all: 147514, 142731, 145611, 140501, 155655, 143656, 156254, 150309,
    140936, 141264, 150649, 142998.
    """

    time_series_measurements_dir = ['set-a', 'set-b', 'set-c']
    outcome_files = ['Outcomes-a.txt', 'Outcomes-b.txt', 'Outcomes-c.txt']

    outcome_collector = []
    for o_ in outcome_files:
        outcome_file_path = os.path.join(local_path, o_)
        outcome = pd.read_csv(outcome_file_path).set_index('RecordID')['In-hospital_death']
        outcome_collector.append(outcome)
    y = pd.concat(outcome_collector)

    all_recordID = []
    df_collector = []

    # iterate over all samples
    for m_ in time_series_measurements_dir:
        raw_data_dir = os.path.join(local_path, m_)
        for filename in os.listdir(raw_data_dir):
            recordID = int(filename.split('.txt')[0])
            with open(os.path.join(raw_data_dir, filename), 'r') as f:
                df_temp = pd.read_csv(f)
            df_temp['Time'] = df_temp['Time'].apply(lambda x: int(x.split(':')[0]))
            df_temp = df_temp.pivot_table('Value', 'Time', 'Parameter')
            df_temp = df_temp.reset_index()  # take Time from index as a col
            if len(df_temp) == 1:
                print(f'Pass {recordID}, because its len==1, having no time series data')
                continue
            all_recordID.append(recordID)  # only count valid recordID

            if df_temp.shape[0] != 48:
                missing = list(set(range(0, 48)).difference(set(df_temp['Time'])))
                missing_part = pd.DataFrame({'Time': missing})
                df_temp = df_temp.append(missing_part, ignore_index=False, sort=False)
                df_temp = df_temp.set_index('Time').sort_index().reset_index()

            df_temp = df_temp.iloc[:48]  # only take 48 hours, some samples may have more records, like 49 hours
            df_temp['RecordID'] = recordID
            df_temp['Age'] = df_temp.loc[0, 'Age']
            df_temp['Height'] = df_temp.loc[0, 'Height']
            df_collector.append(df_temp)

    df = pd.concat(df_collector, sort=True)
    df = df.drop(['Age', 'Gender', 'ICUType', 'Height'], axis=1)
    df = df.reset_index(drop=True)
    X = df.drop('Time', axis=1)  # we don't need Time column
    data = {
        'X': X,
        'y': y
    }
    return data
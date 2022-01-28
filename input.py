"""parse YAML config file and read charged off table and prepay table from input
"""

import pandas as pd
import yaml
import os

curr_dir = os.path.dirname(__file__)
config_file = os.path.join(curr_dir, 'config.yaml')
with open(config_file, 'r') as f:
    settings = yaml.load(f, Loader=yaml.FullLoader)

    input = settings['input']
    filename = input['filename']
    # input file has to be an Excel file
    assert filename.endswith('.xlsx'), 'Input file has to be an Excel file with Charge Off sheet and Prepay sheet.'
    charge_off_sheet_name = input['default_sheetname']
    prepay_sheet_name = input['prepay_sheetname']

# read charged off and prepay tables to pandas DataFrames
CHARGED_OFF = pd.read_excel(filename, sheet_name=charge_off_sheet_name)
PREPAY = pd.read_excel(filename, sheet_name=prepay_sheet_name)
# remove empty columns
PREPAY.drop(list(PREPAY.filter(regex='Unnamed')), axis=1, inplace=True)
# drop first row: 12M, 18M, 24M ...
PREPAY = PREPAY.iloc[1:, :]

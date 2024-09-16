import pandas as pd

# Load the Tmax dataset
file_path_tmax_new = '/mnt/data/interpolated_tmax_1980-2017_elevation_band (2).xlsx'
tmax_new_df = pd.read_excel(file_path_tmax_new)

# Check for null values in the Tmax dataset
null_values_tmax = tmax_new_df.isnull().sum().sum()

if null_values_tmax > 0:
    # Find the columns (stations) with null values
    null_columns_tmax = tmax_new_df.columns[tmax_new_df.isnull().any()].tolist()

    # Find the indices of rows with null values
    null_indices_tmax = tmax_new_df[tmax_new_df.isnull().any(axis=1)].index.tolist()

    # Create a dictionary with stations as keys and list of indices with null values as values
    null_tmax_dict = {col: tmax_new_df[tmax_new_df[col].isnull()].index.tolist() for col in null_columns_tmax}

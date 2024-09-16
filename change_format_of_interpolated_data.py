'''
Algorithm
Read the data
transpose
for each station in row, find the station in the row of another sheet
get the columns and values from the another sheet
concat at the required position
'''
import pandas as pd

data_path = r'C:\Users\Acer\Desktop\GIS\Data_interpolated\Tmax_Nepal\Merged_Tmax_Data_2013_2023.xlsx'
station_details_path = r'C:\Users\Acer\Desktop\Gridded data\DHM-2018-2023\merged_1st&2nd-DHM-102 wecs.xlsx'

# Load the data
df = pd.read_excel(data_path)
details_df = pd.read_excel(station_details_path, sheet_name='Stations_final')

# Melt the data to have one row per station-date combination
df_melted = df.melt(id_vars=['Date'], var_name='Station', value_name='Temperature')

# Convert the 'Station' column to string type
df_melted['Station'] = df_melted['Station'].astype(str)

# Convert the 'Date' column to datetime type
df_melted['Date'] = pd.to_datetime(df_melted['Date'])

# Pivot the data to have dates as columns and stations as rows
df_pivoted = df_melted.pivot(index='Station', columns='Date', values='Temperature').reset_index()

# Rename the date columns to the format Jan_1_2018
def format_date_column(date):
    if date != 'Station':
        return date.strftime('%b_%d_%Y')
    return date

new_column_names = {date: format_date_column(date) for date in df_pivoted.columns}
df_pivoted.rename(columns=new_column_names, inplace=True)

# Convert the 'Station' column to string type (in case it's not already)
details_df['Station'] = details_df['Station'].astype(str)

# Merge the station details with the pivoted data
final_df = pd.merge(details_df, df_pivoted, on='Station', how='inner')

# Save the transformed data to a new Excel file
final_df.to_excel(r'C:\Users\Acer\Desktop\GIS\Data_interpolated\Tmax_Nepal\transformed_tmax_data_2013_2023.xlsx', index=False)
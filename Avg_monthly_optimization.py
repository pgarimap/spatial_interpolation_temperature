'''Code for average monthly (for x years) temperature  for 12 months
Initially, created for 2018-2019
Algorithm:
1.Read the interpolated file
2. Extract data for 2018-2019
3. An empty dataframe
3. For each station:
    calculate the avg temperature for each month
    write to the empty dataframe
'''
import pandas as pd

# Specify the file path
file_path = r'C:\Users\Acer\Desktop\GIS\Data_interpolated\Tmax_Final\Final_tmax_2013_2023.csv'

# Read the Excel file into a DataFrame
df = pd.read_csv(file_path)

# Filter data for the specified range of years
start_year = 2013
end_year = 2023

# Extract the columns representing dates within the specified range
date_columns = [col for col in df.columns if any(str(year) in col for year in range(start_year, end_year + 1))]

# Filter the columns to include only station details and the required date columns
station_details_columns = ['Station', 'lat', 'lon', 'elevation', 'category']
df_filtered = df[station_details_columns + date_columns]

# Convert the wide format to long format for easier manipulation
df_long = pd.melt(df_filtered, id_vars=station_details_columns, var_name='Date', value_name='Temperature')

# Replace underscores with hyphens in the 'Date' column to match the correct datetime format
df_long['Date'] = df_long['Date'].str.replace('_', '-')

# Convert 'Date' column to datetime format
df_long['Date'] = pd.to_datetime(df_long['Date'], format='%b-%d-%Y', errors='coerce')

# Drop rows with invalid 'Date' values
df_long.dropna(subset=['Date'], inplace=True)

# Extract month and year from 'Date' and add as new columns
df_long['Month'] = df_long['Date'].dt.month
df_long['Year'] = df_long['Date'].dt.year

# Group by 'Station', 'lat', 'lon', 'elevation', 'category', and 'Month' and calculate the mean temperature for each station
monthly_avg_temperatures = df_long.groupby(['Station', 'lat', 'lon', 'elevation', 'category', 'Month'])['Temperature'].mean().unstack()

# Check the intermediate result to ensure it has the correct structure
print(monthly_avg_temperatures.head())

# Rename columns to month names (if the pivoting was successful)
if not monthly_avg_temperatures.empty:
    monthly_avg_temperatures.columns = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    # Reset index to make 'Station' and other details regular columns
    monthly_avg_temperatures = monthly_avg_temperatures.reset_index()
else:
    print("Pivoting resulted in an empty DataFrame. Please check the data and column names.")

# Export the result to a new Excel file
output_file_path = r'C:\Users\Acer\Desktop\GIS\Data_interpolated\Tmax_Final\Final_tmaxavgmon_2013_2023.csv'
monthly_avg_temperatures.to_csv(output_file_path, index=False)

# Display the result
print(monthly_avg_temperatures)
import pandas as pd

# Load the final transformed CSV file
transformed_file_path = r'C:\Users\Acer\Desktop\GIS\ARCPY\ERA\Datafinal_CDS\ERA5_India_China_daily_min_temp_transformed.csv' #change the filepath here
df = pd.read_csv(transformed_file_path)

# Load the seasonal lapse rates CSV file
lapse_rates_file_path = r'C:\Users\Acer\Desktop\GIS\ARCPY\ERA\Datafinal_CDS\seasonal_lapse_rates_mintemp_India_China.csv'  #change the file path here
lapse_rates_df = pd.read_csv(lapse_rates_file_path)

# Ensure date columns are in datetime format and melt the dataframe to long format
df_melted = df.melt(id_vars=['Station', 'lat', 'lon', 'elevation', 'geopotential_height', 'category'], var_name='date',
                    value_name='temp')
df_melted['date'] = pd.to_datetime(df_melted['date'])

# Extract month from date
df_melted['month'] = df_melted['date'].dt.month


# Function to categorize months into seasons
def categorize_season(month):
    if month in [3, 4, 5]:
        return 'Pre-Monsoon (MAM)'
    elif month in [6, 7, 8, 9]:
        return 'Monsoon (JJAS)'
    elif month in [10, 11]:
        return 'Post-Monsoon (ON)'
    else:
        return 'Winter (DJF)'


# Add season column
df_melted['season'] = df_melted['month'].apply(categorize_season)


# Function to apply bias correction
def apply_bias_correction(row, lapse_rates_df):
    category = row['category']
    season = row['season']
    elevation = row['elevation']
    geopotential_height = row['geopotential_height']
    temp = row['temp']

    try:
        # Get the corresponding lapse rate for the category and season
        lapse_rate = \
        lapse_rates_df[(lapse_rates_df['country'] == category) & (lapse_rates_df['season'] == season)]['slope'].values[
            0]

        # Apply the lapse rate correction
        corrected_temp = temp + (lapse_rate * (elevation - geopotential_height))
        return corrected_temp
    except IndexError:
        # If no lapse rate is found, return the original temperature
        return temp


# Apply the bias correction
df_melted['corrected_temp'] = df_melted.apply(lambda row: apply_bias_correction(row, lapse_rates_df), axis=1)

# Pivot the dataframe back to wide format
final_df = df_melted.pivot_table(index=['Station', 'lat', 'lon', 'elevation', 'geopotential_height', 'category'],
                                 columns='date', values='corrected_temp').reset_index()

# Save the results to CSV file
output_file_path = r'C:\Users\Acer\Desktop\GIS\ARCPY\ERA\Datafinal_CDS\ERA5_India_China_daily_min_temp_corrected.csv' #change the file name here
final_df.to_csv(output_file_path, index=False)

print("Bias correction applied and data saved successfully.")
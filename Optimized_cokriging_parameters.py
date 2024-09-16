#algorithm:
#1. input= temp file, dem, xml (for january)
#2. loop through each month in the field and for the field, create a merged dataset with the DEM for each month
#3. for each dataset and the xml file for January (optimization=True), create a new xml for the required month
#caution-this code also deletes the primary temp data shape file so improvise the code to not do that
import arcpy
import os

# Set environment settings
arcpy.env.overwriteOutput = True

# Input parameters
workspace = arcpy.GetParameterAsText(0)  # Workspace
template_xml = arcpy.GetParameterAsText(1)  # Template XML file (for January)
temp_shp = arcpy.GetParameterAsText(2)  # Temperature shapefile
dem_raster = arcpy.GetParameterAsText(3)  # DEM raster
output_dir = arcpy.GetParameterAsText(4)  # Output directory for XML files

# Set the workspace
arcpy.env.workspace = workspace

# Ensure output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Months
months = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

# Loop through each month
for month in months:
    try:
        arcpy.AddMessage("Processing for month: {}".format(month))

        # Define the model source
        cokriging_xml = template_xml

        # Format the in_datasets parameter
        in_datasets = '{} F1={} ;{}'.format(temp_shp, month, dem_raster)

        # Create a new geostatistical layer with the new data
        out_layer = "co_kriging_model_{}".format(month)
        arcpy.GACreateGeostatisticalLayer_ga(
            in_ga_model_source=cokriging_xml,
            in_datasets=in_datasets,
            out_layer=out_layer
        )

        # Check if the layer was created successfully
        if arcpy.Exists(out_layer):
            arcpy.AddMessage("Created geostatistical layer for month: {}".format(month))

            # Save the layer file
            layer_file = os.path.join(output_dir, "co_kriging_model_{}.lyr".format(month))
            arcpy.SaveToLayerFile_management(out_layer, layer_file, "ABSOLUTE")

            arcpy.AddMessage("Layer file for {} saved in: {}".format(month, layer_file))
        else:
            arcpy.AddError("Geostatistical layer for {} was not created successfully.".format(month))

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as e:
        arcpy.AddError("Error processing month {}: {}".f ormat(month, str(e)))

# Cleanup
try:
    arcpy.AddMessage("Cleaning up temporary layers...")
    # Comment out or remove the line below to ensure the primary temperature shapefile is not deleted
    # arcpy.Delete_management(temp_shp)
    arcpy.AddMessage("Cleanup completed.")
except Exception as e:
    arcpy.AddError("Error during cleanup: {}".format(str(e)))
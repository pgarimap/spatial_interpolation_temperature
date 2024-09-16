import arcpy
import os
import datetime
from arcpy import env
from arcpy.sa import *

arcpy.env.overwriteOutput = True

# Check out the ArcGIS Geostatistical Analyst extension license
arcpy.CheckOutExtension("GeoStats")

# Set environment settings
workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace

# Create working temp folders if they do not exist
if not os.path.exists(os.path.join(workspace, "tif")):
    arcpy.CreateFolder_management(workspace, "tif")
if not os.path.exists(os.path.join(workspace, "tif/tmp")):
    arcpy.CreateFolder_management(workspace, "tif/tmp")

# Set local variables
tiffold = os.path.join(workspace, "tif")
tmpfold = os.path.join(tiffold, "tmp")

csv_layer = arcpy.GetParameterAsText(1)
dem = arcpy.GetParameterAsText(2)
xml_folder = arcpy.GetParameterAsText(3)  # xml folder
clpbnd = arcpy.GetParameterAsText(4)
gridres = arcpy.GetParameterAsText(5)
ncfile = arcpy.GetParameterAsText(6)
arcpy.env.extent = clpbnd

# Convert CSV Events layer to feature class in memory
in_memory_fc = "in_memory/stations"
arcpy.management.CopyFeatures(csv_layer, in_memory_fc)

# Create File Geodatabases if they do not exist
gdbloc = os.path.join(workspace, "tempsurface.gdb")
if not arcpy.Exists(gdbloc):
    arcpy.CreateFileGDB_management(workspace, "tempsurface.gdb")
sr = arcpy.Describe(in_memory_fc).spatialReference
if not arcpy.Exists(os.path.join(gdbloc, "Temperature")):
    arcpy.CreateRasterCatalog_management(gdbloc, "Temperature", sr, sr, "", "0", "0", "0", "MANAGED", "")
cat = os.path.join(gdbloc, "Temperature")

if not arcpy.Exists(os.path.join(tmpfold, "temp.gdb")):
    arcpy.CreateFileGDB_management(tmpfold, "temp.gdb")
fc1 = os.path.join(tmpfold, "temp.gdb", "fc1")

outLayer = os.path.join(workspace, "tmp", "tmp2out.tif")
calc = "calc"

# Print extents for debugging
dem_extent = arcpy.Describe(dem).extent
csv_extent = arcpy.Describe(in_memory_fc).extent
clip_extent = arcpy.Describe(clpbnd).extent

arcpy.AddMessage("DEM Extent: {}".format(dem_extent))
arcpy.AddMessage("CSV Extent: {}".format(csv_extent))
arcpy.AddMessage("Clip Boundary Extent: {}".format(clip_extent))

# Update the pattern to match your field names for all months and years
month_abbreviations = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
years = range(2013, 2024)  # Include 2023 in the range
fields = []
for year in years:
    for month in month_abbreviations:
        fields.extend(arcpy.ListFields(in_memory_fc, "{}_*_{}".format(month, year)))

if len(fields) == 0:
    arcpy.AddError("No fields matching the pattern 'MMM_DD_YYYY' were found in the feature class.")
    raise arcpy.ExecuteError("No fields matching the pattern 'MMM_DD_YYYY' were found in the feature class.")

arcpy.AddMessage("Fields found: {}".format([field.name for field in fields]))

arcpy.AddMessage(str(fields[0].name))
year0 = fields[0].name[-4:]
month0 = fields[0].name[:3]
day0 = fields[0].name[4:6]
year1 = int(year0)
month1 = datetime.datetime.strptime(month0, "%b").month
day1 = int(day0)
monthdate = "{}{:02d}{:02d}".format(year0, month1, day1)

for field in fields:
    fldname = field.name
    fld = arcpy.da.TableToNumPyArray(in_memory_fc, fldname, skip_nulls=True)
    outgrid = os.path.join(workspace, "tif", "{}.tif".format(fldname))  # Final raster output
    kriging = os.path.join(tmpfold, "cok_{}.tif".format(fldname))  # Kriging interpolation output
    fc1 = os.path.join(tmpfold, "temp.gdb", "tmp{}".format(fldname))  # Temporary feature class
    inData = "{} {} ; {}".format(in_memory_fc, fldname, dem)  # Ensuring correct formatting

    # Skip processing if the output already exists
    if os.path.exists(outgrid):
        arcpy.AddMessage("Skipping already processed {}".format(fldname))
        continue

    arcpy.AddMessage("Processing {} date ......".format(fldname[-10:]))

    # Assigning approximate XML file for different months
    month_index = datetime.datetime.strptime(fldname[:3], "%b").month
    inLayer = os.path.join(xml_folder, "Kriging_{:02d}.xml".format(month_index))
    arcpy.AddMessage("Temperature Field = {}, Month = {:02d}, XML file = Kriging_{:02d}.xml".format(fldname, month_index, month_index))

    arcpy.AddMessage("inData: {}".format(inData))
    arcpy.AddMessage("inLayer: {}".format(inLayer))
    arcpy.AddMessage("outLayer: {}".format(outLayer))

    # Execute CreateGeostatisticalLayer
    try:
        arcpy.GACreateGeostatisticalLayer_ga(inLayer, inData, outLayer)
    except arcpy.ExecuteError as e:
        arcpy.AddError("Failed to execute GACreateGeostatisticalLayer_ga. Error: {}".format(e))
        continue

    arcpy.GALayerToGrid_ga(outLayer, kriging, gridres, "1", "1")
    arcpy.AddMessage("Created the Geostatistical layer for {}".format(fldname))

    # Extract the value of interpolated raster grid at stations points
    ExtractValuesToPoints(in_memory_fc, kriging, fc1, "NONE", "VALUE_ONLY")
    # Adding the calc field in temp fc1 layer
    arcpy.AddField_management(fc1, calc, "SHORT")
    # Execute CalculateField
    arcpy.CalculateField_management(fc1, calc, "!{}! - !RASTERVALU!".format(fldname), "PYTHON")

    # Save final raster
    try:
        outExtractByMask = ExtractByMask(kriging, clpbnd)
        outExtractByMask.save(outgrid)
        arcpy.RasterToGeodatabase_conversion(outgrid, cat)
    except arcpy.ExecuteError as e:
        arcpy.AddError("Failed to execute ExtractByMask or RasterToGeodatabase_conversion. Error: {}".format(e))
        continue
    # Deleting temporary layers
    arcpy.Delete_management(fc1)
    arcpy.Delete_management(kriging)

arcpy.Delete_management(tmpfold)

# Inserting the date in the temperature catalog
field = ['Time']
arcpy.AddField_management(cat, "Time", "DATE")
cursor = arcpy.UpdateCursor(cat, field)
date = datetime.datetime(year1, month1, day1)  # start date
delta = datetime.timedelta(days=1)  # time offset

with arcpy.da.UpdateCursor(cat, field_names=('OBJECTID', 'Time'), sql_clause=('', 'ORDER BY OBJECTID')) as cur:
    for row in cur:
        row[1] = date
        date += delta
        cur.updateRow(row)

# Process: Raster to NetCDF
arcpy.AddMessage(cat)
arcpy.AddMessage(ncfile)
arcpy.RasterToNetCDF_md(cat, ncfile, "Temperature", "", "x", "y", "", "Time")

print("Finished")
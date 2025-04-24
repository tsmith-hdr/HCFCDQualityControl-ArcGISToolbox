# HCFCDQualityControl-ArcGISToolbox
ArcGIS Python Toolbox containing all the tools needed for the Quality Control process of the HCFCD SAFER Project.
## Setup
If using the Standalone Scripts, the user needs to setup a secrests.json file with the following:
``` json
{
    "username":"AGOL USERNAME",
    "password":"AGOL PASSWORD"
}
```
## Tools
There are three toolsets "Data Management Reports", "File Geodatabase Compression", and "Metadata Mangement"

### Data Management Reports
- Compare Spatial References (Excel Report): Pulls the Spatial Reference EPSG/WKID of each item from across the Master File Geodatabase, Category Specific File Geodatabase, and AGOL Service.
- Compare Storage Locations (Excel Report): Checks the existance of the item between the Category Specific File Geodatabase, AGOL Services, and Category Specific File Geodatabase and the Master File Geodatabase.
- Get Feature Class Dates (Excel Report): Pulls the Created, Modified, and Last Accessed Dates of each table listed in the Data Catalog.

### File Geodatabase Compression
- Compress FGDB Data: Iterates over the entered File Geodatabase or File Geodatabase Items and compresses the Items. <br><a href="https://pro.arcgis.com/en/pro-app/3.3/help/data/geodatabases/manage-file-gdb/compress-file-geodatabase-data.htm">Compress File Geodatabase Data (arcgis.com)</a>
- Decompress FGDB Data: Iterates over the entered File Geodatabase or File Geodatabase Items and Decompresses the Items. <br><a href="https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/uncompress-file-geodatabase-data.htm">Uncompress File Geodatabase Data (arcgis.com)</a>
- Get Compression Status (Console Message): Iterates over the entered File Geodatabase or File Geodatabase Items and consoles out if the Item is compressed (True) or not (False).

### Metadata Management
- Compare Metadata (Excel Report): Iterates over the Data Catalog Items and returns an excel report comparing Title, Description, Summary, Tags, Credits, and Access Information for each item across the three datasources. Can be returned as either HTML or Plain Text.
- Retrieve Item's Metadata (HTML): Consoles out the metadata of either the raster or feature class with the description returned in HTML
- Update Metadata (Batch)
- Update Metadata (Individual)


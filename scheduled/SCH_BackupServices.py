import os
import sys
import datetime
from pathlib import Path

import arcpy
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility
from src.tools.backupmanagement import TOOL_BackupServices
from src.constants.paths import  PORTAL_URL
#######################################################################################################################
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#######################################################################################################################
## Input Parameters 
spatial_reference = arcpy.SpatialReference(6588) 
backup_dir = r"\\Houcmi-pcs\GISData\City\HCFCD Mapping\SAFER_Study_10367700\7.2_WIP\Data\_Archive\BackupServices" ## Can't have letter drives
agol_folder_names = ["Measures"]
include_exclude_list = ["SAFER Mitigation Measures (HDR 2025)"]#, "Data", "Exisitng Infrastructure", "Future Projects", "H&H", "Half Layers (2025-04-29)", "Hazardous, Toxic, Radioactive Waste (HTRW)", "Measures", "Real Estate"]  ## list of the category specific Geodatabase names that should be evaluated. If left blank all fgdbs will be evaluated
include_exclude = "Include"
email_from="edward.smith@hdrinc.com"
email_to=email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "aaron.butterer@hdrinc.com"]## Testing
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
#######################################################################################################################
print(__name__)
print(utility.isTaskScheduler())
if __name__ == "__main__":
    if utility.isTaskScheduler():
        username = sys.argv[1]
        if username.lower() == "pro":
            gis_connection = GIS("Pro")
            
        else:
            password = sys.argv[2]
            gis_connection = GIS(PORTAL_URL, username=username, password=password)

    else:
        gis_connection = utility.authenticateAgolConnection(PORTAL_URL)

    agol_folders = [gis_connection.content.folders.get(f.replace("'","")) for f in agol_folder_names]

    TOOL_BackupServices.main(gis_conn=gis_connection,
                              spatial_reference=spatial_reference,
                              agol_folder_objs=agol_folders,
                              backup_dir=backup_dir,
                              include_exclude_flag=include_exclude,
                              include_exclude_list=include_exclude_list,
                              email_from=email_from,
                              email_to=email_to
                              )
import os
import sys
import datetime
import logging
from pathlib import Path
from importlib import reload

import arcpy
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility
from src.tools.backupmanagement import TOOL_BackupServices
from src.constants.paths import  PORTAL_URL, INTRANET_BACKUP_DIR, LOG_DIR
from src.constants.values import PROJECT_SPATIAL_REFERENCE
#######################################################################################################################
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, "Scheduled", "BackupServices_Entire", f"BackupServices_{DATETIME_STR}_Scheduled.log")
#######################################################################################################################
## Input Parameters 

backup_dir = INTRANET_BACKUP_DIR 
agol_folder_names = ["Measures",
                     "Base Layers",
                     "Biological Resources",
                     "Community",
                     "Data",
                     "Existing Infrastructure",
                     "Future Projects",
                     "H&H",
                     "Halff Layers (2025-04-29)", 
                     "Hazardous, Toxic, Radioactive Waste (HTRW)",
                     "Real Estate",
                     "Alternatives"]
include_exclude_list = []#, "Data", "Exisitng Infrastructure", "Future Projects", "H&H", "Half Layers (2025-04-29)", "Hazardous, Toxic, Radioactive Waste (HTRW)", "Measures", "Real Estate"]  ## list of the category specific Geodatabase names that should be evaluated. If left blank all fgdbs will be evaluated
include_exclude = "All"
email_from="edward.smith@hdrinc.com"
email_to=["edward.smith@hdrinc.com"]
#email_to=["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "aaron.butterer@hdrinc.com"]## Testing
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
#######################################################################################################################
## Logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)
#######################################################################################################################

logger.info(f"Run From Scheduler")
logger.info(__file__)

if __name__ == "__main__":
    if utility.isTaskScheduler():
        scheduled = True
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
                              spatial_reference=PROJECT_SPATIAL_REFERENCE,
                              agol_folder_objs=agol_folders,
                              backup_dir=backup_dir,
                              scheduled=scheduled,
                              include_exclude_flag=include_exclude,
                              include_exclude_list=include_exclude_list,
                              email_from=email_from,
                              email_to=email_to
                              )
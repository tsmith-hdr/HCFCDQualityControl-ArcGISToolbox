import os
import sys
import datetime
import logging
from pathlib import Path
from importlib import reload

import arcpy
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility, email
from src.tools.backupmanagement import TOOL_BackupServices
from src.constants.paths import  PORTAL_URL, INTRANET_BACKUP_DIR, LOG_DIR
from src.constants.values import PROJECT_SPATIAL_REFERENCE
#######################################################################################################################
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, "Scheduled", "BackupServices_Entire", f"BackupServices_{DATETIME_STR}_Scheduled.log")
#######################################################################################################################
## Input Parameters 
backup_dir = None#INTRANET_BACKUP_DIR 
folder_avoid_list = []
include_exclude_list = []#, "Data", "Exisitng Infrastructure", "Future Projects", "H&H", "Half Layers (2025-04-29)", "Hazardous, Toxic, Radioactive Waste (HTRW)", "Measures", "Real Estate"]  ## list of the category specific Geodatabase names that should be evaluated. If left blank all fgdbs will be evaluated
include_exclude = "All"
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
## Email Parameters
email_from="edward.smith@hdrinc.com"
email_to=["edward.smith@hdrinc.com"]
email_subject = f"Service Backup {DATETIME_STR.split('-')[0]}"
email_text_type = "plain"
email_message = """
    Service Backup Complete
    Check the attached log file for details.
    Outputs Directory: {}
    AGOL Folders Avoid: {}
    Include Exclude: {}
    Include Exclude List: {}
    """.format(backup_dir, folder_avoid_list, include_exclude, include_exclude_list)
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

    agol_folders = [f for f in gis_connection.content.folders.list() if f.name not in folder_avoid_list]

    outputs_report, zipped_file = TOOL_BackupServices.main(gis_conn=gis_connection,
                                                            spatial_reference=PROJECT_SPATIAL_REFERENCE,
                                                            agol_folder_objs=agol_folders,
                                                            backup_dir=backup_dir,
                                                            include_exclude_flag=include_exclude,
                                                            scheduled=scheduled,
                                                            include_exclude_list=include_exclude_list
                                                            )
    

    attachements_list = [outputs_report, zipped_file, LOG_FILE]

    ## If the email from parameter is entered, there will be an attempt to send an email with the excel report and log file.
    if email_from:
        logger.info("Sending Email...")
        result = email.sendEmail(sendTo=email_to, sendFrom=email_from, subject=email_subject, message_text=email_message+"Backup Directory: {}".format(backup_dir), text_type=email_text_type, attachments=attachements_list)
        logger.info(result)
    

    ## Trys to open the excel report. Logs warning if unable to open.
    logger.info(f"Opening Excel Report...")
    try:
        os.startfile(outputs_report)
    except Exception as t:
        logger.warning(f"Failed to Launch Excel")


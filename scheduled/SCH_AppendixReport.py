import os
import sys
import datetime 
import logging
from pathlib import Path
from importlib import reload
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility, email
from src.tools.backupmanagement import TOOL_AppendixReport
from src.constants.paths import  PORTAL_URL, INTRANET_APPENDIX_H_DIR, LOG_DIR
#######################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, "Scheduled", "AppendixReports",f"AppendixH_{DATETIME_STR}_Scheduled.log")
#######################################################################################################################
## Input Parameters 
agol_folder_names = ["Measures"]
include_records="Include Records" ## 'Overview Only' and 'Include Records'pro
include_exclude = "Include" ## 'Include', 'Exclude', 'All
include_exclude_list = ["SAFER Mitigation Measures (HDR 2025)"] ## Portal Item Title. The name on the Blue Ribbon
output_excel = os.path.join(INTRANET_APPENDIX_H_DIR,"AppendixH_{}.xlsx".format(DATETIME_STR))
## Email Parameters
email_subject = f"Appendix Report {DATETIME_STR.split('-')[0]}"
email_from = "Edward.smith@hdrinc.com"
#email_to= ["Edward.smith@hdrinc.com"]
email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "aaron.butterer@hdrinc.com"] ## Testing 
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
        username = sys.argv[1]
        scheduled = True
        if username.lower() == "pro":
            gis_connection = GIS("Pro")
            
        else:
            password = sys.argv[2]
            gis_connection = GIS(PORTAL_URL, username=username, password=password)

    else:
        scheduled=False
        gis_connection = utility.authenticateAgolConnection(PORTAL_URL)

    agol_folders = [gis_connection.content.folders.get(f.replace("'","")) for f in agol_folder_names]

    ## Logging Input Parameters
    logger.info(f"GIS Connection: {gis_connection}")
    logger.info(f"AGOL Folders: {agol_folders}")
    logger.info(f"Excel Report: {output_excel}")
    logger.info(f"Include/Exclude Flag: {include_exclude}")
    logger.info(f"Service List: {include_exclude_list}")
    logger.info(f"Email From: {email_from}")
    logger.info(f"Email To: {email_to}")
    logger.info("~~"*100)
    logger.info("~~"*100)

    TOOL_AppendixReport.main(gis_conn=gis_connection,
                             agol_folders=agol_folders,
                             include_exclude_flag=include_exclude,
                             include_exclude_list=include_exclude_list,
                             include_records=include_records,
                             output_excel=output_excel)


    ## Emails the result of the process.
    if email_from:
        logger.info(f"Sending Email...")
        email_text = """
        Attached is a copy of the report.
        Appendix H Report run on {}. 
        Input Folders: {}
        -- Input Services --
        {}

        Output Excel Path: {}
        Local User: {}
        GIS User: {}
        """.format(DATETIME_STR, agol_folder_names,"\n".join(include_exclude_list), output_excel, os.getlogin(), gis_connection.users.me.username)
        result = email.sendEmail(sendTo=email_to, sendFrom=email_from, subject=email_subject, message_text=email_text, text_type="plain", attachments=[output_excel, LOG_FILE])
        logger.info(result)
        
    ## Trys to open the excel report. Logs warning if unable to open.
    # I have the scheduled flag included so if the tool is run from task scheduler the excel file is not locked and will not throw any issues when trying to move.
    if not scheduled:
        logger.info(f"Opening Excel Report...")
        try:
            os.startfile(output_excel)
        except Exception as t:
            logger.warning(f"Failed to Launch Excel")
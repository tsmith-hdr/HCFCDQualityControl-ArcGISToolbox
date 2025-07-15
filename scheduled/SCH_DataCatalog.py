import os
import sys
import datetime 
import logging
from pathlib import Path
from importlib import reload
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility, email
from src.tools.datamanagement import TOOL_DataCatalog
from src.constants.paths import  PORTAL_URL, OUTPUTS_DIR, LOG_DIR, INTRANET_APPENDIX_E_DIR
from src.constants.values import EXTERNAL_GROUP_ITEMID, EXTERNAL_GROUP_NAME
#######################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, "Scheduled","DataCatalog",f"DataCatalog_{DATETIME_STR}.log")
#######################################################################################################################
## Input Parameters 
#output_excel =str(Path(OUTPUTS_DIR, "DataCatalog", f"DataCatalog_{DATETIME_STR}.xlsx")) ## Testing
output_excel =str(Path(INTRANET_APPENDIX_E_DIR, f"DataCatalog_{DATETIME_STR}.xlsx"))
email_subject = f"Data Catalog {DATETIME_STR.split('-')[0]}"
email_from = "Edward.smith@hdrinc.com"
#email_to = ["edward.smith@hdrinc.com"]
email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com"] ## Testing 
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
logger.info(f"Run From Task Scheduler")
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


    ## Logging Input Parameters
    logger.info(f"GIS Connection: {gis_connection}")
    logger.info(f"AGOL Group: {EXTERNAL_GROUP_NAME} ({EXTERNAL_GROUP_ITEMID})")
    logger.info(f"Excel Report: {output_excel}")
    logger.info(f"Email From: {email_from}")
    logger.info(f"Email To: {email_to}")
    logger.info("~~"*100)
    logger.info("~~"*100)

    TOOL_DataCatalog.main(gis_conn=gis_connection,
                          output_excel=output_excel)


    ## Emails the result of the process.
    if email_from:
        logger.info(f"Sending Email...")
        email_text = """
        Attached is a copy of the Data Catalog.
        Appendix E Report run on {}. 

        Output Excel Path: {}
        Local User: {}
        GIS User: {}
        """.format(DATETIME_STR, output_excel, os.getlogin(), gis_connection.users.me.username)
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
import os
import sys
import shutil
import datetime 
import logging
from pathlib import Path
from importlib import reload
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import email
from src.constants.paths import  LOG_DIR, INTRANET_APPENDIX_E_DIR, SHAREPOINT_LOCAL_DIR, SHAREPOINT_APPENDIX_E_LOCAL_DIR
#######################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, "Scheduled","DataCatalog_Sync",f"DataCatalogSync_{DATETIME_STR}.log")
#############################################################################################################################
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
## Input Parameters 
email_from = "Edward.smith@hdrinc.com"
email_to = ["Edward.smith@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "aaron.butterer@hdrinc.com"] ## Testing 
email_subject = f"Appendix E SharePoint Sync {DATETIME_STR}"
email_text_type = "plain"
email_attachments = [LOG_FILE]
#######################################################################################################################
logger.info(f"Run From Task Scheduler")
logger.info(__file__)

def main():
    if not os.path.exists(SHAREPOINT_LOCAL_DIR):
        logger.error(f"Locally Connected SharePoint Folder doesn't Exist...\n{SHAREPOINT_LOCAL_DIR}\nPlease Make Connected Folder")
        email_message="""
        The SharePoint Directory has not been created locally...
        """
    else:
        intranet_reports = os.listdir(INTRANET_APPENDIX_E_DIR)
        logger.info(f"Intranet Workbook Count: {len(intranet_reports)}")
        sharepoint_reports = os.listdir(SHAREPOINT_APPENDIX_E_LOCAL_DIR)
        logger.info(f"Local SharePoint Workbook Count: {len(sharepoint_reports)}")
        shutil_list = [i for i in intranet_reports if i not in sharepoint_reports]
        logger.info(f"Shutil List: {shutil_list}")

        if shutil_list:
            logger.info(f"Copying Files...")
            for wb in shutil_list:
                logger.info(f"Workbook: {wb}")
                src = os.path.join(INTRANET_APPENDIX_E_DIR, wb)
                logger.info(f"Source: {src}")
                dst = os.path.join(SHAREPOINT_APPENDIX_E_LOCAL_DIR, wb)
                logger.info(f"Destination: {dst}")

                try:
                    shutil.copy(src, dst)
                    if os.path.exists(dst):
                        logger.info(f"Copy Successful")
                    else:
                        logger.warning(f"Copy Failed")
                except Exception as e:
                    logger.error("Cannot Copy!!")

        
        email_message="""
        Sync Complete. See Attached Log for details.
        """
    if email_from:
        logger.info(f"Sending Email...")
        result = email.sendEmail(sendTo=email_to, 
                        sendFrom=email_from, 
                        subject=email_subject, 
                        message_text=email_message, 
                        text_type=email_text_type,
                        attachments=email_attachments)
        logger.info(result)


if __name__ == "__main__":
    logger.info(f"Appendix E Intranet Directory: {INTRANET_APPENDIX_E_DIR}")
    logger.info(f"Appendix E Local SharePoint Directory: {SHAREPOINT_APPENDIX_E_LOCAL_DIR}")
    logger.info(f"Email To: {email_to}")
    logger.info(f'Email From: {email_from}')
    main()
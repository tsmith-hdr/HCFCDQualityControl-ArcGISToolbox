import os
import sys
import shutil
import datetime 
import logging
from pathlib import Path
from importlib import reload
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility
from src.tools.datamanagement import TOOL_AppendixReport
from src.constants.paths import  LOG_DIR, APPENDIX_H_INTRANET_DIR, SHAREPOINT_LOCAL_DIR, SHAREPOINT_APPENDIX_H_LOCAL_DIR
#######################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#############################################################################################################################
## Logging
reload(logging)
log_file =os.path.join(LOG_DIR, "AppendixReports",f"AppendixH_Sync_{DATETIME_STR}.log")

logging.getLogger().disabled = True
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(log_file, mode='w')
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
logger.debug(logger)
#######################################################################################################################
## Input Parameters 
email_from = "Edward.smith@hdrinc.com"
email_to = ["Edward.smith@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "aaron.butterer@hdrinc.com"] ## Testing 
email_subject = f"Appendix H SharePoint Sync {DATETIME_STR}"
email_text_type = "plain"
email_attachments = [log_file]
#######################################################################################################################

def main():
    if not os.path.exists(SHAREPOINT_LOCAL_DIR):
        logger.error(f"Locally Connected SharePoint Folder doesn't Exist...\n{SHAREPOINT_LOCAL_DIR}\nPlease Make Connected Folder")
        email_message="""
        The SharePoint Directory has not been created locally...
        """
    else:
        intranet_reports = os.listdir(APPENDIX_H_INTRANET_DIR)
        logger.info(f"Intranet Workbook Count: {len(intranet_reports)}")
        sharepoint_reports = os.listdir(SHAREPOINT_APPENDIX_H_LOCAL_DIR)
        logger.info(f"Local SharePoint Workbook Count: {len(sharepoint_reports)}")
        shutil_list = [i for i in intranet_reports if i not in sharepoint_reports]
        logger.info(f"Shutil List: {shutil_list}")

        if shutil_list:
            logger.info(f"Copying Files...")
            for wb in shutil_list:
                logger.info(f"Workbook: {wb}")
                src = os.path.join(APPENDIX_H_INTRANET_DIR, wb)
                logger.info(f"Source: {src}")
                dst = os.path.join(SHAREPOINT_APPENDIX_H_LOCAL_DIR, wb)
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
        result = utility.sendEmail(sendTo=email_to, 
                        sendFrom=email_from, 
                        subject=email_subject, 
                        message_text=email_message, 
                        text_type=email_text_type,
                        attachments=email_attachments)
        logger.info(result)


if __name__ == "__main__":
    logger.info(f"Appendix H Intranet Directory: {APPENDIX_H_INTRANET_DIR}")
    logger.info(f"Appendix H Local SharePoint Directory: {SHAREPOINT_APPENDIX_H_LOCAL_DIR}")
    logger.info(f"Email To: {email_to}")
    logger.info(f'Email From: {email_from}')
    main()
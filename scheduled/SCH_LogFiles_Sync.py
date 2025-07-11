import os
import sys
import shutil
import datetime 
import logging
from pathlib import Path
from importlib import reload


sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility
from src.constants.paths import  LOG_DIR, INTRANET_LOG_DIR
#######################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, "Scheduled", "Logs_Sync",f"LogSync_{DATETIME_STR}_Scheduled.log")
#######################################################################################################################
## Input Parameters 
email_from = "Edward.smith@hdrinc.com"
email_to = ["Edward.smith@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "aaron.butterer@hdrinc.com"] ## Testing 
email_subject = f"Scheduled Processes Log Sync {DATETIME_STR}"
email_text_type = "plain"
email_attachments = [LOG_FILE]

log_directories = [
    "AppendixReports",
    "BackupServices",
    "AppendixReports_Sync",
    "BackupServices_Entire",
    "DataCatalog",
    "DataCatalog_Sync"
]
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
#######################################################################################################################
logger.info(f"Run From Scheduler")
logger.info(__file__)

def main():
    if not os.path.exists(INTRANET_LOG_DIR):
        logger.error(f"Intranet Log Folder doesn't Exist...\n{INTRANET_LOG_DIR}\nPlease Make Connected Folder")
        email_message="""
        The Intranet Log Directory has not been created locally...
        """
    else:
        for folder in log_directories:
            local_folder_path = Path(LOG_DIR, "Scheduled",folder)
            local_log_files = os.listdir(local_folder_path)
            logger.info(f"Local Log File Count: {len(local_log_files)}")
            intranet_folder_path = Path(INTRANET_LOG_DIR, folder)
            intranet_log_files = os.listdir(intranet_folder_path)
            logger.info(f"Intranet Log File Count: {len(intranet_log_files)}")
            shutil_list = [i for i in local_log_files if i not in intranet_log_files]
            logger.info(f"Shutil List: {shutil_list}")

            if shutil_list:
                logger.info(f"Copying Files...")
                for log_file in shutil_list:
                    logger.info(f"Log File: {log_file}")
                    src = os.path.join(local_folder_path, log_file)
                    logger.info(f"Source: {src}")
                    dst = os.path.join(intranet_folder_path, log_file)
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
    logger.info(f"Local Log Directory: {LOG_DIR}")
    logger.info(f"Intranet Log Directory: {INTRANET_LOG_DIR}")
    logger.info(f"Log Folders: {log_directories}")
    logger.info(f"Email To: {email_to}")
    logger.info(f'Email From: {email_from}')
    main()
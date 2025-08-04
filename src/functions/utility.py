#######################################################################################################################################################
## Logging
import logging
logger = logging.getLogger(f"root.utility")
#######################################################################################################################################################
import json
import sys
import os
import getpass
import zipfile
from pathlib import Path
from datetime import datetime

import arcpy
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from src.constants.values import *
################################################################################################################################################################

def getValueFromJSON(json_file, key):
    try:
       with open(json_file) as f:
            data = json.load(f)
            return data[key] 
       
    except Exception as e:
        logger.error(e)
        print("Error: ", e)

def isTaskScheduler()->bool:
    """
    Checks to see if the standalone file is being run from the console or run in a scheduled task.
    """
    # Check for an environment variable that might indicate Task Scheduler
    logger.debug(os.getenv("SESSIONNAME"))
    logger.debug(os.getenv('SCHEDULER_LAUNCH'))
    print(os.getenv("SESSIONNAME"))
    print(os.getenv('SCHEDULER_LAUNCH'))
    return os.getenv('SESSIONNAME') != 'Console' and os.getenv('SCHEDULER_LAUNCH') is None

def authenticateAgolConnection(portal_url):
    """
    Allows the user of the standalone script enter their user credentials. This is to avoid having to store credentials. 
    The portal url is set in the 
    """
    print(f"-- If using Arcgis Pro as Authentication Credentials. Input 'Pro' for username and input nothing for password and Press 'Enter' to continue.\n** You will need to be sure you are logged in to your account and correct Portal in ArcGIS Pro")
    print(f"-- Please enter 'Pro' or your Username and Password for {portal_url} --")
    count = 0
    while True:
        if count > 2:
            print(f"Too Many Attempts !! ")
            input(f"Press Any Key to Exit...")
            sys.exit("Exiting Script...")


        username = input("Username: ")
        password = getpass.getpass()
        print(f"Authenticating...")

        
        try:
            if username.lower().strip() == "pro":
                gis_conn = GIS("Pro")
            else:  
                gis_conn = GIS(portal_url, username, password)
            if gis_conn:
                break
        except Exception as e:
            count+=1
            print(f"Failed GIS Connection: {e} Please Re-enter Credentials...")


        
    return gis_conn


def valueTableToDictionary(metadata_str:str)->dict:
    out_dict = {}
    metadata_vt = arcpy.ValueTable(2)
    metadata_vt.loadFromString(metadata_str)
    for i in range(0, metadata_vt.rowCount):
        md_item = metadata_vt.getValue(i, 0)
        md_value = metadata_vt.getValue(i, 1)
        out_dict[LOCAL_SERVICE_LOOKUP[md_item]] = md_value.strip()
        
    return out_dict


def epochToString(epoch):
    timestamp = datetime.fromtimestamp(epoch/1000)
    time_string = timestamp.strftime("%m/%d/%Y")

    return (timestamp,time_string)


def getLogFile(logger_obj)->str:
    print(logger)
    print(logger_obj)
    print(dir(logger_obj))
    print(logger.root)
    print(logger.root.hasHandlers())
    logger.info(f"Logging Object: {logger}")
    print(logger_obj.handlers)
    logger_file = [h.baseFilename for h in logger_obj.handlers if isinstance(h, logging.FileHandler)]
    logger.info(f"Logger File List: {logger_file}")
    if logger_file:
        return logger_file[0]
    else:
        logger.error(f"No Log File Found...")
        return None
    

def zip_fgdb(input_fgdb, output_zip_dir):
    """
    Zips an ArcGIS file geodatabase folder.
    
    :param input_folder: Path to the file geodatabase folder.
    :param output_zip: Path to the output zip file.
    """
    output_zip = os.path.join(output_zip_dir, f"{os.path.basename(input_fgdb)}.zip")
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(input_fgdb):
            for file in files:
                if not file.endswith(".lock"):
                    file_path = os.path.join(root, file)
                    # Add file to zip, preserving folder structure
                    arcname = os.path.relpath(file_path, input_fgdb)
                    zipf.write(file_path, arcname)

    return output_zip
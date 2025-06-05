#######################################################################################################################################################
## Logging
import logging
logger = logging.getLogger(__name__)
#######################################################################################################################################################
import json
import sys
import os
import getpass
from pathlib import Path
from datetime import datetime

import arcpy
from arcgis.gis import GIS

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))


from src.constants.values import *


################################################################################################################################################################

def getValueFromJSON(json_file, key):
    try:
       with open(json_file) as f:
            data = json.load(f)
            return data[key] 
       
    except Exception as e:
        print("Error: ", e)

def isTaskScheduler()->bool:
    """
    Checks to see if the standalone file is being run from the console or run in a scheduled task.
    """
    # Check for an environment variable that might indicate Task Scheduler
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


def sendEmail(sendTo:list, sendFrom:str, subject:str, message_text:str, text_type:str, attachments:list)->str:
    returnMsgs = ''
    if type(sendTo) == list:
        send_to = ", ".join(sendTo)
    else:
        send_to = sendTo
    try:
        msg = MIMEMultipart()
        msg['Subject'] = subject

        msg.attach(MIMEText(message_text, text_type.lower()))
        ## Adds files to email as attachments
        for attachment in attachments or []:
            with open(attachment, "rb") as f:
                file = MIMEApplication(f.read(), name=os.path.basename(attachment))
            
            # After the file is closed
            file['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"' 
            msg.attach(file)
        smtp = smtplib.SMTP('smtp.hdrinc.com')
        smtp.sendmail(sendFrom, send_to, msg.as_string())
        smtp.close()

        returnMsgs = '-- Message Sent To --\n' + "\n".join(sendTo)

    except Exception as e:
        returnMsgs = str(e)
    
    return returnMsgs


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
    timestamp = datetime.fromtimestamp(epoch)
    time_string = timestamp.strftime("%m/%d/%Y")

    return (timestamp,time_string)

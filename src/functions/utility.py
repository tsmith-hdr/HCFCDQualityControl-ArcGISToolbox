#######################################################################################################################################################
## Logging
import logging
logger = logging.getLogger(__name__)
#######################################################################################################################################################
import json
import sys
import getpass

from arcgis.gis import GIS

################################################################################################################################################################

def getValueFromJSON(json_file, key):
    try:
       with open(json_file) as f:
            data = json.load(f)
            return data[key] 
       
    except Exception as e:
        print("Error: ", e)



def authenticateAgolConnection(portal_url):
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

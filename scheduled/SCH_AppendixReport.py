
import sys
import datetime 
from pathlib import Path
from arcgis.gis import GIS

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from src.functions import utility
from src.tools.datamanagement import TOOL_AppendixReport
from src.constants.paths import  PORTAL_URL, OUTPUTS_DIR
#######################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#######################################################################################################################
## Input Parameters 
agol_folder_names = ["Measures"]
include_records="Include Records" ## 'Overview Only' and 'Include Records'pro
include_exclude = "Include" ## 'Include', 'Exclude', 'All
include_exclude_list = ["SAFER Mitigation Measures (HDR 2025)"] ## Portal Item Title. The name on the Blue Ribbon
#output_excel =str(Path(OUTPUTS_DIR, "AppendixReports", f"AppendixReport_{DATETIME_STR}.xlsx"))
output_excel = r"\\Houcmi-pcs\GISData\City\HCFCD Mapping\SAFER_Study_10367700\7.2_WIP\Data\_Archive\AppendixReports\AppendixH_{}.xlsx".format(DATETIME_STR)
email_from = "Edward.smith@hdrinc.com"
#email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
email_to = ["shama.sheth@hdrinc.com","edward.smith@hdrinc.com", "aaron.butterer@hdrinc.com"] ## Testing 
#######################################################################################################################

if __name__ == "__main__":
    
    if utility.isTaskScheduler():
        username = sys.argv[1]
        if username.lower() == "pro":
            gis_connection = GIS("Pro")
            
        else:
            password = sys.argv[2]
            gis_connection = GIS(PORTAL_URL, username=username, password=password)

    else:
        gis_connection = utility.authenticateAgolConnection(PORTAL_URL)

    agol_folders = [gis_connection.content.folders.get(f.replace("'","")) for f in agol_folder_names]

    TOOL_AppendixReport.main(gis_conn=gis_connection,
                                agol_folders=agol_folders,
                                include_exclude_flag=include_exclude,
                                include_exclude_list=include_exclude_list,
                                include_records=include_records,
                                output_excel=output_excel,
                                email_from=email_from,
                                email_to=email_to
                                )

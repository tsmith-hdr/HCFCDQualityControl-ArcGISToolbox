import os
import sys
import arcpy
import logging
import datetime
import pandas as pd
from pathlib import Path
from importlib import reload

from arcgis.gis import GIS, ItemTypeEnum

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.classes.servicelayer import ServiceLayer
from src.constants.paths import LOG_DIR
#############################################################################################################################
## Environments
#############################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#############################################################################################################################
## Logging
reload(logging)
log_file =os.path.join(LOG_DIR, "AppendiciesReport",f"AppendiciesReport_{DATETIME_STR}.log")

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
print(logger)
#############################################################################################################################
def main(gis_conn:GIS, agol_folders:list, include_exclude_flag:str, output_excel:str, include_records:str,include_exclude_list:list=None)->None:
    PROPERTY_LIST = []
    RECORD_LIST = []
    #############################################################################################################################

    arcpy.AddMessage(f"AGOL Folders Count: {len(agol_folders)}")
    arcpy.AddMessage(f"Building Portal Item List...")

    item_list = []

    arcpy.AddMessage(f"{include_exclude_flag}, {type(include_exclude_flag)}")
    logger.info(f"{include_exclude_list}, {type(include_exclude_list)}")
    for folder_obj in agol_folders:
        if include_exclude_flag.strip().lower()  == "include":
            arcpy.AddMessage("Hit Include")
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)if item.name in include_exclude_list]
        elif include_exclude_flag.strip().lower() == "exclude":
            arcpy.AddMessage("Hit Exclude")
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value) if item.name not in include_exclude_list]
        elif include_exclude_flag.strip().lower()  == "all":
            arcpy.AddMessage("Hit All")
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)]

    arcpy.AddMessage(f"Item Count: {len(item_list)}")
    arcpy.AddMessage(f"Iterating Portal Item List...")
    for item in item_list:
        arcpy.AddMessage(f"Item: {item}")
        item_layers = item.layers
        for layer in item_layers:
            
            sl = ServiceLayer(gis_conn, layer)
            arcpy.AddMessage(f"Service Layer Object: {sl}")
            arcpy.AddMessage(sl.parentServiceName)

            property_dict = sl.propertyDictionary()

            if include_records == "Include Records":
                new_dict = {"Sheet Hyperlink":sl.excelHyperlink}
                for k,v in property_dict.items():
                    new_dict[k]=v
                property_dict = new_dict
                record_df = sl.recordDf()
                RECORD_LIST.append({"sheet_name":sl.excelSheetName, "df":record_df})
                
            PROPERTY_LIST.append(property_dict)

    arcpy.AddMessage(f"Exporting Excel Report...")
    df_properties = pd.DataFrame(PROPERTY_LIST)
    with pd.ExcelWriter(output_excel) as writer:
        df_properties.to_excel(writer, sheet_name="PropertiesOverview", index=False)
        if include_records == "Include Records":
            for j in RECORD_LIST:
                j["df"].to_excel(writer, sheet_name=j["sheet_name"], index=False)
        
        
    ## Trys to open the excel report. Logs warning if unable to open.
    arcpy.AddMessage(f"Opening Excel Report...")
    try:
        os.startfile(output_excel)
    except Exception as t:
        arcpy.AddWarning(f"Failed to Launch Excel")

    return 


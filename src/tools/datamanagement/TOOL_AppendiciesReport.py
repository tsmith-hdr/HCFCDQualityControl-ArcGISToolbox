import os
import sys
import arcpy
import logging
import pandas as pd
from pathlib import Path
from importlib import reload

from arcgis.gis import GIS, ItemTypeEnum

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.functions import utility
from src.classes.servicelayer import ServiceLayer
from src.constants.paths import LOG_DIR
from src.constants.values import DATETIME_STR
#############################################################################################################################
## Environments
#############################################################################################################################
## Globals
PROPERTY_LIST = []
RECORD_LIST = []
#############################################################################################################################
## Logger
reload(logging)
logging.getLogger().disabled = True
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
log_file =os.path.join(LOG_DIR, "AppendiciesReport",f"AppendiciesReport_{DATETIME_STR}.log")
file_handler = logging.FileHandler(log_file, mode='w')
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
#############################################################################################################################
##


def main(gis_conn:GIS, agol_folders:list, include_exclude_flag:str, output_excel:str, include_records:str,include_exclude_list:list=None)->None:
    logger.info(f"AGOL Folders: {agol_folders}")
    arcpy.AddMessage(f"Building Portal Item List...")
    item_list = []
    for folder_obj in agol_folders:
        if include_exclude_flag == "Include":
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)if item.name in include_exclude_list]
        elif include_exclude_flag == "Exclude":
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value) if item.name not in include_exclude_list]
        elif include_exclude_flag == "All":
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)]

    logger.info(f"Item Count: {len(item_list)}")
    arcpy.AddMessage(f"Iterating Portal Item List...")
    for item in item_list:
        logger.info(f"Item: {item}")
        item_layers = item.layers
        for layer in item_layers:
            
            sl = ServiceLayer(gis_conn, layer)
            logger.info(f"Service Layer Object: {sl}")
            logger.info(sl.parentServiceName)

            property_dict = sl.propertyDictionary()

            if include_records == "Include Records":
                new_dict = {"Sheet Hyperlink":sl.excelHyperlink}
                for k,v in property_dict.items():
                    new_dict[k]=v
                property_dict = new_dict
                record_df = sl.recordDf()
                RECORD_LIST.append({"sheet_name":sl.excelSheetName, "df":record_df})
                
            PROPERTY_LIST.append(property_dict)
            logger.info(property_dict)

    arcpy.AddMessage(f"Exporting Excel Report...")
    df_properties = pd.DataFrame(PROPERTY_LIST)
    with pd.ExcelWriter(output_excel) as writer:
        df_properties.to_excel(writer, sheet_name="PropertiesOverview", index=False)
        if include_records == "Include Records":
            for j in RECORD_LIST:
                j["df"].to_excel(writer, sheet_name=j["sheet_name"], index=False)
        
        
    ## Trys to open the excel report. Logs warning if unable to open.
    logger.info(f"Opening Excel Report...")
    try:
        os.startfile(output_excel)
    except Exception as t:
        logger.warning(f"Failed to Launch Excel")


    return
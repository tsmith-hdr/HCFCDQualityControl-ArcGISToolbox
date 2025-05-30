##################################################################################################################################################################
## Libraries
import os
import sys
import pandas as pd
from pandas import DataFrame
import logging
import datetime
import itertools
from pathlib import Path


import arcpy
from arcpy import metadata as md
from arcgis.gis import GIS

import openpyxl
from openpyxl.styles import Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

import  src.classes.DataCatalog as dc 
from src.functions import meta
from src.constants.paths import LOG_DIR, PORTAL_ITEM_URL
from src.constants.values import DF_COLUMNS, SERVICE_ITEM_LOOKUP, SHEET_NAME, DATETIME_STR

#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
## Logging ## Don't Change

log_file =Path(LOG_DIR, "UpdateServiceMetadataBatch",f"UpdateServiceMetadataBatch_{DATETIME_STR}.log")

logging.basicConfig(filename=log_file, filemode="w",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

#################################################################################################################################################################################################################


def main(gis_conn:GIS, item_types:str,agol_folders:list, metadata_dictionary:dict, output_excel:str)->None:
    items = [i for folder_name in agol_folders for i in gis_conn.content.folders.get(folder_name).list() if i.type in item_types]
    arcpy.AddMessage(agol_folders)
    arcpy.AddMessage(items)
    update_list = []
    for item in items:
        arcpy.AddMessage(item.title)
        result = item.update(item_properties=metadata_dictionary)
        arcpy.AddMessage(result)

        update_list.append({"Item Title":item.title, "Update Successful":result, "Item URL":f"{PORTAL_ITEM_URL}{item.id}"})

    update_df = pd.DataFrame(update_list, columns=["Item Title", "Update Successful", "Item URL"])
    arcpy.AddMessage(metadata_dictionary)
    metadata_dictionary["item_types"] = item_types
    arcpy.AddMessage(metadata_dictionary)
    param_df = pd.DataFrame.from_dict(metadata_dictionary, orient="index",columns=["Value"])
   

    with pd.ExcelWriter(output_excel) as writer:
        update_df.to_excel(writer, sheet_name="UpdatedItems", index=False)
        param_df.to_excel(writer, sheet_name="InputParams", header=True,index=True, index_label="Parameter")
        
    arcpy.AddMessage(f"Opening Excel Report...")
    try:
        os.startfile(output_excel)
    except Exception as t:
        arcpy.AddWarning(f"Failed to Launch Excel")

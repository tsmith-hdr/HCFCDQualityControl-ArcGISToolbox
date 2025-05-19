#################################################################################################################################################################################################################
## Libraries
import sys
import os
import pandas as pd
import logging
import datetime
from pathlib import Path

import arcpy
from arcgis.gis import GIS

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from src.classes.DataCatalog import DataCatalogRow
from src.functions import meta
from src.constants.paths import LOG_DIR
from src.constants.values import SHEET_NAME
#################################################################################################################################################################################################################
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#################################################################################################################################################################################################################
## Logging ## Don't Change
log_file = Path(LOG_DIR, "UpdateMetadata", f"Individual_UpdateMetadata_{DATETIME_STR}.log")

logging.basicConfig(filename=log_file, filemode="w",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
## Functions

def main(gis_conn:GIS, gdb_path:Path, catalog_path:Path, item_list:list)->None:
    logger.info(f"Run by: {os.getlogin()}")
    logger.info(f"Run on: {datetime.datetime.now().strftime('%Y/%m/%d')}")
    logger.info(f"File GDB Path: {gdb_path}")
    logger.info(f"Data Catalog Path: {catalog_path}")
    logger.info(f"Item List: {item_list}")
    logger.info(f"Starting: {datetime.datetime.now()}")


    
    logger.info("Creating Pandas DataFrame from Data Catalog Excel and Filtering for Input Values...")

    catalog_df = pd.read_excel(io=catalog_path, sheet_name=SHEET_NAME, header=0)

    df_filter_list = ["\\".join(item.split("\\")[-2:]) for item in item_list]

    catalog_df["stripped_category"] = catalog_df["Initial Screening Criteria"].str.replace(' ', '').str.replace('&','')
    catalog_df["dataset_path"] = catalog_df["stripped_category"]+ "\\"+catalog_df["Table Name"]

    filtered_df = catalog_df.loc[(catalog_df['dataset_path']).isin(df_filter_list)]

    arcpy.AddMessage(df_filter_list)
    arcpy.AddMessage(filtered_df)
    logger.info(f"Filtered DataFrame Length: {len(filtered_df)}")

    for index, row in filtered_df.iterrows():

        row_obj = DataCatalogRow(c_row=row, index=index, gdb_path=gdb_path, gis_conn=gis_conn)
        logger.info(f"Table: {row_obj.table_name}")

        meta.updateMetadataObjects(row_obj=row_obj)
        arcpy.AddMessage("Updated")
    logger.info(f"Finished: {datetime.datetime.now()}")
        



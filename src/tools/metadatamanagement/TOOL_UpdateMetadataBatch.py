#################################################################################################################################################################################################################
## Libraries
import sys
import pandas as pd
from pandas import DataFrame
import logging
import datetime
from pathlib import Path
import os

import arcpy
import arcpy.metadata as md
from arcgis.gis import GIS, Item

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.classes.DataCatalog import DataCatalogRow, getCatalogRows
from src.functions import meta
from src.constants.paths import LOG_DIR
from src.constants.values import SHEET_NAME
#################################################################################################################################################################################################################
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#################################################################################################################################################################################################################
## Logging ## Don't Change


log_file = Path(LOG_DIR, "UpdateMetadata", f"Batch_UpdateMetadata_{DATETIME_STR}.log")

logging.basicConfig(filename=log_file, filemode="w",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
## Functions



def main(gis_conn:GIS, gdb_path:Path, catalog_path:Path, include_exclude:str=None, web_app_categories:list=None)->None:
    logger.info(f"Run by: {os.getlogin()}")
    logger.info(f"Run on: {datetime.datetime.now().strftime('%Y/%m/%d')}")
    logger.info(f"File GDB Path: {gdb_path}")
    logger.info(f"Data Catalog Path: {catalog_path}")
    logger.info(f"Starting: {datetime.datetime.now()}")

    if include_exclude == "Exclude":
        logger.info(f"Web App Categories Not Included: {web_app_categories}")
    else:
        logger.info(f"Web App Categories Included: {web_app_categories}")


    logger.info("Creating Pandas DataFrame from Data Catalog Excel...")
    arcpy.AddMessage("Creating Pandas DataFrame from Data Catalog Excel...")
    catalog_df = pd.read_excel(io=catalog_path, sheet_name=SHEET_NAME, header=0)
    if web_app_categories:
        if include_exclude == "Include":
            update_df = catalog_df.loc[(catalog_df["Initial Screening Criteria"].isin(web_app_categories))]
        elif include_exclude == "Exclude":
            update_df = catalog_df.loc[(~catalog_df["Initial Screening Criteria"].isin(web_app_categories))]
    else:
        update_df = catalog_df
    
    arcpy.AddMessage(len(update_df))

    for index, row in update_df.iterrows():
        row_obj = DataCatalogRow(c_row=row, index=index, gdb_path=gdb_path, gis_conn=gis_conn)
        logger.info(f"Table: {row_obj.table_name}")

        meta.updateMetadataObjects(row_obj=row_obj)

    logger.info(f"Finished: {datetime.datetime.now()}")
        



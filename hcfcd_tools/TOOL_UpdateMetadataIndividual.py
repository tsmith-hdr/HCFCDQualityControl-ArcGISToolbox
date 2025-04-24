#################################################################################################################################################################################################################
## Libraries
import sys
import os
import pandas as pd
from pandas import DataFrame
import logging
import datetime
from pathlib import Path

import arcpy
import arcpy.metadata as md
from arcgis.gis import GIS, Item

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hcfcd_classes.DataCatalog import DataCatalogRow
from hcfcd_constants.values import PORTAL_URL, ROOT_DIR, PORTAL_ITEM_URL
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
## Logging ## Don't Change
log_file = Path(ROOT_DIR, "logs", "UpdateMetadata", f"UpdateMetadata.log")

logging.basicConfig(filename=log_file, filemode="a",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
## Input Parameters
master_gdb_name = "Master"
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
## Functions

def updateMetadataObjects(row_obj:DataCatalogRow)->None:
    """
    This 
    """

    if row_obj.service_exist:
        try:
            logger.info("-- Updating Service Metadata")

            item = row_obj.getServiceObject()
            item.update(item_properties=row_obj.createServiceMetadataDictionary())

        except Exception as e:
            logger.warning(f"!! Failed to update Metadata...{e}")

    if row_obj.master_exist:
        try:
            md_ = md.Metadata(row_obj.getFilePath("Master"))

            logger.info("-- Updating Master Metadata")
            
            md_.title = row_obj.md_title
            md_.description = row_obj.md_description
            md_.summary = row_obj.md_summary
            md_.tags = row_obj.formatTags_str()
            md_.credits = row_obj.md_credits
            md_.accessConstraints = row_obj.md_accessConstraints

            md_.save()
        except Exception as e:
            logger.warning(f"!! Failed to update Metadata...{e}")

    if row_obj.spatial_exist:
        try:
            md_ = md.Metadata(row_obj.getFilePath("Spatial"))

            logger.info("-- Updating Spatial Metadata")

            md_.title = row_obj.md_title
            md_.description = row_obj.md_description
            md_.summary = row_obj.md_summary
            md_.tags = row_obj.formatTags_str()
            md_.credits = row_obj.md_credits
            md_.accessConstraints = row_obj.md_accessConstraints

            md_.save()
        except Exception as e:
            logger.warning(f"!! Failed to update Metadata...{e}")

    return 


def main(gis_conn:GIS, gdb_directory:Path, catalog_path:Path, item_list:list)->None:
    logger.info("^^"*200)
    logger.info("^^"*200)
    logger.info(f"Run by: {os.getlogin()}")
    logger.info(f"Run on: {datetime.datetime.now().strftime('%Y/%m/%d')}")
    logger.info(f"File GDB Directory: {gdb_directory}")
    logger.info(f"Data Catalog Path: {catalog_path}")
    logger.info(f"Item List: {item_list}")
    logger.info(f"Starting: {datetime.datetime.now()}")


    
    logger.info("Creating Pandas DataFrame from Data Catalog Excel and Filtering for Input Values...")
    catalog_df = pd.read_excel(io=catalog_path, sheet_name="Inventory", header=0)

    df_filter_list = ["\\".join(item.split("\\")[-2:]) for item in item_list]
    filtered_df = catalog_df.loc[(catalog_df['Spatial GDB']+".gdb\\"+catalog_df["GDB File Name"]).isin(df_filter_list)]
    arcpy.AddMessage(df_filter_list)
    arcpy.AddMessage(filtered_df)
    logger.info(f"Filtered DataFrame Length: {len(filtered_df)}")

    for index, row in filtered_df.iterrows():
        row_obj = DataCatalogRow(c_row=row, index=index, gdb_directory=gdb_directory, master_gdb_name=master_gdb_name, gis_conn=gis_conn)
        arcpy.AddMessage(row_obj)
        logger.info(f"Table: {row_obj.table_name}")

        updateMetadataObjects(row_obj=row_obj)
        arcpy.AddMessage("Updated")
    logger.info(f"Finished: {datetime.datetime.now()}")
        



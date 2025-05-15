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

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from src.classes.DataCatalog import DataCatalogRow
from src.constants.paths import PORTAL_URL, ROOT_DIR, PORTAL_ITEM_URL
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

def getCatalogRows(catalog_df:DataFrame, gdb_names:list=None, include_exclude:str=None):
    """
    This Function
    """
    if gdb_names and include_exclude == "Exclude":
        return [r for r in catalog_df.iterrows() if r[1]["Spatial GDB"] not in gdb_names]
    elif gdb_names and not include_exclude == "Include":
        return [r for r in catalog_df.iterrows() if r[1]["Spatial GDB"] in gdb_names]
    else:
        return catalog_df.iterrows()
    



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




def main(gis_conn:GIS, gdb_directory:Path, catalog_path:Path, include_exclude:str=None, include_exclude_list:list=None)->None:
    logger.info("^^"*200)
    logger.info("^^"*200)
    logger.info(f"Run by: {os.getlogin()}")
    logger.info(f"Run on: {datetime.datetime.now().strftime('%Y/%m/%d')}")
    logger.info(f"File GDB Directory: {gdb_directory}")
    logger.info(f"Data Catalog Path: {catalog_path}")
    logger.info(f"Starting: {datetime.datetime.now()}")

    if include_exclude == "Exclude":
        logger.info(f"File GDBs Not Included: {include_exclude_list}")
    else:
        logger.info(f"File GDBs Included: {include_exclude_list}")


    logger.info("Creating Pandas DataFrame from Data Catalog Excel...")
    arcpy.AddMessage("Creating Pandas DataFrame from Data Catalog Excel...")
    catalog_df = pd.read_excel(io=catalog_path, sheet_name="Inventory", header=0)

    if include_exclude == "Include":
        update_df = catalog_df.loc[(catalog_df['Spatial GDB'].isin(include_exclude_list))]
    elif include_exclude == "Exclude":
        update_df = catalog_df.loc[(~catalog_df['Spatial GDB'].isin(include_exclude_list))]
    else:
        update_df = catalog_df
    
    arcpy.AddMessage(len(update_df))

    for index, row in update_df.iterrows():
        row_obj = DataCatalogRow(c_row=row, index=index, gdb_directory=gdb_directory, master_gdb_name=master_gdb_name, gis_conn=gis_conn)
        arcpy.AddMessage(row_obj.table_name)
        logger.info(f"Table: {row_obj.table_name}")

        updateMetadataObjects(row_obj=row_obj)

    logger.info(f"Finished: {datetime.datetime.now()}")
        



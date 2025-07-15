import os
import sys
import arcpy
import logging
import datetime
import pandas as pd
from pathlib import Path
from importlib import reload

from arcgis.gis import GIS, ItemTypeEnum

## Required when using ArcGIS Pro Environment.
# This tells the script where to look for the modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.functions import utility, email
from src.classes.servicelayer import ServiceLayer
#############################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#############################################################################################################################

#############################################################################################################################
## Logger
logger = logging.getLogger(f"root.TOOL_AppendixReport")
log_file = utility.getLogFile(logger)
#############################################################################################################################
def main(gis_conn:GIS, agol_folders:list, include_exclude_flag:str, output_excel:str, include_records:str,include_exclude_list:list=None)->None:

    #########################################################################################################################
    ## Empty lists used later in the process
    property_list = [] ## Holds the Items that will populate the Overview Sheet of the report. 
    record_list = [] ## If the report is to include the records from the Feature Layer. This Holds a dictionary with the Excel Sheet Name and a Pandas DataFrame of the layers attribute table
    item_list = [] ## Holds the AGOL Item Objects.
    #########################################################################################################################

    arcpy.AddMessage(f"AGOL Folders Count: {len(agol_folders)}")
    arcpy.AddMessage(f"Building Portal Item List...")
    logger.info(f"AGOL Folders Count: {len(agol_folders)}")
    logger.info(f"Building Portal Item List...")

    
    ## Iterates over the AGOL Folder objects and based on the include/exclude flag we build a list of AGOL Item Objects.
    for folder_obj in agol_folders:
        if include_exclude_flag.strip().lower()  == "include":
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)if item.title in include_exclude_list]
        elif include_exclude_flag.strip().lower() == "exclude":
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value) if item.title not in include_exclude_list]
        elif include_exclude_flag.strip().lower()  == "all":
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)]

    arcpy.AddMessage(f"Item Count: {len(item_list)}")
    arcpy.AddMessage(f"Iterating Portal Item List...")
    logger.info(f"Item Count: {len(item_list)}")
    logger.info(f"Iterating Portal Item List...")

    ## Here we are starting to iterate over the AGOL Item Objects from the previously generated list. 
    # This object will be passed into the ServiceLayer class
    for item in item_list:
        arcpy.AddMessage(f"Item: {item}")
        logger.info(f"Item: {item}")
        item_layers = item.layers ## Retrieve the Services sublayers
        arcpy.AddMessage(f"Layer Count: {len(item_layers)}")
        logger.info(f"Layer Count: {len(item_layers)}")
        ## Iterate over the layers contained in the Service/Portal Item.
        for layer in item_layers:
            arcpy.AddMessage(f"Layer: {layer}")
            logger.info(f"Layer: {layer}")
            ## Creates an instance of the ServicLayer class
            sl = ServiceLayer(gis_conn, layer, item)
            logger.debug(f"Service Layer Object: {sl}")

            ## Here we are creating a dictionary of the properties used in the Overview sheet of the out report. 
            # This dictionary will be added the property_list which is used in the Pandas DataFrame
            property_dict = sl.propertyDictionary()
            logger.debug(f"Property Dictionary: {property_dict}")

            ## If the report is going to include records for each of the layers, the below chunk handles the creation.
            if include_records == "Include Records":
                logger.info(f"Adding Hyperlink to Property Dictionary...")
                ## I create a new dictionary to make sure that the Sheet Hyperlink is in the first column.
                new_dict = {"Sheet Hyperlink":sl.excelHyperlink}
                for k,v in property_dict.items(): ## Populating the new_dict
                    new_dict[k]=v

                property_dict = new_dict ## reassign the property_dict variable to the new_dict. I did this for when we append the property_dict toe the property_list.
                
                logger.info(f"Creating Record DataFrame...")
                record_df = sl.recordDf() ## Method that creates a Pandas DataFrame of the layers attribute table.

                logger.debug(record_df.head())
                logger.info(f"Appending Record DF to RECORD_LIST...")

                record_list.append({"sheet_name":sl.excelSheetName, "df":record_df}) 

            logger.info("Appending property_dict to PROPERTY_LIST...")
            property_list.append(property_dict)

    logger.info(f"PROPERTY_LIST Count: {len(property_list)}")
    logger.info(f"RECORD_LIST Count: {len(record_list)}")

    arcpy.AddMessage(f"Exporting Excel Report...")
    logger.info(f"Exporting Excel Report...")

    ## Here is the creation and export of the Pandas Dataframes and excel workbooks
    df_properties = pd.DataFrame(property_list)
    logger.info(df_properties.head())
    with pd.ExcelWriter(output_excel) as writer:
        df_properties.to_excel(writer, sheet_name="PropertiesOverview", index=False)
        if include_records == "Include Records":
            for j in record_list:
                j["df"].to_excel(writer, sheet_name=j["sheet_name"], index=False)



    return 


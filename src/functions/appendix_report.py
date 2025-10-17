## Libraries
import os
import sys
import logging 
import datetime
import pandas as pd
from pathlib import Path

import arcpy
from arcgis.gis import GIS

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.functions import utility, meta
from src.classes.servicelayer import ServiceLayer
#############################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

#############################################################################################################################
## Logger
logger = logging.getLogger(f"root.appendix_report")
log_file = utility.getLogFile(logger)

#############################################################################################################################




def generateAppendixReport(gis_conn:GIS, item_list:list, include_records:bool, output_excel:Path)->tuple:
    '''
    This function will iterate over a list of the Item Objects and will return two lists. 
    - Property List: Holds the Items that will populate the Overview Sheet of the report. 
    - Record List: If the report is to include the records from the Feature Layer. This Holds a dictionary with the Excel Sheet Name and a Pandas DataFrame of the layers attribute table

    Input Parameters:
    - gis_conn: GIS Connection Object
    - item_list : List of ArcGIS Item Objects
    - include_records : Boolean Flag to tell indicate if the individual records of the feature layer need to be exported as well.
    - output_excel : The path to the output Excel File.

    These lists will can be used in generating reports from a Pandas Dataframe
    '''
    #########################################################################################################################
    ## The Lists that will be returned from the function
    property_list = [] ## Holds the Items that will populate the Overview Sheet of the report. 
    record_list = [] ## If the report is to include the records from the Feature Layer. This Holds a dictionary with the Excel Sheet Name and a Pandas DataFrame of the layers attribute table
    #########################################################################################################################
    
    logger.info(f"Item Count: {len(item_list)}")
    logger.info(f"Iterating Portal Item List...")
    
    ## Here we are starting to iterate over the AGOL Item Objects from the previously generated list. 
    # This object will be passed into the ServiceLayer class
    for item in item_list:
        arcpy.AddMessage(f"Item: {item}")
        logger.info(f"Item: {item}")
        try:

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
                property_dict = sl.propertyDictionary(metadata_text_type='plain')
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
        except Exception as e:
            logger.error(e)


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

    return (property_list, record_list)
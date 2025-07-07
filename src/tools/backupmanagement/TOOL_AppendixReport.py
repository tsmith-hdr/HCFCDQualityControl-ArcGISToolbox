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
## Email Parameters
subject = f"Appendix Report {DATETIME_STR.split('-')[0]}"
#############################################################################################################################
## Logger
logger = logging.getLogger(f"root.TOOL_AppendixReport")
log_file = utility.getLogFile(logger)
#############################################################################################################################
def main(gis_conn:GIS, agol_folders:list, include_exclude_flag:str, output_excel:str, include_records:str,scheduled:bool,include_exclude_list:list=None, email_from:str=None, email_to:list=None)->None:
    ## Logging Input Parameters
    logger.info(f"GIS Connection: {gis_conn}")
    logger.info(f"AGOL Folders: {agol_folders}")
    logger.info(f"Excel Report: {output_excel}")
    logger.info(f"Include/Exclude Flag: {include_exclude_flag}")
    logger.info(f"Service List: {include_exclude_list}")
    logger.info(f"Email From: {email_from}")
    logger.info(f"Email To: {email_to}")
    logger.info("~~"*100)
    logger.info("~~"*100)
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

    ## Emails the result of the process.
    if email_from:
        logger.info(f"Sending Email...")
        email_text = """
        Attached is a copy of the report.
        Appendix H Report run on {}. 
        -- Input Services --
        {}

        Output Excel Path: {}
        Local User: {}
        GIS User: {}
        """.format(DATETIME_STR, "\n".join([i.title for i in item_list]), output_excel, os.getlogin(), gis_conn.users.me.username)
        result = email.sendEmail(sendTo=email_to, sendFrom=email_from, subject=subject, message_text=email_text, text_type="plain", attachments=[output_excel, log_file])
        logger.info(result)
        
    ## Trys to open the excel report. Logs warning if unable to open.
    # I have the scheduled flag included so if the tool is run from task scheduler the excel file is not locked and will not throw any issues when trying to move.
    if not scheduled:
        arcpy.AddMessage(f"Opening Excel Report...")
        logger.info(f"Opening Excel Report...")
        try:
            os.startfile(output_excel)
        except Exception as t:
            arcpy.AddWarning(f"Failed to Launch Excel")
            logger.warning(f"Failed to Launch Excel")

    return 


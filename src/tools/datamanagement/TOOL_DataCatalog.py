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

from src.functions import utility, meta
from src.classes.servicelayer import ServiceLayer
from src.constants.values import EXTERNAL_GROUP_ITEMID
from src.constants.paths import PORTAL_ITEM_URL
#############################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#############################################################################################################################
## Logger
logger = logging.getLogger(f"root.TOOL_DataCatalog")
log_file = utility.getLogFile(logger)
#############################################################################################################################
def main(gis_conn:GIS, output_excel:str)->None:
    ## Empty lists used later in the process
    df_list = [] ## If the report is to include the records from the Feature Layer. This Holds a dictionary with the Excel Sheet Name and a Pandas DataFrame of the layers attribute table

    group_object = gis_conn.groups.get(EXTERNAL_GROUP_ITEMID)

    arcpy.AddMessage(f"Building Portal Item List...")
    logger.info(f"Building Portal Item List...")

    group_items = group_object.search("type:Feature Service")["results"]
    logger.info(f"Feature Service Count: {len(group_items)}")

    hosted_group_items = [i for i in group_items if 'Hosted Service' in i.typeKeywords]
    logger.info(f"Hosted Feature Service Count: {len(hosted_group_items)}")

    arcpy.AddMessage(f"Iterating Hosted Item List...")
    logger.info(f"Iterating Hosted Item List...")

    ## Here we are starting to iterate over the AGOL Item Objects from the previously generated list. 
    # This object will be passed into the ServiceLayer class
    for item in hosted_group_items:
        arcpy.AddMessage(f"Item: {item}")
        logger.info(f"Item: {item}")
        item_layers = item.layers ## Retrieve the Services sublayers
        arcpy.AddMessage(f"Layer Count: {len(item_layers)}")
        logger.info(f"Layer Count: {len(item_layers)}")
        ## Iterate over the layers contained in the Service/Portal Item.
        item_category = item.categories[0].split("/")[-1] if item.categories else None
        service_name = item.name if item.name else item.url.split("/")[-2]
        item_dictionary = {
            "Service Name":service_name, 
            "Item ID": item.id, 
            "Item Title": item.title, 
            "Item Last Edited Date":utility.epochToString(item.modified)[1],
            "Layer Name": None,
            "Layer ID":"root", 
            "Layer Last Edited Date":None,
            "Web App Category":item_category, 
            "Metadata - Description":meta.formatMdItem(text=item.description, md_item="description", text_type="plain"),
            "Metadata - Summary":item.snippet,
            "Metadata - Tags":item.tags,
            "Metadata - Credits": meta.formatMdItem(text=item.accessInformation, md_item="accessconstraints", text_type="plain"),
            "Metadata - License Information":meta.formatMdItem(text=item.licenseInfo, md_item="licenseinfo", text_type="plain"),
            "AGOL URL":f"{PORTAL_ITEM_URL}{item.id}"
            }
        
        df_list.append(item_dictionary)


        for layer in item_layers:
            arcpy.AddMessage(f"Layer: {layer}")
            logger.info(f"Layer: {layer}")
            ## Creates an instance of the ServicLayer class
            sl = ServiceLayer(gis_conn, layer, item)
            logger.info(f"Service Layer Object: {sl}")

            ## Here we are creating a dictionary of the properties used in the Overview sheet of the out report. 
            # This dictionary will be added the property_list which is used in the Pandas DataFrame
            datacatalog_dict = sl.dataCatalogDictionary()
            logger.debug(f"Data Catalog Dictionary: {datacatalog_dict}")

            logger.info("Appending datacalog_dict to PROPERTY_LIST...")
            df_list.append(datacatalog_dict)

    logger.info(f"DF_LIST Count: {len(df_list)}")


    arcpy.AddMessage(f"Exporting Excel Report...")
    logger.info(f"Exporting Excel Report...")

    ## Here is the creation and export of the Pandas Dataframes and excel workbooks
    df_datacatalog = pd.DataFrame(df_list)
    logger.info(df_datacatalog.head(25))
    with pd.ExcelWriter(output_excel) as writer:
        df_datacatalog.to_excel(writer, sheet_name="PropertiesOverview", index=False)

    return 


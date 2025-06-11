import os
import sys
import arcpy
import logging
import datetime
import pandas as pd
from pathlib import Path
from importlib import reload

from arcgis.gis import GIS, ItemTypeEnum

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.functions import utility
from src.constants.paths import LOG_DIR
#############################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#############################################################################################################################
## Email Parameters
send_from = "edward.smith@hdrinc.com"
send_to = ["edward.smith@hdrinc.com", "robert.graham@hdrinc.com", "shama.sheth@hdrinc.com","stewart.macpherson@hdrinc.com", "aaron.butterer@hdrinc.com"]
subject = f"Appendix H Report {DATETIME_STR.split('-')[0]}"

#############################################################################################################################
## Logging
reload(logging)
log_file =os.path.join(LOG_DIR, "AppendixReports",f"AppendixH_{DATETIME_STR}.log")

logging.getLogger().disabled = True
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler(log_file, mode='w')
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
logger.debug(logger)

from src.classes.servicelayer import ServiceLayer
#############################################################################################################################
def main(gis_conn:GIS, agol_folders:list, include_exclude_flag:str, output_excel:str, include_records:str,include_exclude_list:list=None)->None:
    PROPERTY_LIST = []
    RECORD_LIST = []
    #############################################################################################################################

    arcpy.AddMessage(f"AGOL Folders Count: {len(agol_folders)}")
    arcpy.AddMessage(f"Building Portal Item List...")
    logger.info(f"AGOL Folders Count: {len(agol_folders)}")
    logger.info(f"Building Portal Item List...")

    item_list = []

    logger.debug(f"{include_exclude_list}, {type(include_exclude_list)}")
    for folder_obj in agol_folders:
        if include_exclude_flag.strip().lower()  == "include":
            logger.debug("Hit Include")
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)if item.title in include_exclude_list]
        elif include_exclude_flag.strip().lower() == "exclude":
            logger.debug("Hit Exclude")
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value) if item.title not in include_exclude_list]
        elif include_exclude_flag.strip().lower()  == "all":
            logger.debug("Hit All")
            [item_list.append(item) for item in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)]

    arcpy.AddMessage(f"Item Count: {len(item_list)}")
    arcpy.AddMessage(f"Iterating Portal Item List...")
    logger.info(f"Item Count: {len(item_list)}")
    logger.info(f"Iterating Portal Item List...")
    for item in item_list:
        arcpy.AddMessage(f"Item: {item}")
        logger.info(f"Item: {item}")
        item_layers = item.layers
        logger.info(f"Layer Count: {len(item_layers)}")
        for layer in item_layers:
            logger.info(f"Layer: {layer}")
            sl = ServiceLayer(gis_conn, layer, item)
            logger.debug(f"Service Layer Object: {sl}")

            property_dict = sl.propertyDictionary()

            if include_records == "Include Records":
                logger.info(f"Adding Hyperlink to Property Dictionary...")
                new_dict = {"Sheet Hyperlink":sl.excelHyperlink}
                for k,v in property_dict.items():
                    new_dict[k]=v
                property_dict = new_dict
                logger.info(f"Creating Record DataFrame...")
                record_df = sl.recordDf()
                logger.debug(record_df.head())
                logger.info(f"Appending Record DF to RECORD_LIST...")
                RECORD_LIST.append({"sheet_name":sl.excelSheetName, "df":record_df})
            logger.info("Appending property_dict to PROPERTY_LIST...")
            PROPERTY_LIST.append(property_dict)

    logger.info(f"PROPERTY_LIST Count: {len(PROPERTY_LIST)}")
    logger.info(f"RECORD_LIST Count: {len(RECORD_LIST)}")

    arcpy.AddMessage(f"Exporting Excel Report...")
    logger.info(f"Exporting Excel Report...")
    df_properties = pd.DataFrame(PROPERTY_LIST)
    logger.debug(df_properties.head())
    with pd.ExcelWriter(output_excel) as writer:
        df_properties.to_excel(writer, sheet_name="PropertiesOverview", index=False)
        if include_records == "Include Records":
            for j in RECORD_LIST:
                j["df"].to_excel(writer, sheet_name=j["sheet_name"], index=False)


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
    result = utility.sendEmail(sendTo=send_to, sendFrom=send_from, subject=subject, message_text=email_text, text_type="plain", attachments=[output_excel])
    logger.info(result)
        
    ## Trys to open the excel report. Logs warning if unable to open.
    arcpy.AddMessage(f"Opening Excel Report...")
    logger.info(f"Opening Excel Report...")
    try:
        os.startfile(output_excel)
    except Exception as t:
        arcpy.AddWarning(f"Failed to Launch Excel")
        logger.warning(f"Failed to Launch Excel")

    return 


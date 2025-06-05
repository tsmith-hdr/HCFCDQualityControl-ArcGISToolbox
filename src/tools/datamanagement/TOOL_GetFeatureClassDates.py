#######################################################################################################################################################################################################
## Libraries
import os
import sys
import pytz
from pandas import DataFrame
import pandas as pd
from datetime import datetime
from arcpy.da import SearchCursor
import arcpy
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.constants.paths import LOG_DIR
from src.constants.values import DATETIME_STR
#################################################################################################################################################################################################################
## Logging ## Don't Change
#log_file = os.path.join(os.getcwd(),"ftp_achd.log")
log_file = Path(LOG_DIR, "GetFeatureClassDates",f"GetFeatureClassDates_{DATETIME_STR}.log")
arcpy.AddMessage(f"Log File: {log_file}")
logging.basicConfig(filename=log_file, filemode="w",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)
#######################################################################################################################################################################################################
## Global Parameters
DF_LIST = []
DF_COLUMNS = ["Feature Class Name", "Last Edited Date", "Last Accessed Date", "Created Date", "FGDB Name", "FGDB Path"]
#######################################################################################################################################################################################################
## Functions

def adjustTime(timezone:str, time_string:str, time_format='%Y-%m-%dT%H:%M:%S.%f')->str:
    """
    The Time Format returned from ArcGIS is '%Y-%m-%dT%H:%M:%S.%f'. As long as the timestamp is returned from the arcpy.Describe().dateModified/Accessed/Created, it will be this fromat.
    Args: time_zone
    """
    time_zone = pytz.timezone(timezone)
    
    utc_datetime = datetime.strptime(time_string, time_format)
    local_datetime = utc_datetime.astimezone(time_zone)
    local_date_str = local_datetime.strftime("%Y/%m/%d")
    
    return local_date_str

def checkGdb(gdb_path:Path, workspace):
    ## Simply makes sure that the workspace is set to the correct FGDB. The program stops if it doesn't match
    if gdb_path != workspace:
        sys.exit("!!! Workspace and FGDB Path Dont Match !!!")
    
    
def generateFeatureClassList()->list:
    datasets = arcpy.ListDatasets(feature_type="Feature")

    feature_class_list = []
    arcpy.AddMessage(f"'DataSetList:{datasets}")
    datasets.append(None)
    for dataset in datasets:
        [feature_class_list.append(feature_class) for feature_class in arcpy.ListFeatureClasses(feature_dataset=dataset)]

    
    return feature_class_list

#######################################################################################################################################################################################################
## Main
def main(gdb_list:list, excel_path:Path, timezone:str)->DataFrame:
    logger.info(f"--- TimeZone: {timezone}")
    logger.info(f"--- Output Excel Path: {excel_path}")
    logger.info(f"--- FGDB List: {gdb_list}")

    arcpy.AddMessage(f"GDB List: {gdb_list}")
    gdb_list = [g.replace("'","") for g in gdb_list]
    for gdb in gdb_list:
        arcpy.AddMessage(f"GDB: {gdb}")
        arcpy.env.workspace = gdb
        arcpy.AddMessage(f"Workspace: {arcpy.env.workspace}")
        logger.info(f"----- {arcpy.env.workspace} -----")
        checkGdb(gdb, arcpy.env.workspace)
        
        feature_class_list = generateFeatureClassList()
        logger.info(f"Feature Class Count: {len(feature_class_list)}\n")
        arcpy.AddMessage(f"Feature Class Count: {len(feature_class_list)}\n")
        for feature_class in feature_class_list:
            logger.info(f'Feature Class: {feature_class}')
            arcpy.AddMessage(f'Feature Class: {feature_class}')
            desc = arcpy.Describe(feature_class) ## Retrieves the Object Properties of the feature class above has links to the documentation
            
            utc_modified = desc.dateModified
            utc_accessed = desc.dateAccessed
            utc_created = desc.dateCreated

            
            modified_date = adjustTime(timezone, utc_modified)
            accessed_date = adjustTime(timezone, utc_accessed)
            created_date = adjustTime(timezone, utc_created)

            logger.info(f"Modified Date: {modified_date}")
            logger.info(f"Last Accessed Date: {accessed_date}")
            logger.info(f"Created Date: {created_date}\n")

            DF_LIST.append([desc.name, modified_date, accessed_date, created_date, Path(gdb).stem, gdb])

    logger.info(f"Generating DataFrame...")
    print(DF_LIST)
    df = pd.DataFrame(DF_LIST, columns=DF_COLUMNS, index=False)
    logger.info(df.head(5))

    logger.info(f"Exporting Excel...")
    df.to_excel(excel_path)

    arcpy.AddMessage(f"Excel Report Has Been Exported to:\n{excel_path}")
    arcpy.AddMessage(f"Opening Excel Report...")
    try:
        os.startfile(excel_path)
    except Exception as t:
        arcpy.AddWarning(f"Failed to Launch Excel")


    return df
            
            
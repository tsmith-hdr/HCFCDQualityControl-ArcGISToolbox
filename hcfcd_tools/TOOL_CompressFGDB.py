#######################################################################################################################################################################################################
## Libraries
import os
import sys

from datetime import datetime
from arcpy.da import SearchCursor
import arcpy
import logging
from pathlib import Path

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hcfcd_constants.values import ROOT_DIR
from hcfcd_functions.utility import getLogger
#######################################################################################################################################################################################################
log_file = Path(ROOT_DIR, "logs", "FGDBCompressionsAndDecompressions","FGDBCompressionsAndDecompressions.log")

logging.basicConfig(filename=log_file, filemode="a",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)
#logger = getLogger(log_file=log_file, file_mode="a", uses_arcgis_api=False)
logger.info(f"Run by: {os.getlogin()}")
logger.info(f"Run on: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
#######################################################################################################################################################################################################

def main(item_type:str, items:list)->None:
    logger.info(f"Item Type: {item_type}")

    for item in items:
        logger.info(f"-- {item}")
        arcpy.AddMessage(f"-- {item}")
        arcpy.management.CompressFileGeodatabaseData(in_data=item, lossless=True)
        if item_type in ["Feature Class", "Table"]:
            logger.info(arcpy.Describe(item).isCompressed)

    logger.info(f"Finished: {datetime.now()}")
    

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
#######################################################################################################################################################################################################

log_file = Path(ROOT_DIR, "logs", "FGDBCompressionsAndDecompressions","FGDBCompressionsAndDecompressions.log")
logging.basicConfig(filename=log_file, filemode="a",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


logger.info(f"Run by: {os.getlogin()}")
logger.info(f"Run on: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
#######################################################################################################################################################################################################
def main(item_type:str, items:list)->None:

    logger.info(f"Item Type: {item_type}")
    arcpy.AddMessage(f"Items: {items}")
    for item in items:
        logger.info(f"-- {item}")
        arcpy.AddMessage(f"-- {item}")
        arcpy.management.UncompressFileGeodatabaseData(in_data=item)

    logger.info(f"Finished: {datetime.now()}")
    
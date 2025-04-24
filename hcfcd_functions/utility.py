import json
from pathlib import Path
import logging
from hcfcd_constants.values import ROOT_DIR

def getValueFromJSON(json_file, key):
    try:
       with open(json_file) as f:
            data = json.load(f)
            return data[key] 
       
    except Exception as e:
        print("Error: ", e)


def getLogger(log_file, file_mode, uses_arcgis_api):
    #log_file = Path(ROOT_DIR, "logs", "Compare_SpatialReferences", "Compare_SpatialReferences.log")

    logging.basicConfig(filename=log_file, filemode=file_mode,format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    if uses_arcgis_api:
        logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
        logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    return logger
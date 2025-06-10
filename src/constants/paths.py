from pathlib import Path
import urllib
import arcpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = Path(ROOT_DIR, "logs")

SHP_DIR = Path(ROOT_DIR, "src", "shp")

OUTPUTS_DIR = Path(ROOT_DIR, "outputs")

PORTAL_URL = "https://hcfcd-safer.maps.arcgis.com/"

PORTAL_ITEM_URL = urllib.parse.urljoin(PORTAL_URL, "home/item.html?id=")


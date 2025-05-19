from pathlib import Path
import urllib


ROOT_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = Path(ROOT_DIR, "logs")

OUTPUTS_DIR = Path(ROOT_DIR, "outputs")

PORTAL_URL = "https://hdr.maps.arcgis.com/"

PORTAL_ITEM_URL = urllib.parse.urljoin(PORTAL_URL, "home/item.html?id=")

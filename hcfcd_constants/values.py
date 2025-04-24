from pathlib import Path
import urllib


ROOT_DIR = Path(__file__).resolve().parents[1]

PORTAL_URL = "https://cascadiahsr.maps.arcgis.com/"

PORTAL_ITEM_URL = urllib.parse.urljoin(PORTAL_URL, "home/item.html?id=")


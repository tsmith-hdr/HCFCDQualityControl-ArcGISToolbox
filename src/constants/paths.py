from pathlib import Path
import urllib
import arcpy
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = Path(ROOT_DIR, "logs")

SHP_DIR = Path(ROOT_DIR, "src", "shp")

OUTPUTS_DIR = Path(ROOT_DIR, "outputs")

PORTAL_URL = "https://hcfcd-safer.maps.arcgis.com/"

PORTAL_ITEM_URL = urllib.parse.urljoin(PORTAL_URL, "home/item.html?id=")

SHAREPOINT_URL = "https://hdrinc.sharepoint.com/teams/DL10412519/"

SHAREPOINT_LOCAL_DIR = fr"C:\Users\{os.getlogin()}\HDR, Inc\HCFCD SAFER 203 Study - GIS"

SHAREPOINT_APPENDIX_H_LOCAL_DIR = os.path.join(SHAREPOINT_LOCAL_DIR,"Documents","Appendices","Appendix H - Hosted Feature Reports")

INTRANET_ARCHIVE = r"\\Houcmi-pcs\GISData\City\HCFCD Mapping\SAFER_Study_10367700\7.2_WIP\Data\_Archive"

INTRANET_BACKUP_DIR = os.path.join(INTRANET_ARCHIVE, "BackupServices")

APPENDIX_H_INTRANET_DIR = os.path.join(INTRANET_ARCHIVE, "AppendixReports")
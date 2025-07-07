from pathlib import Path
import urllib
import arcpy
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

## Local Paths
ROOT_DIR = Path(__file__).resolve().parents[2]

LOG_DIR = Path(ROOT_DIR, "logs")

SHP_DIR = Path(ROOT_DIR, "src", "shp")

OUTPUTS_DIR = Path(ROOT_DIR, "outputs")

## AGOL Paths
PORTAL_URL = "https://hcfcd-safer.maps.arcgis.com/"

PORTAL_ITEM_URL = urllib.parse.urljoin(PORTAL_URL, "home/item.html?id=")


## SharePoint Paths
SHAREPOINT_URL = "https://hdrinc.sharepoint.com/teams/DL10412519/"

SHAREPOINT_LOCAL_DIR = fr"C:\Users\{os.getlogin()}\HDR, Inc\HCFCD SAFER 203 Study - GIS"

SHAREPOINT_APPENDIX_H_LOCAL_DIR = os.path.join(SHAREPOINT_LOCAL_DIR,"Documents","Appendices","Appendix H - Hosted Feature Reports")

## Intranet Paths
INTRANET_ROOT_DIR = r"\\Houcmi-pcs\GISData\City\HCFCD Mapping\SAFER_Study_10367700"

## Intranet Logs
INTRANET_LOG_DIR = Path(INTRANET_ROOT_DIR, "7.2_WIP","Scripts","HCFCDQualityControl-ArcGISToolbox","logs")

## Intranet Archive Directories
INTRANET_ARCHIVE = Path(INTRANET_ROOT_DIR, "7.2_WIP","Data","_Archive")

INTRANET_BACKUP_DIR = os.path.join(INTRANET_ARCHIVE, "BackupServices")

APPENDIX_H_INTRANET_DIR = os.path.join(INTRANET_ARCHIVE, "AppendixReports")


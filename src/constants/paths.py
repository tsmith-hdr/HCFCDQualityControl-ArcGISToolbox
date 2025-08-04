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

SHAREPOINT_APPENDIX_E_LOCAL_DIR = os.path.join(SHAREPOINT_LOCAL_DIR,"Documents","Appendices","Appendix E- Safer Data Catalog")


## Intranet Paths
INTRANET_ROOT_DIR = r"\\Houcmi-pcs\GISData\City\HCFCD Mapping\SAFER_Study_10367700"

INTRANET_LOG_DIR = Path(INTRANET_ROOT_DIR, "7.2_WIP","Scripts","HCFCDQualityControl-ArcGISToolbox","logs")

INTRANET_ARCHIVE = Path(INTRANET_ROOT_DIR, "7.2_WIP","Data","_Archive")

INTRANET_BACKUP_DIR = os.path.join(INTRANET_ARCHIVE, "BackupServices")

INTRANET_APPENDIX_H_DIR = os.path.join(INTRANET_ARCHIVE, "AppendixReports")

INTRANET_APPENDIX_E_DIR = os.path.join(INTRANET_ARCHIVE, "DataCatalog")


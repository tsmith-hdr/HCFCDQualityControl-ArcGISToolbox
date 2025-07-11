import arcpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

PROJECT_SPATIAL_REFERENCE = arcpy.SpatialReference(2278)

SHEET_NAME = "Test Data Catalog"


DF_COLUMNS = ["Local - Exist",  
              "Service - Exist", 
              "Local - title",
              "Service - title",
              "title - Match", 
              "Local - description",
              "Service - description",
              "description - Match", 
              "Local - summary",
              "Service - summary",
              "summary - Match", 
              "Local - tags",
              "Service - tags",
              "tags - Match",
              "Local - credits",
              "Service - credits",
              "credits - Match", 
              "Local - accessConstraints",
              "Service - accessConstraints",
              "accessConstraints - Match"
              ]

SERVICE_ITEM_LOOKUP = {"title":"title", 
                       "description":"description", 
                       "summary":"snippet", 
                       "tags":"tags", 
                       "credits":"accessInformation", 
                       "accessConstraints":"licenseInfo"}

LOCAL_SERVICE_LOOKUP = {
    "Title":"title",
    "Description":"description",
    "Tags":"tags",
    "Summary":"snippet",
    "Credits":"accessInformation",
    "Terms of Use":"licenseInfo"
}



EXTERNAL_GROUP_NAME = "SAFER - External share group"
EXTERNAL_GROUP_ITEMID = "acf03764bdab420abe07ee61452012ea"
import datetime 

SHEET_NAME = "Test Data Catalog"

DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")



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
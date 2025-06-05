import arcpy
import datetime
import pandas as pd

from arcgis.gis import Item

class ServiceLayer():
    def __init__(self, gis_conn, layer_obj):
        self.gis_conn = gis_conn
        self.layerProperties = layer_obj.properties
        self.parentPortalItem = self._getParentPortalItem()
        self.parentServiceName = self.parentPortalItem.name
        self.parentServiceUrl = self.parentPortalItem.url
        self.parentId = self.layerProperties["serviceItemId"]
        self.portalTitle = self.parentPortalItem.title
        self.portalCreatedDate = self.parentPortalItem.created ## Return Epoch
        self.portalModifiedDate = self.parentPortalItem.modified ## Return Epoch
        self.portalDescription = self.parentPortalItem.description
        self.portalSummary = self.parentPortalItem.snippet
        self.portalTags = self.parentPortalItem.tags
        self.portalCredits = self.parentPortalItem.accessInformation
        self.portalTermsOfUse = self.parentPortalItem.licenseInfo
        self.layerName = self.layerProperties["name"]
        self.layerUrl = layer_obj.url
        self.layerId = self.layerProperties["id"]
        self.layerSchemaEditDate = self.layerProperties["editingInfo"]["schemaLastEditDate"] ## Return Epoch
        self.layerDataEditDate = self.layerProperties["editingInfo"]["dataLastEditDate"] ## Return Epoch
        self.layerPropertiesEditDate = self.layerProperties["editingInfo"]["lastEditDate"] ## Return Epoch
        self.layerFields = self.layerProperties["fields"]  ## Returns a list of dictionaries 

    @property
    def excelSheetName(self):
        formatted = self.layerName.translate({ord(c): "" for c in "_ "})
        excelSheetName=formatted[0:31]
        return excelSheetName
    
    @property
    def excelHyperlink(self):
        return f'=HYPERLINK("#{self.excelSheetName}!A1", "Go To Sheet {self.excelSheetName}")'

    def _getParentPortalItem(self)->Item:
        return self.gis_conn.content.get(self.layerProperties["serviceItemId"])
    
    def propertyDictionary(self)->dict:
        out_dict = {}
        
        out_dict["Feature Service Name"]=self.parentServiceName
        #out_dict["Feature Service REST URL"]=self.parentServiceUrl
        out_dict["Portal Item ID"]=self.parentId
        out_dict["Portal Item Created Date"]=self.epochToString(self.portalCreatedDate)
        #out_dict["Portal Item Last Edit Date"]=self.epochToString(self.portalModifiedDate)
        out_dict["Layer Name"]=self.layerName
        out_dict["Layer Schema Edit Date"]=self.epochToString(self.layerSchemaEditDate)
        out_dict["Layer Data Edit Date"]=self.epochToString(self.layerDataEditDate)
        out_dict["Layer Properties Edit Date"]=self.epochToString(self.layerPropertiesEditDate)
        out_dict["Layer Field Names"]=", ".join([f["name"] for f in self.layerFields])
        out_dict["Portal Item Title"]=self.portalTitle
        out_dict["Portal Item Description"]=self.portalDescription
        out_dict["Portal Item Summary"]=self.portalSummary
        out_dict["Portal Item Tags"]=', '.join(self.portalTags)
        out_dict["Portal Item Credits"]=self.portalCredits
        out_dict["Portal Item Terms of Use"]=self.portalTermsOfUse
        

        return out_dict

    def recordDf(self)->pd.DataFrame:
        fields = [field["name"] for field in self.layerFields]
        df_columns = [f'{field["name"]} ({field["alias"]})' for field in self.layerFields]
        print(self.layerUrl)
        print(fields)
        records = [list(row) for row in arcpy.da.SearchCursor(self.layerUrl.replace("'",""), [fields])]
        print(records)
        df = pd.DataFrame(data=records, columns=df_columns)

        return df
    

    @staticmethod
    def epochToString(epoch:int)->str:
        timestamp = datetime.datetime.fromtimestamp(epoch/1000)
        time_string = timestamp.strftime("%m/%d/%Y")

        return time_string
    

    

    

        



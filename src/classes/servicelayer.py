import os
import sys
import json
import datetime
import logging
import pandas as pd
from pathlib import Path

import arcpy
from arcgis.gis import Item

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.functions import meta
from src.constants.paths import SHP_DIR, PORTAL_ITEM_URL
from src.constants.values import PROJECT_SPATIAL_REFERENCE
#################################################################################################################################################################################
logger = logging.getLogger("root.servicelayer")
#################################################################################################################################################################################

class ServiceLayer():
    def __init__(self, gis_conn, layer_obj, portal_obj):
        self.logger = logging.getLogger("root.servicelayer.ServiceLayer")
        self.gis_conn = gis_conn
        self.layer = layer_obj
        self.layerProperties = self.layer.properties
        self.parentPortalItem = portal_obj
        self.isMultilayer = True if "Multilayer" in self.parentPortalItem["typeKeywords"] else False
        self.isHosted = True if "Hosted Service" in self.parentPortalItem["typeKeywords"] else False
        self.parentServiceName = self.parentPortalItem.name
        self.parentServiceUrl = self.parentPortalItem.url
        self.parentId = portal_obj.id
        self.portalItemUrl = f"{PORTAL_ITEM_URL}{self.parentId}"
        self.portalTitle = self.parentPortalItem.title
        self.portalCategories = self.parentPortalItem.categories
        self.portalCategory = self.portalCategories[0].split("/")[-1] if self.portalCategories else None
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
        self.layerPortalUrl = f"{self.portalItemUrl}&sublayer={self.layerId}"
        self.layerSchemaEditDate = self.layerProperties["editingInfo"]["schemaLastEditDate"] if hasattr(self.layerProperties,"editingInfo") else None ## Return Epoch
        self.layerDataEditDate = self.layerProperties["editingInfo"]["dataLastEditDate"] if hasattr(self.layerProperties,"editingInfo") else None## Return Epoch
        self.layerPropertiesEditDate = self.layerProperties["editingInfo"]["lastEditDate"] if hasattr(self.layerProperties,"editingInfo") else None## Return Epoch
        self.layerFields = self.layerProperties["fields"]  ## Returns a list of dictionaries 
        self.layerDescription = self.layerProperties["description"]
        self.layerCredits = self.layerProperties["copyrightText"]
        self.layerSpatialReferenceWkid = self.layerProperties["spatialReference"]["latestWkid"] if hasattr(self.layerProperties, "spatialReference") else self.layerProperties["sourceSpatialReference"]["latestWkid"]
        self.projectBoundaryPath = os.path.join(SHP_DIR, "project_boundaries",str(self.layerSpatialReferenceWkid), "projectboundary.shp") if self.isHosted else os.path.join(SHP_DIR, "project_boundaries",str(self.layerSpatialReferenceWkid), "projectboundary.shp")


    @property
    def excelSheetName(self):
        formatted = self.layerName.translate({ord(c): "" for c in "_ ,()|/\\"})
        excelSheetName=formatted[0:31]
        return excelSheetName
    
    @property
    def excelHyperlink(self):
        return f'=HYPERLINK("#{self.excelSheetName}!A1", "Go To Sheet {self.excelSheetName}")'
    
    def _getServiceName(self):
        basesplit = self.parentServiceUrl.split("Server")[0]
        service_name =basesplit.split("/")[-2]

        return service_name


    def _getParentPortalItem(self)->Item:
        return self.gis_conn.content.get(self.layerProperties["serviceItemId"])
    
    def dataCatalogDictionary(self)->dict:
        out_dict = {}
        out_dict["Service Name"] = self.parentServiceName if self.parentServiceName else self.layerUrl.split("/")[-3]
        out_dict["Item ID"] = self.parentId
        out_dict["Item Title"] = None
        out_dict["Item Last Edited Date"] = None
        out_dict["Layer Name"] = self.layerName
        out_dict["Layer ID"] = self.layerId
        out_dict["Layer Last Edited Date"] = self.epochToString(self.layerDataEditDate)
        out_dict["Web App Category"] = self.portalCategory
        out_dict["Metadata - Description"] = meta.formatMdItem(self.layerDescription, "description", "plain")
        out_dict["Metadata - Summary"] = self.portalSummary
        out_dict["Metadata - Tags"] = self.portalTags
        out_dict["Metadata - Credits"] = meta.formatMdItem(self.layerCredits, "accessconstraints", "plain")
        out_dict["Metadata - License Information"] = meta.formatMdItem(self.portalTermsOfUse, "licenseinfo", "plain")
        out_dict["AGOL URL"] = self.layerPortalUrl

        return out_dict
    
    def propertyDictionary(self)->dict:
        out_dict = {}
        out_dict["Layer Name"]=self.layerName
        out_dict["Feature Service Name"]=self.parentServiceName if self.parentServiceName else self._getServiceName()
        out_dict["Is Hosted"] = self.isHosted
        out_dict["Is Multilayer"] = self.isMultilayer
        #out_dict["Feature Service REST URL"]=self.parentServiceUrl
        out_dict["Portal Item ID"]=self.parentId
        out_dict["Portal Item Created Date"]=self.epochToString(self.portalCreatedDate)
        #out_dict["Portal Item Last Edit Date"]=self.epochToString(self.portalModifiedDate)
        out_dict["Layer Schema Edit Date"]=self.epochToString(self.layerSchemaEditDate)
        out_dict["Layer Data Edit Date"]=self.epochToString(self.layerDataEditDate)
        out_dict["Layer Properties Edit Date"]=self.epochToString(self.layerPropertiesEditDate)
        out_dict["Layer Field Names"]=", ".join([f["name"] for f in self.layerFields])
        out_dict["Layer Description"] = self.layerDescription
        out_dict["Layer Credits"] = self.layerCredits
        out_dict["Portal Item Title"]=self.portalTitle
        out_dict["Portal Item Description"]=self.portalDescription
        out_dict["Portal Item Summary"]=self.portalSummary
        out_dict["Portal Item Tags"]=', '.join(self.portalTags)
        out_dict["Portal Item Credits"]=self.portalCredits
        out_dict["Portal Item Terms of Use"]=self.portalTermsOfUse

        

        return out_dict

    def recordDf(self)->pd.DataFrame:
        self._handleProjectBoundaryShp()
        shp_geom = [i[0] for i in arcpy.da.SearchCursor(self.projectBoundaryPath, ["SHAPE@"])][0]
        spatial_rel = "ENVELOPE_INTERSECTS"
        fields = [field["name"] for field in self.layerFields]
        df_columns = [f'{field["name"]} ({field["alias"]})' for field in self.layerFields]
        records = [list(row) for row in arcpy.da.SearchCursor(self.layerUrl.replace("'",""), [fields], spatial_filter=shp_geom, spatial_relationship=spatial_rel)]
        df = pd.DataFrame(data=records, columns=df_columns)

        return df
    

    @staticmethod
    def epochToString(epoch:int)->str:
        if epoch:
            timestamp = datetime.datetime.fromtimestamp(epoch/1000)
            time_string = timestamp.strftime("%m/%d/%Y")
        
            return time_string
        else:
            return "No Available Date"
    

    def _handleProjectBoundaryShp(self):
        base_shp = os.path.join(SHP_DIR,"project_boundaries", str(PROJECT_SPATIAL_REFERENCE.factoryCode), "projectboundary.shp")
    
        if os.path.exists(self.projectBoundaryPath):
            pass

        else:
            self.logger.info("Creating New Shapefile...")
            if not os.path.exists(os.path.dirname(self.projectBoundaryPath)):
                os.makedirs(os.path.dirname(self.projectBoundaryPath))
            arcpy.management.Project(base_shp, self.projectBoundaryPath, arcpy.SpatialReference(self.layerSpatialReferenceWkid))

        return 
    
    
    

    def exportLayer(self, out_workspace):
        metadata_dict = {}
        feature_names = [f for dataset in arcpy.ListDatasets(feature_type="Feature") for f in arcpy.ListFeatureClasses(feature_dataset=dataset)]
        formatted_layer_name = self.layerName.translate({ord(c): "_" for c in "!@#$%^&*()[] {};:,./<>?\|`~-=_+"})
        ## Need to add logic to replace leading digits
        
        count = 1
        while True:
            if formatted_layer_name not in feature_names:
                break
            else:
                if count==1:
                    formatted_layer_name = f"{formatted_layer_name}_{count}"
                else:
                    formatted_layer_name = f"{formatted_layer_name.rsplit('_',1)[0]}_{count}"

                count+=1
        self.logger.info(f"Formatted Name: {formatted_layer_name}")
        self.logger.info(f"Layer Spatial Reference: {self.layerSpatialReferenceWkid}")
        self._handleProjectBoundaryShp()

        try:
            self.logger.info("Exporting...")
            featureclass_path = os.path.join(out_workspace, formatted_layer_name)
            with arcpy.EnvManager(outputCoordinateSystem=PROJECT_SPATIAL_REFERENCE, preserveGlobalIds=True, extent=self.projectBoundaryPath):
                arcpy.conversion.ExportFeatures(in_features=self.layerUrl,
                                                out_features=featureclass_path)
        except Exception as f:
            self.logger.error(f"{self.layerName:30s} {self.parentId:30s}")
            arcpy.AddWarning(f"Layer Failed to Export:\n{self.layerName:30s} {self.parentId:30s}")

        metadata_dict["Feature Class Name"]=formatted_layer_name
        metadata_dict["Feature Class Path"]=featureclass_path
        metadata_dict["Layer Name"]=self.layerName
        metadata_dict["Layer URL"]=self.layerUrl
        metadata_dict["Service Item Id"]=self.parentId
        metadata_dict["Service Credits"]=self.portalCredits

        return metadata_dict

        



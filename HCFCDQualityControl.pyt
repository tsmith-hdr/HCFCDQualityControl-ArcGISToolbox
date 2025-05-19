# -*- coding: utf-8 -*-
import sys
import os
import arcpy
from arcgis.gis import GIS
import pandas as pd
import ctypes
import requests
import re

from pathlib import Path

if str(Path(__file__).resolve().parents[0]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
    
from src.tools import TOOL_UpdateMetadataBatch
from src.tools import TOOL_UpdateMetadataIndividual
from src.tools import TOOL_CompareSpatialReferences
from src.tools import TOOL_GetFeatureClassDates
from src.tools import TOOL_CompareMetadata
from src.tools import TOOL_CompareStorageLocations


from src.constants.paths import PORTAL_URL, OUTPUTS_DIR
from src.constants.values import DATETIME_STR

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "HCFCD Quality Control"
        self.alias = "HCFCD Quality Control"

        # List of tool classes associated with this toolbox
        self.tools = [UpdateMetadata_b,
                      UpdateMetadata_i,
                      CompareSpatialReference,
                      CompareStorageLocations,
                      FeatureClassDates,
                      CompareMetadata,
                      GrabItemsMD,
                      GrabWebItemsMD]


class UpdateMetadata_b:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Metadata (Batch)"
        self.description = "Updates the metadata across the 3 data sources."
        self.gis_conn = GIS("Pro")
        self.category = "Metadata Management"

    def getParameterInfo(self):
        """Define the tool parameters."""
        gdb_path = arcpy.Parameter(
            displayName="File GDB Path",
            name="gdb_path",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        
        gdb_path.filter.list = ["Local Database"]

        catalog_path = arcpy.Parameter(
            displayName="Data Catalog Path (Excel)",
            name="catalog_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        
        catalog_path.filter.list = ["xlsx"]

        include_exclude = arcpy.Parameter(
            displayName="Include/Exclude",
            name="include_exclude",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        
        include_exclude.filter.list = ["Include", "Exclude"]
    

        include_exclude_list = arcpy.Parameter(
            displayName="Include/Exclude List",
            name="include_exclude_list",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
            enabled=False)
        
        
        
        params = [gdb_path, catalog_path, include_exclude, include_exclude_list]
        
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        # if self.gis_conn.url != PORTAL_URL:
        #     return False
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        
        gdb_path = parameters[0]
        include_exclude = parameters[2]
        include_exclude_list = parameters[3]

        arcpy.env.workspace = gdb_path.valueAsText

        if gdb_path.altered:
            include_exclude_list.filter.list = [i for i in arcpy.ListDatasets(feature_type="Feature")]

        if include_exclude.altered:
            if include_exclude.value in ["Include", "Exclude"]:
                include_exclude_list.enabled = True
        elif not include_exclude.altered:
            setattr(include_exclude_list, "value", None)
            include_exclude_list.enabled = False

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        gdb_path = parameters[0].valueAsText
        catalog_path = parameters[1].valueAsText   
        include_exclude = parameters[2].valueAsText
        if parameters[3].valueAsText:
            include_exclude_list = list(set(parameters[3].valueAsText.split(";"))) if parameters[3].value else None
        
        arcpy.AddMessage(include_exclude)
        arcpy.AddMessage(include_exclude_list)
        if __name__ == "__main__":
            TOOL_UpdateMetadataBatch.main(gis_conn=self.gis_conn,
                                        gdb_path=Path(gdb_path),
                                        catalog_path=Path(catalog_path),
                                        include_exclude=include_exclude,
                                        include_exclude_list=include_exclude_list
                                        )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
    

class UpdateMetadata_i:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Metadata (Individual)"
        self.description = "Updates the metadata across the 3 data sources. "
        self.gis_conn = GIS("Pro")
        self.canRunInBackground = True
        self.category = "Metadata Management"


    def getParameterInfo(self):
        """Define the tool parameters."""
        catalog_path = arcpy.Parameter(
            displayName="Data Catalog Path (Excel)",
            name="catalog_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input",
            enabled=True)
        
        catalog_path.filter.list=["xlsx"]

        gdb_path = arcpy.Parameter(
            displayName="File GDB Path",
            name="gdb_path",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        
        gdb_path.filter.list = ["Local Database"]
    

        item_type = arcpy.Parameter(
            displayName="Item Type",
            name="item_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        item_type.filter.type = "ValueList"
        item_type.filter.list = ["Feature Class", "Raster"]

        featureclass = arcpy.Parameter(
            displayName="Feature Class",
            name="featureclass",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input",
            enabled=False,
            multiValue=True)
        
        raster = arcpy.Parameter(
            displayName="Raster",
            name="raster",
            datatype="DERasterDataset",
            parameterType="Optional",
            direction="Input",
            enabled=False,
            multiValue=True)
        
        

        params = [catalog_path, gdb_path, item_type, featureclass, raster]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        # if self.gis_conn.url != PORTAL_URL:
        #     return False
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        item_type = parameters[2]
        featureclass = parameters[3]
        raster = parameters[4]

        if item_type.altered and not item_type.hasBeenValidated:
            check_list = [featureclass, raster]

            [setattr(i, "enabled", False) for i in check_list]
            [setattr(i, "value", None) for i in check_list]

            if item_type.valueAsText == "Feature Class":
                featureclass.enabled = True
            elif item_type.valueAsText == "Raster":
                raster.enabled = True
            else:
                pass
                
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        catalog_path = parameters[0]
        gdb_path = parameters[1]
        if catalog_path.value:
            df = pd.read_excel(catalog_path.valueAsText)

            #concat_list = list(f"{gdb_path.valueAsText}\\"+df["Table Name"])
            concat_list = df["Table Name"].to_list()
            message_list = "\n".join(concat_list)
            catalog_path.setWarningMessage(message_list)

        item_type = parameters[2]
        feature_classes = parameters[3]
        rasters = parameters[4]

        if item_type.altered:
            if feature_classes.valueAsText or rasters.valueAsText:
                split_item = feature_classes.valueAsText if item_type.valueAstext == "Feature Class" else rasters.valueAsText
                item_list = [i.replace("'","").split("\\")[-1] for i in split_item.split(";")]
            
                #check_list = ["\\".join(item.split("\\")[-2:]) for item in item_list]

                for i in item_list:
                    if i not in concat_list:
                        if item_type.valueAsText == "Feature Class":
                            feature_classes.setErrorMessage(f"{i} not in Data Catalog")
                        elif item_type.valueAsText == "Raster":
                            rasters.setErrorMessage(f"{i} not in Data Catalog")
    
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        catalog_path = parameters[0].valueAsText
        gdb_path = parameters[1].valueAsText
        
        item_type = parameters[2].valueAsText
        featureclasses = parameters[3].valueAsText
        rasters = parameters[4].valueAstext

        if item_type == "Feature Class":
            item_list = featureclasses.split(";")
        elif item_type == "Raster":
            item_list = rasters.split(";")
        arcpy.AddMessage(parameters[3].value)
        cleaned_items = [i.replace("'", "") for i in item_list]
        arcpy.AddMessage(item_list)
        if __name__ == "__main__":
            TOOL_UpdateMetadataIndividual.main(gis_conn=self.gis_conn,
                                               gdb_path=gdb_path,
                                               catalog_path=Path(catalog_path),
                                               item_list=cleaned_items)

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return



class CompareSpatialReference:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Compare Spatial References (Excel Report)"
        self.description = "Compares the Spatial Reference Code for all three of the data sources."
        self.gis_conn = GIS("Pro")
        self.canRunInBackground = True
        self.category = "Data Management Reports"

    def getParameterInfo(self):
        """Define the tool parameters."""
        gdb_path = arcpy.Parameter(
            displayName="File GDB Path",
            name="gdb_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        
        catalog_path = arcpy.Parameter(
            displayName="Data Catalog Path (Excel)",
            name="catalog_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        
        catalog_path.filter.list = ["xlsx"]

        output_excel =arcpy.Parameter(
            displayName="Output Path (Excel)",
            name="output_excel",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        
        output_excel.filter.list = ["xlsx"]
        output_excel.value = os.path.join(OUTPUTS_DIR, "CompareSpatialReferences", f"CompareSpatialReferences_{DATETIME_STR}.xlsx")

        params = [gdb_path, catalog_path, output_excel]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        if self.gis_conn.url != PORTAL_URL:
            return False
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        gdb_path = parameters[0].valueAsText
        catalog_path = parameters[1].valueAsText
        output_excel = parameters[2].valueAsText
        if __name__ == "__main__":
            TOOL_CompareSpatialReferences.main(gis_conn=self.gis_conn,
                                           gdb_path=gdb_path,
                                           catalog_path=catalog_path,
                                           output_excel=output_excel
                                           )
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return



class FeatureClassDates:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Get Feature Class Dates (Excel Report)"
        self.description = "Iterates over a list of File GDBs and returns the Access, Modified, and Created Dates of the Feature Classes."
        self.canRunInBackground = True
        self.category = "Data Management Reports"

    def getParameterInfo(self):
        """Define the tool parameters."""
        gdb_list = arcpy.Parameter(
            displayName="File GDBs",
            name="gdb_list",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        
        gdb_list.filter.list = ["Local Database"]

        excel_path = arcpy.Parameter(
            displayName="Output Report Path (Excel)",
            name="excel_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        
        excel_path.filter.list = ["xlsx"]    
        excel_path.value = os.path.join(OUTPUTS_DIR, "FeatureClassDates", f"FeatureClassDates_{DATETIME_STR}.xlsx")

        time_zone = arcpy.Parameter(
            displayName="Local Timezone",
            name="time_zone",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        time_zone.filter.list = ["America/Los_Angeles","America/Denver","America/Chicago","America/New_York"]    


        params = [gdb_list, excel_path, time_zone]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        gdb_list = parameters[0].valueAsText
        output_excel = parameters[1].valueAsText
        time_zone = parameters[2].valueAsText

        if __name__ == "__main__":
            TOOL_GetFeatureClassDates.main(gdb_list=gdb_list.split(";"),
                                       excel_path=Path(output_excel),
                                       timezone=time_zone
                                       )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return





class CompareMetadata:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Compare Metadata (Excel Report)"
        self.description = ""
        self.gis_conn = GIS("Pro")
        self.canRunInBackground = True
        self.category = "Metadata Management"

    def getParameterInfo(self):
        """Define the tool parameters."""
        gdb_path = arcpy.Parameter(
            displayName="File GDB Path",
            name="gdb_path",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        
        gdb_path.filter.list = ["Local Database"]

        catalog_path = arcpy.Parameter(
            displayName="Data Catalog Path (Excel)",
            name="catalog_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        
        catalog_path.filter.list = ["xlsx"]


        text_type = arcpy.Parameter(
            displayName="Metadata Output Text Type",
            name="text_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        text_type.filter.type = "ValueList"
        text_type.filter.list = ["Plain", "HTML"]

        output_excel = arcpy.Parameter(
            displayName="Output Report Path (Excel)",
            name="output_excel",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        
        output_excel.filter.list = ["xlsx"]
        


        web_app_categories = arcpy.Parameter(
            displayName="Web App Categories to be evaluated",
            name="spatial_gdb_names",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True)
        
        include_exclude = arcpy.Parameter(
            displayName="Include/Exclude",
            name="include_exclude",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=False)
        
        include_exclude.filter.type = "Value"
        include_exclude.filter.list = ["Include", "Exclude"]
        


        params = [gdb_path, catalog_path, text_type, output_excel, include_exclude,web_app_categories]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        if self.gis_conn.url != PORTAL_URL:
            return False
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        gdb_path = parameters[0]
        text_type = parameters[2]
        out_excel = parameters[3]
        web_app_categories = parameters[5]

        if gdb_path.altered:
            arcpy.env.workspace = gdb_path.valueAsText
            dataset_list = [dataset for dataset in arcpy.ListDatasets(feature_type="Feature")]
            web_app_categories.filter.type = "ValueList"
            web_app_categories.filter.list = dataset_list

        if text_type.altered and not text_type.hasBeenValidated:
            out_excel.value = os.path.join(OUTPUTS_DIR, "CompareMetadata", f"CompareMetadata_{text_type.valueAsText}_{DATETIME_STR}.xlsx")
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        gdb_path = parameters[0].valueAsText
        catalog_path = parameters[1].valueAsText
        output_excel = parameters[3].valueAsText
        text_type = parameters[2].valueAsText
        web_app_categories = None if parameters[5].valueAsText is None else parameters[5].valueAsText.split(";")
        include_exclude = parameters[4]

        if __name__ == "__main__":
            arcpy.AddMessage(output_excel)
            TOOL_CompareMetadata.main(gis_conn=self.gis_conn,
                                  gdb_path=gdb_path,
                                  catalog_path=catalog_path,
                                  output_excel=output_excel,
                                  text_type=text_type,
                                  web_app_categories=web_app_categories,
                                  include_exclude=include_exclude
                                )


        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return



class CompareStorageLocations:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Compare Storage Locations (Excel Report)"
        self.description = ""
        self.gis_conn = GIS("Pro")
        self.canRunInBackground = True
        self.category = "Data Management Reports"

    def getParameterInfo(self):
        """Define the tool parameters."""
        gdb_path = arcpy.Parameter(
            displayName="File GDB Path",
            name="gdb_path",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        
        gdb_path.filter.list = ["Local Database"]
        
        catalog_path = arcpy.Parameter(
            displayName="Data Catalog Path (Excel)",
            name="catalog_path",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        
        catalog_path.filter.list = ["xlsx"]

        output_excel =arcpy.Parameter(
            displayName="Output Path (Excel)",
            name="output_excel",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        
        output_excel.filter.list = ["xlsx"]
        output_excel.value = os.path.join(OUTPUTS_DIR, "CompareStorageLocations", f"CompareStorageLocations_{DATETIME_STR}.xlsx")

        params = [gdb_path, catalog_path, output_excel]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        if self.gis_conn.url != PORTAL_URL:
            return False
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        gdb_path = parameters[0].valueAsText
        catalog_path = parameters[1].valueAsText
        excel_path = parameters[2].valueAsText

        if __name__ == "__main__":
            TOOL_CompareStorageLocations.main(gis_conn=self.gis_conn,
                                          gdb_path=gdb_path,
                                          catalog_path=catalog_path,
                                          excel_path=excel_path
                                          )

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return



class GrabItemsMD:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Retrieve Items Metadata (ArcGIS Pro)"
        self.description = ""
        self.category = "Metadata Management"

    def getParameterInfo(self):
        """Define the tool parameters."""
        item_type = arcpy.Parameter(
            displayName="Item Type",
            name="item_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        item_type.filter.type = "ValueList"
        item_type.filter.list = ["Feature Class", "Raster"]

        featureclass = arcpy.Parameter(
            displayName="Feature Class",
            name="featureclass",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input",
            enabled=False)
        
        raster = arcpy.Parameter(
            displayName="Raster",
            name="raster",
            datatype="DERasterDataset",
            parameterType="Optional",
            direction="Input",
            enabled=False)
        
        

        params = [item_type, featureclass, raster]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        item_type = parameters[0]
        featureclass = parameters[1]
        raster = parameters[2]

        if item_type.altered and not item_type.hasBeenValidated:
            check_list = [featureclass, raster]

            [setattr(i, "enabled", False) for i in check_list]
            [setattr(i, "value", None) for i in check_list]

            if item_type.valueAsText == "Feature Class":
                featureclass.enabled = True
            elif item_type.valueAsText == "Raster":
                raster.enabled = True
            else:
                pass
                
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import arcpy.metadata
        if parameters[1]:
            item = parameters[1].valueAsText
        elif parameters[2]:
            item = parameters[2].valueAsText
        
        md = arcpy.metadata.Metadata(item)
        md_items = ['title', 'summary','description','tags','accessConstraints','credits','maxScale', 'minScale', 'xMax','xMin','yMax','yMin']

        for i in md_items:
            attr = getattr(md, i)
            arcpy.AddMessage(f"{i.title()}:\n{attr}\n")

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return



class GrabWebItemsMD:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Retrieve Items Metadata (AGOL/Portal)"
        self.description = ""
        self.category = "Metadata Management"

    def getParameterInfo(self):
        """Define the tool parameters."""
        org_type = arcpy.Parameter(
            displayName="Organization Type",
            name="org_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        org_type.filter.type = "ValueList"
        org_type.filter.list = ["AGOL", "Portal"]

        portal_path = arcpy.Parameter(
            displayName="Portal Path",
            name="portal_path",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            enabled=False)
        
        item_id = arcpy.Parameter(
            displayName="Item ID",
            name="item_id",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            enabled=True)
        
        

        params = [org_type, portal_path, item_id]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        org_type = parameters[0]
        portal_path = parameters[1]
 

        if org_type.altered and not org_type.hasBeenValidated:
            check_list = [portal_path]

            [setattr(i, "enabled", False) for i in check_list]
            [setattr(i, "value", None) for i in check_list]

            if org_type.valueAsText == "Portal":
                portal_path.enabled = True
            else:
                pass
                
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        portal_path = parameters[1]

        if portal_path.altered and not portal_path.hasBeenValidated:
            if not portal_path.valueAsText.startswith("https"):
                portal_path.setErrorMessage("Invalid Portal Path | Portal Path needs to begin with https:// ")
            elif not portal_path.valueAsText.endswith("/portal") and not portal_path.valueAsText.endswith("/portal/"):
                portal_path.setErrorMessage("Invalid Portal Path | Portal Path needs to end with /portal ")
            try:
                result = requests.get(portal_path.valueAsText)
                if result.status_code != 200:
                    portal_path.setErrorMessage("Invalid Portal Path | Connection Error ")
            except Exception as e:
                portal_path.setErrorMessage(f"Invalid Portal Path | {e.__doc__} ")
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        org_type = parameters[0].valueAsText
        if org_type == "Portal":
            gis_path = parameters[1].valueAsText
        else:
            gis_path = "https://arcgis.com"

        item_id = parameters[2].valueAsText
        
        gis = GIS(gis_path)
        item_url = f"{gis_path}/home/item.html?id={item_id}"
        md = gis.content.get(item_id)
        if not md:
            arcpy.AddError("No Web Item Found")
        else:
            md_items = {'id':"Item ID", 
                        'owner':'Owner',
                        'name':'Service Name',
                        'title':"Item Title",
                        'type':'Item Type', 
                        'snippet':"Summary",
                        'description':"Description",
                        'tags':"Tags",
                        'accessInformation':"Credits",
                        'licenseInfo':"Access Constraints",
                        'extent':"Extent", 
                        'spatialReference':"Spatial Reference",
                        'url':"Service Url"}

            for k,v in md_items.items():
                attr = getattr(md, k)
                if k == 'description' and attr:
                    attr = attr.replace("\xa0", "").replace("\n", " ")
                arcpy.AddMessage(f"{v}:\n{attr}\n")
            
            arcpy.AddMessage(f"Item Url:\n{item_url}\n")

        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
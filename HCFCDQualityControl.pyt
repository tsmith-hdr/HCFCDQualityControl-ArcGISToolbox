# -*- coding: utf-8 -*-
import os
import sys
import requests
import datetime
import pandas as pd
from pathlib import Path

import arcpy

from arcgis.gis import GIS, ItemTypeEnum
print(str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
print(sys.path)
    
from src.functions import utility
from src.constants.paths import PORTAL_URL, OUTPUTS_DIR
#############################################################################################################################
## Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#############################################################################################################################

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
                      GrabWebItemsMD,
                      BackupServices,
                      UpdateServicesMeta,
                      AppendiciesReport]


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
            from src.tools.metadatamanagement import TOOL_UpdateMetadataBatch

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
            from src.tools.metadatamanagement import TOOL_UpdateMetadataIndividual

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
            from src.tools.datamanagement import TOOL_CompareSpatialReferences

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
            from src.tools.datamanagement import TOOL_GetFeatureClassDates

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
            from src.tools.metadatamanagement import TOOL_CompareMetadata

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
            from src.tools.datamanagement import TOOL_CompareStorageLocations

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
    

class BackupServices:

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Service Backup"
        self.description = ""
        self.category = "Backup Management"
        self.gis = GIS("Pro")
        self.datetime_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    def getParameterInfo(self):
        """Define the tool parameters."""
        # gdb_directory = arcpy.Parameter(
        #     displayName="File GDB Folder",
        #     name="gdb_directory",
        #     datatype="DEFolder",
        #     parameterType="Required",
        #     direction="Input")
        
        spatial_reference = arcpy.Parameter(
            displayName="Spatial Reference",
            name="spatial_reference",
            datatype="GPSpatialReference",
            parameterType="Required",
            direction="Input")
        
        agol_folders = arcpy.Parameter(
            displayName="AGOL Folders",
            name="agol_folder",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        
        agol_folders.filter.type = "ValueList"
        agol_folders.filter.list = [folder.name for folder in self.gis.content.folders.list()]
        
        include_exclude = arcpy.Parameter(
            displayName="Include/Exclude Flag",
            name="include_exclude",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
        
        include_exclude.value = "All"
        include_exclude.filter.type = "ValueList"
        include_exclude.filter.list = ["Include", "Exclude", "All"]

        include_exclude_list = arcpy.Parameter(
            displayName="AGOL Services",
            name="include_exclude_list",
            datatype="GPString",
            parameterType="optional",
            direction="Input",
            enabled=False,
            multiValue=True)
        
        include_exclude_list.filter.type="ValueList"


        email_from = arcpy.Parameter(
            displayName="Email From",
            name="email_from",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            category="Email")
        

        email_to = arcpy.Parameter(
            displayName="Email To",
            name="email_to",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
            category="Email")
        
        backup_dir = arcpy.Parameter(
            displayName="Backup Directory",
            name="backup_dir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        

        # excel_report = arcpy.Parameter(
        #     displayName="Excel Report",
        #     name="excel_report",
        #     datatype="DEFile",
        #     parameterType="Required",
        #     direction="Output")
        
        # excel_report.filter.list = ["xlsx"]
        # excel_report.value = os.path.join(OUTPUTS_DIR, "BackupServices", f"BackupServices_{self.datetime_str}.xlsx")


        params = [agol_folders,spatial_reference,include_exclude, include_exclude_list,email_from, email_to, backup_dir]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        agol_folders = parameters[0]
        include_exclude = parameters[2]
        include_exclude_list = parameters[3]

        if agol_folders.altered and not agol_folders.hasBeenValidated:
            if agol_folders.valueAsText:
                agol_folder_objs = [self.gis.content.folders.get(f.replace("'", "")) for f in agol_folders.valueAsText.split(";")]
                include_exclude_list.filter.list = [i.title for folder_obj in agol_folder_objs for i in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)]
        
        if include_exclude.altered and not include_exclude.hasBeenValidated:
            if include_exclude.valueAsText in ["Include", "Exclude"] and agol_folders.valueAsText:
                include_exclude_list.enabled = True

            else:
                include_exclude_list.value = None
                include_exclude_list.enabled = False

        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        email_from = parameters[4]
        email_to = parameters[5]

        if email_from.altered and not email_from.hasBeenValidated:
            if not email_from.valueAsText.lower().endswith("@hdrinc.com"):
                email_from.setErrorMessage("Senders email needs to be from an HDR inc. Email")
        
        if email_to.altered and not email_to.hasBeenValidated:
            if email_to.valueAsText:
                email_list = email_to.valueAsText.split(";")
                for email in email_list:
                    if not email.lower().endswith("@hdrinc.com"):
                        email_to.setErrorMessage(f"All Emails need to be an HDR inc. email.\n{email}")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        spatial_reference = arcpy.SpatialReference(text=parameters[1].valueAsText)
        backup_dir = parameters[6].valueAsText
        include_exclude = parameters[2].valueAsText
        include_exclude_list = [i.replace("'","") for i in parameters[3].valueAsText.split(";")] if parameters[3].valueAsText else []
        email_from = parameters[4].valueAsText if parameters[4].valueAsText else None
        email_to = [i.replace("'", "") for i in parameters[5].valueAsText.split(";")] if parameters[5].valueAsText else None
        agol_folders = [self.gis.content.folders.get(f.replace("'","")) for f in parameters[0].valueAsText.split(";")]
        arcpy.AddMessage(__name__)
        if __name__ == "__main__" or __name__ == "pyt":
            from src.tools.backupmanagement import TOOL_BackupServices

            TOOL_BackupServices.main(gis_conn=self.gis, 
                                     spatial_reference=spatial_reference,
                                     agol_folder_objs=agol_folders,
                                     backup_dir=backup_dir,
                                     include_exclude_flag=include_exclude,
                                     include_exclude_list=include_exclude_list,
                                     email_from=email_from,
                                     email_to=email_to)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return

class UpdateServicesMeta:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Batch Update Service Metadata (Excel Report)"
        self.description = ""
        self.category = "Metadata Management"
        self.gis = GIS("Pro")

    def getParameterInfo(self):
        """Define the tool parameters."""
        item_types = arcpy.Parameter(
            displayName="Item Types",
            name="item_types",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        
        item_types.filter.type = "ValueList"
        #item_types.filter.list = ["Map Service", "Feature Service", 'Web Map', 'Web Experience','StoryMap','Dashboard','Vector Tile Service']

        agol_folders = arcpy.Parameter(
            displayName="AGOL Folders",
            name="agol_folder",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        
        agol_folders.filter.type = "ValueList"
        agol_folders.filter.list = [folder.name for folder in self.gis.content.folders.list()]

        metadata_dict = arcpy.Parameter(
            displayName="Metadata Dictionary",
            name="metadata_dict",
            datatype="GPValueTable",
            parameterType="Required",
            direction="Input")
        
        metadata_dict.columns = [['GPString', "Item"], ["GPString", "Value"]]
        metadata_dict.filters[0].type = 'ValueList'
        metadata_dict.filters[0].list = ["Title", "Summary", "Description", "Terms of Use", "Credits", "Tags"]

        output_excel = arcpy.Parameter(
            displayName="Excel Report Path",
            name="output_excel",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        
        output_excel.filter.list = ["xlsx"]
        output_excel.value = os.path.join(OUTPUTS_DIR, "UpdateServiceMetadataBatch", f"UpdateServiceMetadataBatch_{DATETIME_STR}.xlsx")


        params = [agol_folders, item_types,metadata_dict, output_excel]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        agol_folders = parameters[0]
        item_types = parameters[1]

        if agol_folders.altered and not agol_folders.hasBeenValidated:
            if agol_folders.valueAsText:
                item_types.filter.list = list(set([i.type for folder_name in agol_folders.valueAsText.split(";") for i in self.gis.content.folders.get(folder_name.replace("'","")).list()]))

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        metadata = parameters[2]
        metadata_str = metadata.valueAsText
        if metadata.altered:
            metadata_vt = arcpy.ValueTable(2)
            metadata_vt.loadFromString(metadata_str)
            for i in range(0, metadata_vt.rowCount):
                md_item = metadata_vt.getValue(i, 0)
                md_value = metadata_vt.getValue(i, 1)
                if md_value is None or md_value.strip() == '':
                    metadata.setWarningMessage(f"If a Value is left blank, the associated metadata item will not be updated.\nProblem Metadata Item: {md_item}")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        item_types_str = parameters[1].valueAsText
        item_types_list = [i.replace("'","") for i in item_types_str.split(";")]

        metadata_str = parameters[2].valueAsText
        metadata_dictionary = utility.valueTableToDictionary(metadata_str)
        arcpy.AddMessage(metadata_dictionary)
        output_excel = parameters[3].valueAsText

        agol_folders = [f.replace("'","") for f in parameters[0].valueAsText.split(";")]

        if __name__ == "__main__":
            from src.tools.metadatamanagement import TOOL_UpdateServiceMetadataBatch

            TOOL_UpdateServiceMetadataBatch.main(gis_conn=self.gis, item_types=item_types_list, agol_folders = agol_folders,metadata_dictionary=metadata_dictionary, output_excel=output_excel)
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
    

class AppendiciesReport:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Appendix Report (Excel Report)"
        self.description = ""
        self.category = "Data Management Reports"
        self.gis = GIS("Pro")
        self.datetime_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    def getParameterInfo(self):
        """Define the tool parameters."""
        agol_folders = arcpy.Parameter(
            displayName="AGOL Folders",
            name="agol_folder",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            multiValue=True)
        
        agol_folders.filter.type = "ValueList"
        agol_folders.filter.list = [folder.name for folder in self.gis.content.folders.list()]


        include_exclude = arcpy.Parameter(
            displayName= "Include/Exclude Flag",
            name="include_exclude",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        include_exclude.value = "All"
        include_exclude.filter.type = "ValueList"
        include_exclude.filter.list = ["Include", "Exclude", "All"]

        include_exclude_list = arcpy.Parameter(
            displayName= "Include/Exclude List",
            name="include_exclude_list",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
            enabled=False)
        
        include_exclude_list.filter.type = "ValueList"
        
        output_excel = arcpy.Parameter(
            displayName="Excel Report Path",
            name="output_excel",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        
        output_excel.filter.list = ["xlsx"]
        output_excel.value = os.path.join(OUTPUTS_DIR, "AppendixReports", f"AppendixReport_{self.datetime_str}.xlsx")

        include_records = arcpy.Parameter(
            displayName="Include Records",
            name="include_records",
            direction="Input",
            datatype="GPString",
            parameterType="Optional")
        
        include_records.value = "Overview Only"
        include_records.filter.type = "ValueList"
        include_records.filter.list = ["Overview Only", "Include Records"]        

        email_from = arcpy.Parameter(
            displayName="Email From",
            name="email_from",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            category="Email")
        

        email_to = arcpy.Parameter(
            displayName="Email To",
            name="email_to",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True,
            category="Email")


        params = [agol_folders,include_exclude,include_exclude_list, output_excel, include_records, email_from, email_to]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        agol_folders = parameters[0]
        include_exclude = parameters[1]
        include_exclude_list = parameters[2]

        if agol_folders.altered and not agol_folders.hasBeenValidated:
            if agol_folders.valueAsText:
                agol_folder_objs = [self.gis.content.folders.get(f.replace("'", "")) for f in agol_folders.valueAsText.split(";")]
                include_exclude_list.filter.list = [i.title for folder_obj in agol_folder_objs for i in folder_obj.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)]
        
        if include_exclude.altered and not include_exclude.hasBeenValidated:
            if include_exclude.valueAsText in ["Include", "Exclude"] and agol_folders.valueAsText:
                include_exclude_list.enabled = True

            else:
                include_exclude_list.value = None
                include_exclude_list.enabled = False

        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        email_from = parameters[5]
        email_to = parameters[6]

        if email_from.altered and not email_from.hasBeenValidated:
            if not email_from.valueAsText.lower().endswith("@hdrinc.com"):
                email_from.setErrorMessage("Senders email needs to be from an HDR inc. Email")
        
        if email_to.altered and not email_to.hasBeenValidated:
            if email_to.valueAsText:
                email_list = email_to.valueAsText.split(";")
                for email in email_list:
                    if not email.lower().endswith("@hdrinc.com"):
                        email_to.setErrorMessage(f"All Emails need to be an HDR inc. email.\n{email}")

        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        include_exclude_flag = parameters[1].valueAsText
        include_exclude_list = [i.replace("'","") for i in parameters[2].valueAsText.split(";")] if parameters[2].valueAsText else []
        output_excel = parameters[3].valueAsText
        agol_folders = [self.gis.content.folders.get(f.replace("'","")) for f in parameters[0].valueAsText.split(";")]
        include_records = parameters[4].valueAsText
        email_from = parameters[5].valueAsText if parameters[5].valueAsText else None
        email_to = [e.replace("'", "") for e in parameters[6].valueAsText] if parameters[6].valueAsText else None
        arcpy.AddMessage(__name__)
        
        if __name__ == "__main__" or __name__ == "pyt":
            from src.tools.datamanagement import TOOL_AppendixReport
            TOOL_AppendixReport.main(gis_conn=self.gis, 
                                        agol_folders=agol_folders,
                                        include_exclude_flag=include_exclude_flag, 
                                        output_excel=output_excel,
                                        include_records=include_records,
                                        include_exclude_list=include_exclude_list,
                                        email_from=email_from,
                                        email_to=email_to
                                        )
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
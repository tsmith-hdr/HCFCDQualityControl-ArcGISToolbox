import arcpy
import os
import requests
from arcpy import metadata as md
from pandas import DataFrame

def getCatalogRows(catalog_df:DataFrame, web_app_categories:list=None,include_exclude:str="Include"):
    if web_app_categories:
        if include_exclude == "Exclude":
            return [r for r in catalog_df.iterrows() if r[1]["Initial Screening Criteria"].replace(' ','').replace('&','') not in web_app_categories]
        elif include_exclude == "Include":
            return [r for r in catalog_df.iterrows() if r[1]["Initial Screening Criteria"].replace(' ','').replace('&','') in web_app_categories]
        else:
            return [r for r in catalog_df.iterrows() if r[1]["Initial Screening Criteria"].replace(' ','').replace('&','') in web_app_categories]

    else:
        return catalog_df.iterrows()




class DataCatalogRow():
    def __init__(self, c_row, index, gdb_path, gis_conn):
        
        
        self._excel_index = index + 2 
        self._gis_conn = gis_conn
        self._gdb_path = gdb_path
        self._c_row = c_row
        self._validateRow(c_row, self.excel_index, gdb_path=gdb_path, gis_conn=gis_conn)

    ################ Getter/Setters ################
    ## Getter Excel Index
    @property
    def excel_index(self):
        return self._excel_index
    
    @property 
    def c_row(self):
        return self._c_row
    
    ## Getter GIS Connection Index
    @property
    def gis_conn(self):
        return self._gis_conn
    
    ## Getter GIS GDB Path
    @property
    def gdb_path(self):
        return self._gdb_path
        ## Getter Table Name
    @property
    def table_name(self):
        return self.c_row["Table Name"]
    
    @property
    def data_name(self):
        return self.c_row["Data Name"]
    
    @property
    def gdb_item_path(self):
        return os.path.join(self.gdb_path, self.table_name)
    
    # ## Getter Spatial GDB 
    @property
    def agol_item_id(self):
        return self.c_row["AGOL Item ID"] if not isinstance(self.c_row["AGOL Item ID"], float) else None

    @property
    def provider(self):
        return self.c_row["Provider"]
        
    @property
    def webapp_category(self):
        return self.c_row["Initial Screening Criteria"] if not isinstance(self.c_row["Initial Screening Criteria"], float) else None

    ## Getter Local Exist
    @property
    def local_exist(self):
        return self._getLocalExist(self.gdb_path, self.table_name)
    
    ## Getter Service Exist
    @property
    def service_exist(self):
        return self._getServiceExist(self.gis_conn, self.agol_item_id)
    
    @property
    def md_title(self):
        return self._getGdbItemMetadata("title")
    
    @property
    def md_summary(self):
        return self._getGdbItemMetadata("summary")
    
    @property
    def md_description(self):
        return self._getGdbItemMetadata("description")
    
    @property
    def md_credits(self):
        return self._getGdbItemMetadata("credits")
    
    @property
    def md_accessConstraints(self):
        return self._getGdbItemMetadata("accessConstraints")
    
    @property
    def md_tags(self):
        return self._getGdbItemMetadata("tags")


    ### Row Validation ###
    def _validateRow(self, row, index, **kwargs):
        if not os.path.exists(kwargs["gdb_path"]):
            raise ValueError(f"File GDB Path: {kwargs['gdb_path']} does not exist.")
        
        if self.agol_item_id and not self.gis_conn.content.get(self.agol_item_id):
            raise ValueError(f"The input at index: {index} 'AGOL Item ID' is invalid.")
        
        if self._checkSpecialChar(row["Table Name"]):
            raise ValueError(f"The input at index: {index} 'Table Name' Contains invalid Characters.")
        
        if not self._getLocalExist(kwargs["gdb_path"], row["Table Name"]):
            raise ValueError(f"The input at index: {index} 'Table Name' Does Not Exist.")
        
        
        
    @staticmethod
    def _getLocalExist(gdb_path, table_name):
        arcpy.env.workspace = gdb_path
        if not gdb_path:
            return False


        item_list = []
        datasets = [d for d in arcpy.ListDatasets(feature_type="Feature")]
        datasets.append(None)
        [item_list.append(os.path.join(gdb_path, featureclass)) for dataset in datasets for featureclass in arcpy.ListFeatureClasses(feature_dataset=dataset)]
        [item_list.append(os.path.join(gdb_path, raster)) for raster in arcpy.ListRasters()]

        if os.path.join(gdb_path, table_name) in item_list:
            return True
        else:
            return False

    @staticmethod
    def _getServiceExist(gis_conn, item_id):
        if type(item_id) == float or not item_id:
            return False

        result = gis_conn.content.get(item_id)
        
        if result:
            return True
        
        else:
            return False



    ### AGOL Service Methods ###
    def getServiceObject(self):
        item_id = self.agol_item_id
        if not item_id:
            return None
        else:
            result = self._gis_conn.content.get(item_id)
            if result:
                return result
            else:
                return None
    

    ### Metadata Methods ###
    def _getGdbItemMetadata(self, category):
        md_ = md.Metadata(self.gdb_item_path)
        
        return getattr(md_, category)


    def createServiceMetadataDictionary(self):
        out_dict = {
            "description":self.md_description,
            "snippet":self.md_summary,
            "tags":self.formatTags_list(),
            "accessInformation":self.md_credits,
            "licenseInfo":self.md_accessConstraints
        }

        return out_dict
    

    def formatTags_list(self):
        if type(self.md_tags) == str:
            tags = self.md_tags.split(",")

        elif type(self.md_tags) == float or self.md_tags is None:
            tags = []

        elif type(self.md_tags) == list:
            tags_cleaned = [t.strip() for t in self.md_tags]
            tags_sorted =  sorted(tags_cleaned)
            tags = ",".join(tags_sorted)
            tags = ",".join(self.md_tags)

        formatted_tags = [t.strip() for t in tags]
        
        return formatted_tags
    

    def formatTags_str(self):
        if type(self.md_tags) == list:
            tags_cleaned = [t.strip() for t in self.md_tags]
            tags_sorted =  sorted(tags_cleaned)
            tags = ",".join(tags_sorted)
            #tags = ",".join(self.md_tags)

        elif type(self.md_tags) == float or self.md_tags is None:
            tags = None

        elif type(self.md_tags) == str:
            tags_list = self.md_tags.split(",")
            tags_cleaned = [t.strip() for t in tags_list]
            tags_sorted =  sorted(tags_cleaned)
            tags = ",".join(tags_sorted)
            
        formatted_tags = tags
        
        return formatted_tags
    
    def formatCredits(self):

        return f"Data Created by Safer Project Team - Data Source: {self.provider}"
    
    def formatSummary(self):
        if not self.webapp_category:
            return "This dataset was used in the development of the Safer project, but does not need to be published to the AGOL for web app purposes."
        
        else:
            return f"This dataset was requested by SMEs for the {self.webapp_category} web app and map figure production."
        
    def formatAccessConstraints(self):

       return "The Safer Program Hub is offered solely as a convenience to authorized users. It is provided as is and as available and neither HCFCD nor any other person or entity makes any warranty whatsoever regarding it or the information it contains, including but not limited to warranties of accuracy, availability, currency, completeness, non-infringement, or fitness for a particular purpose. By accessing or using it you acknowledge and agree to all of the foregoing."
        
    def formatTitle(self):
        if self.data_name:
            return self.data_name
        else:
            return self.table_name
        
    ### Utility Methods ###
    @staticmethod
    def _checkSpecialChar(string):
        """
        Purpose: Checks for Special characters from a string. 
        """
        string = str(string)
        count = 0
        scs = ':<>–/\" |?*\'%);(^#@!&-'
        for char in string:
            if char in scs:
                count+=1
        if count > 0:
            return True
        else:
            return False
        

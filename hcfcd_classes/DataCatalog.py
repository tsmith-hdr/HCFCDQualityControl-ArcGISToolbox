import arcpy
import os
import requests


class DataCatalogRow():
    def __init__(self, c_row, index,gdb_directory, master_gdb_name, gis_conn):
        self._validateRow(c_row, index, master_gdb_name=master_gdb_name, gdb_directory=gdb_directory)
        
        self._excel_index = index + 2
        self._gis_conn = gis_conn
        self._table_name = c_row["GDB File Name"]
        self._spatial_gdb = self._formatGdbName(c_row['Spatial GDB']) if not isinstance(c_row['Spatial GDB'], float) else None
        self._master_gdb = self._formatGdbName(master_gdb_name) if not isinstance(master_gdb_name, float) else None
        self._gdb_directory = gdb_directory
        self._agol_link = c_row["AGOL Link"] if not isinstance(c_row["AGOL Link"], float) else None
        self._datasource = c_row["Data Source"]
        self._webapp_category = c_row["Web App Category"] if not isinstance(c_row["Web App Category"], float) else None
        self._spatial_exist = self._getSpatialExist(self.getGdbPath("Spatial"), self._table_name)
        self._master_exist = self._getMasterExist(self.getGdbPath("Master"), self._table_name)
        self._service_exist = self._getServiceExist(gis_conn, self.getItemId())
        self._tags = c_row["Tags"]
        self._summary = c_row["Metadata-Summary"] if not isinstance(c_row["Metadata-Summary"], float) else None
        self._md_title = c_row["AGOL Title Name"] if not isinstance(c_row["AGOL Title Name"], float) else c_row["Common Name"]
        self._md_summary = self._formatSummary()
        self._md_description = c_row["Metadata - Description"] if not isinstance(c_row["Metadata - Description"], float) else None
        self._md_credits = self._formatCredits()
        self._md_accessConstraints = self._formatAccessConstraints()

    ################ Getter/Setters ################
    
    ## Getter Excel Index
    @property
    def excel_index(self):
        return self._excel_index
    
    ## Getter GIS Connection Index
    @property
    def gis_conn(self):
        return self._gis_conn
    
    ## Getter Table Name
    @property
    def table_name(self):
        return self._table_name

    ## Getter Spatial GDB
    @property
    def spatial_gdb(self):
        return self._formatGdbName(self._spatial_gdb)
    
    ## Getter Master GDB
    @property
    def master_gdb(self):
        return self._formatGdbName(self._master_gdb)

    ## Getter GDB Directory Path
    @property
    def gdb_directory(self):
        return self._gdb_directory
    
    @property
    def agol_link(self):
        return self._agol_link

    @property
    def datasource(self):
        return self._datasource
        
    @property
    def webapp_category(self):
        return self._webapp_category

    ## Getter Spatial Exist
    @property
    def spatial_exist(self):
        return self._spatial_exist
    
    ## Getter Master Exist
    @property
    def master_exist(self):
        return self._master_exist
    
    ## Getter Service Exist
    @property
    def service_exist(self):
        return self._service_exist
    
    @property
    def tags(self):
        return self._tags
    
    @property
    def summary(self):
        return self._summary
    
    @property
    def md_title(self):
        return self._md_title
    
    @property
    def md_summary(self):
        return self._md_summary
    
    @property
    def md_description(self):
        return self._md_description
    
    @property
    def md_credits(self):
        return self._md_credits
    
    @property
    def md_accessConstraints(self):
        return self._md_accessConstraints


    ### Row Validation ###
    def _validateRow(self, row, index, **kwargs):
        if self._checkSpecialChar(row["GDB File Name"]):
            raise ValueError(f"The input at index: {index} 'GDB File Name' Contains Invalid Characters.")
            
        if self._checkSpecialChar(row["Spatial GDB"]):
            raise ValueError(f"The input at index: {index} 'Spatial GDB' Contains Invalid Characters.")
            
        if self._checkSpecialChar(kwargs["master_gdb_name"]):
            raise ValueError(f"The input at index: {index} 'Master GDB Name' Contains Invalid Characters.")
        
        if not os.path.exists(kwargs["gdb_directory"]):
            raise ValueError(f"File GDB Directory: {kwargs['gdb_directory']} does not exist.")
        
        if not isinstance(row["AGOL Link"], float):
            if not row["AGOL Link"].startswith("http") or requests.get(row["AGOL Link"]).status_code != 200:
                raise ValueError(f"The input at index: {index} 'AGOL Link' is invalid.")
        

            
    ### File Path Methods ###
    def getGdbPath(self, gdb_type):
        if gdb_type.lower() not in ["spatial", "master"]:
            raise ValueError("The 'gdb_type' needs to be either 'Spatial' or 'Master'")
        
        if not self._spatial_gdb:
            return None
        
        elif gdb_type.lower() == "spatial":
            return os.path.join(self._gdb_directory, self._spatial_gdb)

        else:
            return os.path.join(self._gdb_directory, self._master_gdb)


    def getFilePath(self, gdb_type):
        gdb_path = self.getGdbPath(gdb_type) 
        
        if gdb_type.lower() not in ["spatial", "master"]:
            raise ValueError("The 'gdb_type' needs to be either 'Spatial' or 'Master'")
        
        if not gdb_path:
            return None
        else:
            file_path = os.path.join(self.getGdbPath(gdb_type),self._table_name)
            return file_path


    @staticmethod
    def _formatGdbName(gdb_name):
        #if type(gdb_name) == float:
        if not gdb_name:
            return None
        
        if gdb_name:
            if not gdb_name.endswith(".gdb"):
                return f"{gdb_name}.gdb"
            else:
                return gdb_name
            
        else:
            return None
        
    @staticmethod
    def _getSpatialExist(gdb_path, table_name):
        #gdb_path = self.getGdbPath("Spatial")

        #if arcpy.Exists(os.path.join(gdb_path, self._table_name)):
        if not gdb_path:
            return False
        
        elif arcpy.Exists(os.path.join(gdb_path, table_name)):
            return True
        
        else:
            return False
        
    @staticmethod
    def _getMasterExist(gdb_path, table_name):
        #gdb_path = self.getGdbPath("Master")
        if not gdb_path:
            return False

        #if arcpy.Exists(os.path.join(gdb_path, self._table_name)):
        elif arcpy.Exists(os.path.join(gdb_path, table_name)):
            return True
        

        else:
            return False
    @staticmethod
    def _getServiceExist(gis_conn, item_id):
        if not item_id:
            return False
        
        result = gis_conn.content.get(item_id)
        
        if result:
            return True
        
        else:
            return False


    ### AGOL Service Methods ###
    def getServiceObject(self):
        item_id = self.getItemId()
        if not item_id:
            return None
        else:
            result = self._gis_conn.content.get(item_id)
            if result:
                return result
            else:
                return None
    
    def getItemId(self):
        if not self._agol_link:
            return None
        
        elif "=" not in self._agol_link:
            raise ValueError(f"AGOL Link at index {self._excel_index} does not have '='")
            
        elif self._agol_link:
            return self._agol_link.split("=")[1].split("#")[0]
        

        
    def getAgolPortal(self):
        if not self._agol_link:
            return None
        elif self._agol_link:
            return self._agol_link.split("/home")[0]   
         

    ### Metadata Methods ###
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
        if type(self._tags) == str:
            tags = self._tags.split(",")
        elif type(self._tags) == float:
            tags = []
            
        formatted_tags = [t.strip() for t in tags]
        
        return formatted_tags
    

    def formatTags_str(self):
        if type(self._tags) == list:
            tags_cleaned = [t.strip() for t in self._tags]
            tags_sorted =  sorted(tags_cleaned)
            tags = ",".join(tags_sorted)
            tags = ",".join(self._tags)

        elif type(self._tags) == float:
            tags = None

        elif type(self._tags) == str:
            tags_list = self._tags.split(",")
            tags_cleaned = [t.strip() for t in tags_list]
            tags_sorted =  sorted(tags_cleaned)
            tags = ",".join(tags_sorted)
            
        formatted_tags = tags
        
        return formatted_tags
    
    def _formatCredits(self):

        return f"Data Created by Cascadia Project Team - Data Source: {self._datasource}"
    
    def _formatSummary(self):
        if self._summary:
            return self._summary
        
        elif not self._webapp_category and not self._summary:
            return "This dataset was used in the development of the Cascadia project, but does not need to be published to the AGOL for web app purposes."
        
        else:
            return f"This dataset was requested by SMEs for the {self._webapp_category} web app and map figure production."
        
    def _formatAccessConstraints(self):

       return "The Cascadia High-Speed Rail and I-5 Program Hub is offered solely as a convenience to authorized users. It is provided as is and as available and neither WSDOT nor any other person or entity makes any warranty whatsoever regarding it or the information it contains, including but not limited to warranties of accuracy, availability, currency, completeness, non-infringement, or fitness for a particular purpose. By accessing or using it you acknowledge and agree to all of the foregoing."
        
        
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
        

        
#######################################################################################################################################################
## Logging
import logging
logger = logging.getLogger(f"root.arc")
#######################################################################################################################################################

import sys
import os
from pathlib import Path
from datetime import datetime

import arcpy
from arcgis.gis import GIS, ItemTypeEnum

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from src.constants.values import *
################################################################################################################################################################



def checkSource(gis_conn:GIS, source_type:str, source_item:str)->bool:
    if source_type.lower() == "folder":
        return True if gis_conn.content.folders.get(source_item) else False
        
    elif source_type.lower() == "group":
        return True if gis_conn.groups.get(source_item) else False
    
    elif source_type.lower() not in ["folder","group", "catalog"]:
        logger.error(f"Incorrect 'source' variable")
        raise ValueError(f"Incorrect 'source' variable. Must be 'folder', 'group', or 'content'")


def generateItemList(gis_conn:GIS, source_type:str, include_exclude_flag:str="all",source_list:list=None, include_exclude_list:list=None)->list:
    '''
    
    Input Parameters
    -gis_conn : GIS Connection Object
    - source : This is the place were the items are searched for. The options are;
    ~~ "folder" : Specific Folders *These folders can only be folder that account being run 
    ~~ "group" : Named Portal Groups
    ~~ "catalog" : The entire content library
    - include_exclude_flag : Specify if the items specified  should be included or excluded
    ~~ "all" (Default) : Using this flag, all of the items within the group or portal will be included in the Item List
    ~~ "include" : these item id's 
    '''
    item_id_list = []
    item_list = []

    search_method = {
        "folder":gis_conn.content.folders.get,
        "group": gis_conn.groups.get,
        'catalog': gis_conn.content.search
    }

    
    
    if source_list:
        for source in source_list:
            logger.info(f"Source: {source}")
            if checkSource(gis_conn, source_type, source) and source_type in ['folder', 'group']:
                content_list = search_method[source_type.lower()](source).list(item_type=ItemTypeEnum.FEATURE_SERVICE.value) if source_type.lower() == 'folder' else [c for c in search_method[source_type.lower()](source).content() if c.type == "Feature Service"]

                if include_exclude_flag.lower() == "include":
                    [item_list.append(i) for i in content_list if i.id in include_exclude_list and i.id not in item_id_list]
                elif include_exclude_flag.lower() == "exclude":
                    [item_list.append(i) for i in content_list if i.id not in include_exclude_list and i.id not in item_id_list]
                else:
                    [item_list.append(i) for i in content_list if i.id not in item_id_list]
    else:
        [item_list.append(i.id) for i in search_method["catalog"]("", max_items=-1) if i.id not in item_id_list]



    return item_list
#######################################################################################################################################################
## Logging
import logging
logger = logging.getLogger(__name__)
#######################################################################################################################################################
## Libraries
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup
from bs4.element import Tag

import arcpy.metadata as md

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))


from src.classes.DataCatalog import DataCatalogRow
from src.constants.values import *


#######################################################################################################################################################
## Functions
def updateMetadataObjects(row_obj:DataCatalogRow)->None:
    """
    This 
    """
    if row_obj.local_exist:
        try:
            md_ = md.Metadata(row_obj.gdb_item_path)

            logger.info("-- Updating Master Metadata")
            
            md_.title = row_obj.formatTitle()
            md_.description = row_obj.md_description
            md_.summary = row_obj.formatSummary()
            md_.tags = row_obj.formatTags_str()
            md_.credits = row_obj.formatCredits()
            md_.accessConstraints = row_obj.formatAccessConstraints()

            md_.save()
        except Exception as e:
            logger.warning(f"!! Failed to update Metadata...{e}")

    if row_obj.service_exist:
        try:
            logger.info("-- Updating Service Metadata")

            item = row_obj.getServiceObject()
            print(item.id, item)
            print(f"Updating Service")
            print(row_obj.createServiceMetadataDictionary())
            item.update(item_properties=row_obj.createServiceMetadataDictionary())

        except Exception as e:
            logger.warning(f"!! Failed to update Metadata...{e}")



    return 



def getMetadata(row_obj:DataCatalogRow, md_items:list, text_type:str)->dict:

    out_dictionary = {}

    local_md_obj =md.Metadata(row_obj.gdb_item_path)
    service_obj = row_obj.getServiceObject()
    
    local_exist = row_obj.local_exist
    service_exist = row_obj.service_exist

    out_dictionary[f"Local - Exist"] = local_exist
    out_dictionary[f"Service - Exist"] = service_exist

    for md_item in md_items:
        if not local_exist:
            local_md_attr = "Dataset Doesn't Exist"
        else:
            if hasattr(local_md_obj, md_item):
                local_md_attr = _formatMdItems(getattr(local_md_obj, md_item),md_item, text_type) if getattr(local_md_obj, md_item) else "Missing"

        if not service_exist:
            service_md_attr = "Dataset Doesn't Exist"
        else:
            if hasattr(service_obj, SERVICE_ITEM_LOOKUP[md_item]):
                service_md_attr = _formatMdItems(getattr(service_obj, SERVICE_ITEM_LOOKUP[md_item]),SERVICE_ITEM_LOOKUP[md_item], text_type) if getattr(service_obj, SERVICE_ITEM_LOOKUP[md_item]) else "Missing"



        out_dictionary[f"Local - {md_item}"] = local_md_attr
        out_dictionary[f"Service - {md_item}"] = service_md_attr

        
        local_md_item_check = _cleanCheckText(local_md_attr) if local_md_attr else None
        service_md_item_check = _cleanCheckText(service_md_attr) if service_md_attr else None


        check_list = [i for i in [local_md_item_check, service_md_item_check] if i is not None and i != "dataset doesn't exist"]
        check_set = set(check_list)
        result = len(check_set)

        if result == 1 and [i for i in check_list][0] == "missing":
            check_bool = False
            
        elif result <= 1:
            check_bool = True

        else:
            check_bool = False

        out_dictionary[f"{md_item} - Match"] = check_bool

    return out_dictionary



        
def _formatMdItems(text:str, md_item:str, text_type:str)->str:
    """
    Using ReGex to strip HTML Tags from the Description, Summary, and Access Constraints.
    The Item Tags are also formatted from a string to a list and all spaces are striped and the list is sorted.
    """

    if text and text_type == "Plain" and md_item in ["description", "accessConstraints", "licenseInfo"]:
        bs = BeautifulSoup(text,'html.parser')

        a_tags = bs.find_all('a', href=True)
        for a_tag in a_tags:
            if a_tag.contents:
                a_tag_contents = a_tag.contents[0]

                if isinstance(a_tag.contents[0], Tag):
                    a_tag_contents = a_tag.contents[0].text
                
                if not a_tag_contents:
                    new_content = f"{a_tag['href']}"
                elif a_tag_contents.startswith("http"):
                    new_content = f"{a_tag['href']}"
                else:
                    new_content = f"{a_tag_contents} ({a_tag['href']})"

                a_tag.contents[0].replace_with(new_content)

            else:
                logger.warning(f"!! HTML Description/AccessConstraint/LicenseInfo is missing <a> tag content.")

        clean_text = bs.get_text()
        #clean_text = re.sub(r'<.*?>', '', new_text)
        
        
    elif text and md_item == 'tags':
        if type(text) == str:
            tag_list = text.split(",")

        if type(text) == list:
            tag_list = text

        cleaned_list = [t.strip() for t in tag_list]

        sorted_list = sorted(cleaned_list)

        clean_text = ",".join(sorted_list)

        
    else:
        clean_text = text


    return clean_text
    

def _cleanCheckText(text):
    notags_text = re.sub(r'<.*?>', '', text)
    lower_text = notags_text.lower()
    
    #nofollow_text = lower_text.replace(" rel='nofollow ugc'", "")
    standard_quotes = lower_text.replace('"',"'")
    text_strip = standard_quotes.strip()
    clean_text = text_strip
    
    return clean_text


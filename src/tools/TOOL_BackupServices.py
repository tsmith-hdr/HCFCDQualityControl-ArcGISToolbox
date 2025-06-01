import os
import re
import sys
import logging
import shutil
import pandas as pd
from pathlib import Path
from zipfile import ZipFile


import arcpy
from arcpy import metadata as md

from arcgis.gis import GIS, ItemTypeEnum, Item

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.constants.values import DATETIME_STR
from src.constants.paths import LOG_DIR, OUTPUTS_DIR
from src.functions import utility
########################################################################################################################################
## Logging ## Don't Change

log_file =os.path.join(LOG_DIR, "BackupServices",f"BackupServices_{DATETIME_STR}.log")

logging.basicConfig(filename=log_file, filemode="w",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

########################################################################################################################################
arcpy.env.overwriteOutput=True



def createFeatureDataset(gdb_path:str, dataset_name:str, spatial_reference:arcpy.SpatialReference)->None:
    arcpy.env.workspace = str(gdb_path)
    formatted_name = dataset_name.translate({ord(c): "" for c in "!@#$%^&*()[] {};:,./<>?\|`~-=_+"})
    if formatted_name not in [d for d in arcpy.ListDatasets(feature_type="Feature")]:
        arcpy.AddMessage(f"Creating Feature Dataset: {formatted_name}...")
        arcpy.management.CreateFeatureDataset(out_dataset_path=gdb_path,
                                                out_name=formatted_name,
                                                spatial_reference=spatial_reference)

        
    return

def exportFeatureService(layer, gdb_path:str, folder_name:str, spatial_reference:arcpy.SpatialReference)->dict:
    arcpy.env.workspace = gdb_path
    out_dict = {}
    feature_names = [f for dataset in arcpy.ListDatasets(feature_type="Feature") for f in arcpy.ListFeatureClasses(feature_dataset=dataset)]
    layer_url = layer.url
    layer_name = layer.properties["name"]
    layer_id = layer.properties["serviceItemId"]
    formatted_layer_name = layer_name.translate({ord(c): "_" for c in "!@#$%^&*()[] {};:,./<>?\|`~-=_+"})
    count=1
    while True:
        if formatted_layer_name not in feature_names:
            break
        else:
            if count==1:
                formatted_layer_name = f"{formatted_layer_name}_{count}"
            else:
                formatted_layer_name = f"{formatted_layer_name.rsplit('_',1)[0]}_{count}"

            count+=1

        arcpy.AddMessage(formatted_layer_name)
    try:
        featureclass_path = os.path.join(gdb_path, folder_name, formatted_layer_name)
        with arcpy.EnvManager(outputCoordinateSystem=spatial_reference, preserveGlobalIds=True):
            arcpy.conversion.ExportFeatures(in_features=layer_url,
                                            out_features=featureclass_path)
    except Exception as f:
        arcpy.AddWarning(f"Layer Failed to Export:\n{layer_name:30s} {layer_id:30s}")
        

    out_dict = {"Feature Class Name":formatted_layer_name,"Feature Class Path":featureclass_path,"Layer Name":layer_name, "Layer URL":layer_url, "Service Item Id":layer_id}

    return out_dict

def updateFeatureClassMetadata(featureclass_dict:dict)->None:
    meta = md.Metadata(featureclass_dict["Feature Class Path"])
    meta.summary = f"Created as part of a backup on {DATETIME_STR.split('-')[0]} performed by {os.getlogin()}"
    meta.tags = f"Layer Name:{featureclass_dict['Layer Name']}, Layer URL:{featureclass_dict['Layer URL']}, Service Item Id:{featureclass_dict['Service Item Id']}"
    meta.credits = featureclass_dict["Credits"]
    meta.save()

    return

def formatIncludeExcludeList(gis_conn:GIS,input_list:list)->list:
    id_list = []
    for item_name in input_list:
        item_obj = gis_conn.content.search(f"title:{item_name}")[0]
        id_list.append(item_obj.id)

    return id_list

def getFolderObjs(gis_conn, include_exclude, include_exclude_list):
    if include_exclude.lower() == "exclude":
        return [folder for folder in gis_conn.content.folders.list() if folder.name not in include_exclude_list]
    elif include_exclude.lower() == "include":
        return [folder for folder in gis_conn.content.folders.list() if folder.name in include_exclude_list]
    else:
        return [folder for folder in gis_conn.content.folders.list()]



def main(gis_conn:GIS, gdb_directory:str,spatial_reference:str, excel_report:str,backup_dir:str,include_exclude:str=None, include_exclude_list:list=None, email_from:str=None, email_to:list=None)->None:
    df_list = []
    arcpy.AddMessage(f"Creating Local GDB...")
    local_gdb = arcpy.management.CreateFileGDB(out_folder_path=gdb_directory, 
                                               out_name=f"ServiceBackup_{DATETIME_STR.split('-')[0]}")
    arcpy.AddMessage(f"Local GDB Path: {local_gdb}")

    folder_objs = getFolderObjs(gis_conn, include_exclude, include_exclude_list)


    for folder in folder_objs:
        arcpy.AddMessage(f"AGOL Folder: {folder}")
        formatted_folder_name = folder.name.translate({ord(c): "" for c in "!@#$%^&*()[] {};:,./<>?\|`~-=_+"})
        arcpy.AddMessage(f"Formatted AGOL Folder Name: {formatted_folder_name}")
        item_list = [i for i in folder.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)]
        arcpy.AddMessage(f"AGOL Item Count: {len(item_list)}")
        if item_list:
            createFeatureDataset(gdb_path=str(local_gdb), dataset_name=formatted_folder_name, spatial_reference=spatial_reference)

        for item in item_list:
            arcpy.AddMessage(f"AGOL Item: {item}")
            arcpy.AddMessage(f"Layer Count: {len(item.layers)}")
            for layer in item.layers:
                out_dict = exportFeatureService(layer=layer,
                                                gdb_path=str(local_gdb),
                                                folder_name=formatted_folder_name,
                                                spatial_reference=spatial_reference)
                
            

                df_list.append(out_dict)
                out_dict["Credits"]=item.accessInformation
                updateFeatureClassMetadata(featureclass_dict=out_dict)

    arcpy.AddMessage(f"Compressing Local GDB Items...")
    with arcpy.EnvManager(workspace=str(local_gdb)):
        arcpy.management.CompressFileGeodatabaseData(str(local_gdb), lossless=True)
        uncompressed = [f for dataset in arcpy.ListDatasets(feature_type="Feature") for f in arcpy.ListFeatureClasses(feature_dataset=dataset) if not arcpy.Describe(f).isCompressed]
        compression_status = "Successful" if len(uncompressed) == 0 else "Not Successful"
    arcpy.AddMessage(f"Compression: {compression_status}")


    meta = md.Metadata(str(local_gdb))
    meta.summary = f"This File GDB is a backup of the Feature Services. Run by {os.getlogin()} using AGOL User {gis_conn.users.me.username}"

    param_dict = {
    "GIS Connection":gis_conn,
    "GIS User":gis_conn.users.me.username,
    "Local User":os.getlogin(),
    "Include/Exclude Flag":include_exclude,
    "Folder List":include_exclude_list,
    "Spatial Reference":str(spatial_reference.factoryCode),
    "Compression":compression_status
    }
    gdb_description = """"""
    for k, v in param_dict.items():
        gdb_description+=f"{k}: {v}\n"
    meta.description = gdb_description
    meta.save()

    arcpy.AddMessage(f"Creating Pandas Data Frames...")
    param_df = pd.DataFrame.from_dict(param_dict, orient="index", columns=["Value"])
    update_df = pd.DataFrame(df_list, columns=["Feature Class Name","Layer Name", "Service Item Id","Feature Class Path", "Layer URL"])
    failed_compress_df = pd.DataFrame(uncompressed, columns=["Feature Class Name"])

    arcpy.AddMessage(f"Exporting Pandas Data Frames...")
    try:
        with pd.ExcelWriter(excel_report) as writer:
            update_df.to_excel(writer, sheet_name="UpdatedItems", index=False)
            param_df.to_excel(writer, sheet_name="InputParams", header=True,index=True, index_label="Parameter")
            failed_compress_df.to_excel(writer, sheet_name="FailedCompress", index=False)
    except Exception as e:
        arcpy.AddError(f"Failed to Export Excel Report.\n{e}")

    arcpy.AddMessage(f"Zipping Local GDB and Excel Reports...")
    try:
        zipped = os.path.join(OUTPUTS_DIR, "BackupServices", f"BackupServices_{DATETIME_STR}.zip")
        with ZipFile(zipped, 'w') as zip:
            zip.write(str(local_gdb), os.path.basename(str(local_gdb)))
            zip.write(excel_report, os.path.basename(excel_report))
            arcpy.AddMessage('All files zipped successfully!')
    except Exception as r:
        arcpy.AddError(f"Failed to Zip Files.\n{r}")


    arcpy.AddMessage("Copying Zipped Folder...")
    shutil.copy(zipped, os.path.join(backup_dir, os.path.basename(zipped)))
    if os.path.exists(os.path.join(backup_dir, os.path.basename(zipped))):
        arcpy.AddMessage(f"Excel Report Has Been Exported to:\n{excel_report}")
    else:
        arcpy.AddError(f"Excel Report Failed to Export to:\n{excel_report}")

    if email_from:
        arcpy.AddMessage("Sending Email...")
        utility.sendEmail(sendTo=",".join(email_to), sendFrom=email_from, subject=f"Service Backup {DATETIME_STR.split('-')[0]}", message_text="Completed Backup", text_type="plain", attachments=[excel_report])
        
    
    arcpy.AddMessage(f"Opening Excel Report...")
    try:
        os.startfile(excel_report)
    except Exception as t:
        arcpy.AddWarning(f"Failed to Launch Excel")

    
    return
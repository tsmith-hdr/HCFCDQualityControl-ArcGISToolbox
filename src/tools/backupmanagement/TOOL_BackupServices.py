import os
import re
import sys
import logging
import shutil
import datetime
import pandas as pd
from pathlib import Path
from importlib import reload  
from zipfile import ZipFile


import arcpy
from arcpy import metadata as md

from arcgis.gis import GIS, ItemTypeEnum

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.constants.paths import LOG_DIR, OUTPUTS_DIR
from src.functions import utility
from src.classes.servicelayer import ServiceLayer
########################################################################################################################################
## Environments
arcpy.env.overwriteOutput=True
########################################################################################################################################
##Globals
DATETIME_STR = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
#############################################################################################################################
## Logging
reload(logging)
log_file =os.path.join(LOG_DIR, "BackupServices",f"BackupServices_{DATETIME_STR}.log")

logging.getLogger().disabled = True
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)

logger=logging.getLogger(__name__)
file_handler = logging.FileHandler(log_file, mode='w')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
logger.info(logger)
#############################################################################################################################
def createFeatureDataset(gdb_path:str, dataset_name:str, spatial_reference:arcpy.SpatialReference)->None:
    arcpy.env.workspace = gdb_path
    formatted_name = dataset_name.translate({ord(c): "" for c in "!@#$%^&*()[] {};:,./<>?\|`~-=_+"})
    if formatted_name not in [d for d in arcpy.ListDatasets(feature_type="Feature")]:
        arcpy.AddMessage(f"Creating Feature Dataset: {formatted_name}...")
        logger.info(f"Creating Feature Dataset: {formatted_name}...")
        arcpy.management.CreateFeatureDataset(out_dataset_path=gdb_path,
                                                out_name=formatted_name,
                                                spatial_reference=spatial_reference)
        

        
    return

# def exportFeatureService(layer, gdb_path:str, folder_name:str, spatial_reference:arcpy.SpatialReference)->dict:
#     arcpy.env.workspace = gdb_path
#     out_dict = {}
#     feature_names = [f for dataset in arcpy.ListDatasets(feature_type="Feature") for f in arcpy.ListFeatureClasses(feature_dataset=dataset)]
#     layer_url = layer.url
#     layer_name = layer.properties["name"]
#     layer_id = layer.properties["serviceItemId"]
#     formatted_layer_name = layer_name.translate({ord(c): "_" for c in "!@#$%^&*()[] {};:,./<>?\|`~-=_+"})
#     count=1
#     while True:
#         if formatted_layer_name not in feature_names:
#             break
#         else:
#             if count==1:
#                 formatted_layer_name = f"{formatted_layer_name}_{count}"
#             else:
#                 formatted_layer_name = f"{formatted_layer_name.rsplit('_',1)[0]}_{count}"

#             count+=1

#     try:
#         featureclass_path = os.path.join(gdb_path, folder_name, formatted_layer_name)
#         with arcpy.EnvManager(outputCoordinateSystem=spatial_reference, preserveGlobalIds=True):
#             arcpy.conversion.ExportFeatures(in_features=layer_url,
#                                             out_features=featureclass_path)
#     except Exception as f:
#         logger.error(f"{layer_name:30s} {layer_id:30s}")
#         arcpy.AddWarning(f"Layer Failed to Export:\n{layer_name:30s} {layer_id:30s}")
        

#     out_dict = {"Feature Class Name":formatted_layer_name,"Feature Class Path":featureclass_path,"Layer Name":layer_name, "Layer URL":layer_url, "Service Item Id":layer_id}

#     return out_dict

def updateFeatureClassMetadata(featureclass_dict:dict)->None:
    meta = md.Metadata(featureclass_dict["Feature Class Path"])
    meta.summary = f"Created as part of a backup on {DATETIME_STR.split('-')[0]} performed by {os.getlogin()}"
    meta.tags = f"Layer Name:{featureclass_dict['Layer Name']}, Layer URL:{featureclass_dict['Layer URL']}, Service Item Id:{featureclass_dict['Service Item Id']}"
    meta.credits = featureclass_dict["Service Credits"]
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



def main(gis_conn:GIS, gdb_directory:str,spatial_reference:arcpy.SpatialReference, excel_report:str,backup_dir:str,include_exclude:str=None, include_exclude_list:list=None, email_from:str=None, email_to:list=None)->None:
    logger.info(f"GIS Connection: {gis_conn}")
    logger.info(f"GDB Directory: {gdb_directory}")
    logger.info(f"Spatial Reference: {spatial_reference.factoryCode}")
    logger.info(f"Excel Report: {excel_report}")
    logger.info(f"Backup Directory: {backup_dir}")
    logger.info(f"Include/Exclude Flag: {include_exclude}")
    logger.info(f"Folder List: {include_exclude_list}")
    logger.info(f"Email From: {email_from}")
    logger.info(f"Email To: {email_to}")
    logger.info("~~"*100)
    logger.info("~~"*100)

    df_list = []

    logger.info(f"Creating Local File GDB...")
    local_gdb_name = os.path.join(gdb_directory, f"ServiceBackup_{DATETIME_STR.split('-')[0]}.gdb")
    arcpy.management.CreateFileGDB(out_folder_path=gdb_directory, 
                                    out_name=f"ServiceBackup_{DATETIME_STR.split('-')[0]}"
                                    )
    
    arcpy.env.workspace = local_gdb_name

    logger.info(f"Local GDB Path: {local_gdb_name}")

    folder_objs = getFolderObjs(gis_conn, include_exclude, include_exclude_list)
    logger.info(f"Folder Count: {len(folder_objs)}")


    for folder in folder_objs:
        logger.info(f"AGOL Folder: {folder}")
        dataset_name = folder.name.translate({ord(c): "" for c in "!@#$%^&*()[] {};:,./<>?\|`~-=_+"}) ## Removes any special characters


        logger.info(f"Formatted AGOL Folder Name: {dataset_name}")
        item_list = [i for i in folder.list(item_type=ItemTypeEnum.FEATURE_SERVICE.value)] ## We only want the Feature Services.

        logger.info(f"AGOL Item Count: {len(item_list)}")

        if item_list:
            ## We may have a folley for using hardcoding only one single spatial reference, but for most projects they only use one. When the layer is exported it will be projected to the stated Spatial Reference. 
            createFeatureDataset(gdb_path=local_gdb_name, dataset_name=dataset_name, spatial_reference=spatial_reference) 

        for item in item_list:
            logger.info(f"AGOL Item: {item}")
            logger.info(f"Layer Count: {len(item.layers)}")
            for layer in item.layers:
                sl = ServiceLayer(gis_conn, layer, item)
                logger.info(f"Layer: {sl.layerName}")
                out_dict = sl.exportLayer(out_workspace=os.path.join(local_gdb_name, dataset_name))

                out_dict["Folder Name"] = folder.name

                df_list.append(out_dict)
                #out_dict["Credits"]=item.accessInformation ## I am capturing the credits, because the editors are going to manually enter when they make any changes to the service in the Services Access Information Property
                
                updateFeatureClassMetadata(featureclass_dict=out_dict)


    ## Here we are compressing the file gdb this is a lossless function. We want to add this process to make sure that the archived records are unable to be editied.
    logger.info(f"Compressing Local GDB Items...")
    with arcpy.EnvManager(workspace=local_gdb_name):
        arcpy.management.CompressFileGeodatabaseData(local_gdb_name, lossless=True)
        uncompressed = [f for dataset in arcpy.ListDatasets(feature_type="Feature") for f in arcpy.ListFeatureClasses(feature_dataset=dataset) if not arcpy.Describe(f).isCompressed]
        compression_status = "Successful" if len(uncompressed) == 0 else "Not Successful"
    logger.info(f"Compression: {compression_status}")



    meta = md.Metadata(local_gdb_name)
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


    logger.info(f"Creating Pandas Data Frames...")
    param_df = pd.DataFrame.from_dict(param_dict, orient="index", columns=["Value"])
    update_df = pd.DataFrame(df_list, columns=["Feature Class Name","Layer Name", "Folder Name","Service Item Id","Feature Class Path", "Layer URL"])
    failed_compress_df = pd.DataFrame(uncompressed, columns=["Feature Class Name"])



    logger.info(f"Exporting Pandas Data Frames...")
    try:
        with pd.ExcelWriter(excel_report) as writer:
            update_df.to_excel(writer, sheet_name="UpdatedItems", index=False)
            param_df.to_excel(writer, sheet_name="InputParams", header=True,index=True, index_label="Parameter")
            failed_compress_df.to_excel(writer, sheet_name="FailedCompress", index=False)
    except Exception as e:

        logger.error(f"Failed to Export Excel Report. {e}")


    ## Here we are compress together the excel report and the local filegdb. zipping these items will make it more efficient to send from local machine to the backup directory. 
    logger.info(f"Zipping Local GDB and Excel Reports...")
    try:
        zipped = os.path.join(OUTPUTS_DIR, "BackupServices", f"BackupServices_{DATETIME_STR}.zip")
        with ZipFile(zipped, 'w') as zip:
            zip.write(local_gdb_name, os.path.basename(local_gdb_name))
            zip.write(excel_report, os.path.basename(excel_report))
            zip.write(log_file, os.path.basename(log_file))

            logger.info('All files zipped successfully!')
    except Exception as r:
        arcpy.AddError(f"Failed to Zip Files.\n{r}")
        logger.error(f"Failed to Zip Files.\n{r}")



    ## Copies the zipped folder of the local file gdb to the designated directory to hold the weekly backups. 
    ### If we want to I can add logic to unzip the folder...
    logger.info("Copying Zipped Folder...")
    try:
        shutil.copy(zipped, os.path.join(backup_dir, os.path.basename(zipped)))
    except Exception as u:
        logger.error(f"Failed Copy: {u}")

    # Checks if the zipped folder was successfully copied.
    if os.path.exists(os.path.join(backup_dir, os.path.basename(zipped))):
        logger.info(f"Excel Report Has Been Exported to: {excel_report}")
    else:
        logger.error(f"Excel Report Failed to Export to: {excel_report}")


    ## If the email from parameter is entered, there will be an attempt to send an email with the excel report and log file.
    if email_from:
        logger.info("Sending Email...")
        result = utility.sendEmail(sendTo=",".join(email_to), sendFrom=email_from, subject=f"Service Backup {DATETIME_STR.split('-')[0]}", message_text="Completed Backup", text_type="plain", attachments=[excel_report, log_file])
        logger.info(result)
    

    ## Trys to open the excel report. Logs warning if unable to open.
    logger.info(f"Opening Excel Report...")
    try:
        os.startfile(excel_report)
    except Exception as t:
        logger.warning(f"Failed to Launch Excel")
    return


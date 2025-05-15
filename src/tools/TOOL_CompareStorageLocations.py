#################################################################################################################################################################################################################
## Libraries
import os
import sys
import itertools
import pandas as pd
import logging
from pathlib import Path
import datetime

import arcpy
from arcgis.gis import GIS

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from src.constants.paths import ROOT_DIR, PORTAL_ITEM_URL
#################################################################################################################################################################################################################
## Logging ## Don't Change
#log_file = os.path.join(os.getcwd(),"ftp_achd.log")
log_file = Path(ROOT_DIR, "logs", "CompareStorageLocations","CompareStorageLocations.log")
logging.basicConfig(filename=log_file, filemode="w",format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("arcgis.gis._impl._portalpy").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
#################################################################################################################################################################################################################
#################################################################################################################################################################################################################
## Functions
def createServicesList(gis_conn:GIS)->list:
    """
    This function creates a list of all Feature Layer and Map Image Layer services in the AGOL Portal
    Args: GIS Connection
    Returns: List of AGOL Services
    """
    service_item_types = ["Feature Layer", "Map Image Layer"]
    logger.info(f"Creating Services List...")
    services_list = []
    for service_item_type in service_item_types:
        result_list = gis_conn.content.search(query="", item_type=service_item_type, max_items=-1)

        services_list = services_list + result_list

    return services_list

# def createSpatialDictionary(gdb_dir:Path, avoidance_list:list)->dict:
#     """
#     Function creates a dictionary of all the Feature Classes and Rasters in the Spatial File GDBs
#     Args: Directory of Spatial File GDBs, List of GDBs to Avoid
#     Returns: Dictionary of GDBs and their respective Feature Classes and Rasters
#     """
#     logger.info(f"Creating Spatial File GDB List...")

#     spatial_gdb_dictionary = {}

#     spatial_gdb_list = [os.path.join(gdb_dir, g) for g in os.listdir(gdb_dir) if g.endswith('.gdb') and g not in avoidance_list]

#     for gdb in spatial_gdb_list:
#         spatial_gdb_dictionary[gdb] = []

#         arcpy.env.workspace = gdb
#         if arcpy.env.workspace != gdb:
#             logger.error("!! Workspaces Don't Match !!")
#             sys.exit("!! Workspaces Don't Match !!")

#         fc_list = arcpy.ListFeatureClasses()
#         raster_list = arcpy.ListRasters()
#         item_list = fc_list + raster_list
#         logger.debug(item_list)

#         spatial_gdb_dictionary[gdb] = item_list

#     return spatial_gdb_dictionary

def createLocalList(gdb_path:Path)->list:
    """
    This function creates a list of all the Feature Classes and Rasters in the Master File GDB
    Args: Master File GDB
    Returns: List of Feature Classes and Rasters in the Master File GDB
    """
    logger.info(f"Creating Master File GDB List...")

    arcpy.env.workspace = str(gdb_path)

    if arcpy.env.workspace != str(gdb_path):
        logger.error("!! Workspaces Don't Match !!")
        sys.exit("!! Workspaces Don't Match !!")
    fc_list = []
    dataset_list = arcpy.ListDatasets(feature_type="Feature")+None
    for dataset in dataset_list:
        [fc_list.append(fc) for fc in arcpy.ListFeatureClasses(feature_dataset=dataset)]
    
    raster_list = arcpy.ListRasters()

    local_list = fc_list + raster_list
    logger.debug(local_list)

    return local_list



# def createCombinedDictionary(master_list:list, spatial_dictionary:dict, master_gdb:str)->dict:
#     """
#     This function combines the Master List and the Spatial Dictionary into a single dictionary
#     Args: Master List, Spatial Dictionary, Master GDB Name
#     Returns: Combined Dictionary
#     """
#     updated_spatial_dictionary = {}
#     for k,v in spatial_dictionary.items():
#         updated_spatial_dictionary[k] = v
#     updated_spatial_dictionary[master_gdb] = master_list

#     return updated_spatial_dictionary


def checkItem(item:str, item_list:list, item_type:str, check_list:list)->str:
    if item in check_list and item in item_list:
        return "Both"
    
    elif item in check_list and item not in item_list:
        return "Data Catalog Only"

    elif item not in check_list and item in item_list:
        return "Service Only"
        
    else:
        return False


#################################################################################################################################################################################################################
def main(gis_conn:GIS, gdb_path:Path, catalog_path:Path, excel_path:Path)->None:
    logger.info(f"Starting: {datetime.datetime.now()}")
    logger.info(f"Run by: {os.getlogin()}")
    logger.info(f"Run on: {datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    logger.info(f"Excel Report: {excel_path}")
    logger.info(f"Data Catalog: {catalog_path}")
    logger.info(f"FGDB Path: {gdb_path}")

    catalog_df = pd.read_excel(io=catalog_path, sheet_name="Inventory",header=0,names=None)
    catalog_df["Item_Tuple"] = list(zip(catalog_df["AGOL Item ID"], catalog_df["Table Name"]))

    services_df = catalog_df[catalog_df['AGOL Item ID']]
    services_df["Item_Tuple"] = list(zip(services_df["AGOL Item ID"], services_df["Table Name"]))

    logger.info(f"Building Input Dictionary...")

    services_list = createServicesList(gis_conn)

    local_list = createLocalList(gdb_path)


    combined_list = local_list + services_list


    input_dict = {"Service":{"item_list":services_list, "dataframe":services_df, "df_column":"Item_Tuple"},
                "Local":{"item_list":local_list, "dataframe":catalog_df, "df_column":"Table Name"},
                "LocalvService":{"item_list":combined_list, "dataframe":catalog_df, "df_column":"Item_Tuple"}
                }



    out_dfs = []
    

    for item_type in list(input_dict.keys()):
        logger.info(f"---- {item_type} ----")

        df_list = []

        item_list = input_dict[item_type]["item_list"]
        pandas_list = input_dict[item_type]["dataframe"][input_dict[item_type]["df_column"]].tolist()

        if item_type == "Service":
            _checked = []
            pandas_id_list = []
            for p in pandas_list:
                item_id = p[0]
                pandas_id_list.append(item_id)
            #pandas_id_list = [p[0].split("=")[1].replace("#overview","")[0] for p in pandas_list] ## Retrieves just the Item Id from the AGOL Portal Item URL
            agol_id_list = [i.id for i in item_list] ## Creates a list of Item Ids from the items on the AGOL Portal
            print(agol_id_list)
            for service in item_list:
                df_list.append([service.title, f"{PORTAL_ITEM_URL}{service.id}", checkItem(service.id, agol_id_list, item_type, pandas_id_list)])
                _checked.append(service.id)
            print(_checked)
            for item_id, name in pandas_list:
                if item_id not in _checked:
                    df_list.append([name, item_id, "Data Catalog Only"])



        # elif item_type == "Spatial":
        #     _checked = []
        #     for spatial_gdb, table_name_list in item_list.items():
        #         logger.info(f"--{spatial_gdb}")
        #         for table_name in table_name_list:

        #             df_list.append([table_name, os.path.basename(spatial_gdb), checkItem(table_name, table_name_list, item_type, pandas_list)])
        #             _checked.append(table_name)
            
        #     for table_name in master_list:
        #         if table_name not in _checked:
        #             df_list.append([table_name, os.path.basename(gdb_path), checkItem(table_name, master_list, item_type, pandas_list)])
        #             _checked.append(table_name)

        #     for table_name in pandas_list:
        #         if table_name not in _checked:
        #             df_list.append([table_name, "Not In GDB", checkItem(table_name, combined_list, item_type, pandas_list)])
        
        # elif item_type == "Master":
        #     combined_list = list(set(itertools.chain(pandas_list, item_list)))
        #     for table_name in combined_list:

        #         df_list.append([table_name, os.path.basename(gdb_path), checkItem(table_name, item_list, item_type, pandas_list)]) 

        elif item_type == "LocalvService":
            _checked = []
            service_list = input_dict["Service"]["item_list"]
            local_list = input_dict["Local"]["item_list"]
            for table_name in local_list:
                for table_name in local_list:

                    df_list.append([table_name, checkItem(table_name, service_list, item_type, local_list)])
                    _checked.append(table_name)

            for table_name in master_list:
                if table_name not in _checked:
                    df_list.append([table_name, os.path.basename(gdb_path), checkItem(table_name, spatial_list, item_type, master_list)])
                    _checked.append(table_name)

            for table_name in pandas_list:
                if table_name not in _checked:
                    df_list.append([table_name, "Not In GDB", checkItem(table_name, combined_list, item_type, pandas_list)])



        df = pd.DataFrame(df_list, columns=["Item Name", "Source","Existance"])
        
        out_dfs.append((df, item_type))


    logger.info(f"Exporting DataFrames to Excel...")
    with pd.ExcelWriter(excel_path) as writer:
        out_dfs[0][0].to_excel(writer, sheet_name=out_dfs[0][1], index=False)
        out_dfs[1][0].to_excel(writer, sheet_name=out_dfs[1][1], index=False)
        #out_dfs[2][0].to_excel(writer, sheet_name=out_dfs[2][1], index=False)
        out_dfs[3][0].to_excel(writer, sheet_name=out_dfs[3][1], index=False)

        
    logger.info(f"Formatting Excel Report...") 
    wb = openpyxl.load_workbook(excel_path)

    sheet_names = wb.sheetnames
    count = 1
    for sheet_name in sheet_names:
        ws = wb[sheet_name]

        
        if sheet_name in ws.tables:
            del ws.tables[sheet_name]
            
        table_dimensions = ws.calculate_dimension()
        
        tbl = Table(displayName=sheet_name, ref=table_dimensions)
        
        style = TableStyleInfo(name=f"TableStyleMedium{count+1}",showFirstColumn=True, showLastColumn=True, showRowStripes=True, showColumnStripes=False)
        
        tbl.tableStyleInfo = style
        ws.add_table(tbl)
        
        ws.column_dimensions["A"].width = 80
        ws.column_dimensions["B"].width = 100
        ws.column_dimensions["C"].width = 20
        

        count+=1
    wb.save(excel_path)

    del wb

    return
#######################################################################################################################################################################################################
## Libraries
import arcpy
from pathlib import Path
#######################################################################################################################################################################################################
#######################################################################################################################################################################################################


def main(items:list)->None:
    for item in items:
        item_desc = arcpy.Describe(item)

        if item_desc.dataType == "Workspace":
            arcpy.AddMessage(f"------ {item_desc.name} ------- ")
            arcpy.env.workspace = str(item)
            datasets = arcpy.ListDatasets(feature_type="Feature")
            datasets.append(None)
            for dataset in datasets:
                arcpy.AddMessage(f"--- {dataset} --- ")
                featureclasses = arcpy.ListFeatureClasses(feature_dataset=dataset)
                tables = arcpy.ListTables()
                search_list = featureclasses + tables
                for fc in search_list:
                    arcpy.AddMessage(f"-- {arcpy.Describe(fc).isCompressed} -- {fc}")

        elif item_desc.dataType == "FeatureDataset":
            arcpy.env.workspace = str(Path(item_desc.path, item_desc.name))
            featureclasses = arcpy.ListFeatureClasses()
            for fc in featureclasses:
                arcpy.AddMessage(f"-- {arcpy.Describe(fc).isCompressed} -- {fc}")
        
        elif item_desc.dataType in ["FeatureClass", "Table"]:
            arcpy.AddMessage(f"-- {item_desc.isCompressed} -- {item_desc.name}")
        
        else:
            arcpy.AddWarning(f"!! {item} is not a valid input")


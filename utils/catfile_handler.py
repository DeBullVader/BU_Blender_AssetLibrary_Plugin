
import bpy
from pathlib import Path
import shutil
import os
from uuid import uuid4
from . import addon_info
from bpy.app.handlers import persistent
def read_lines_sequentially(filepath):
    with open(filepath) as file:
        while True:
            try:
                yield next(file)
            except StopIteration:
                break

CATALOGS_FILENAME = "blender_assets.cats.txt"

def check_current_catalogs_file_exist():
        root_folder = Path(bpy.data.filepath).parent
        catalog_filepath= str(root_folder) + os.sep + CATALOGS_FILENAME
        if not os.path.exists(catalog_filepath):
            return False
        return True
    
def get_current_file_catalog_filepath():
        root_folder = Path(bpy.data.filepath).parent
        catalog_filepath= str(root_folder) + os.sep + CATALOGS_FILENAME
        # directory = os.path.dirname(bpy.data.filepath)
        file_path =str(root_folder) + os.sep
        # catalog_filepath= file_path + CATALOGS_FILENAME
        if not os.path.exists(catalog_filepath):
            catalog_filepath = copy_catalog_file(file_path)
            return catalog_filepath
        else:
            return catalog_filepath




def catalog_info_from_line(catalog_line):
    return catalog_line.split(":")




def has_catalogs(catalog_filepath):
    return catalog_filepath is not None and Path(catalog_filepath).exists()

def copy_catalog_file(file_path):
    context = bpy.context
    core_lib = addon_info.get_core_asset_library()
    catfile = CATALOGS_FILENAME
    current_filepath = file_path.removesuffix(catfile)
    shutil.copy(os.path.join(core_lib.path,catfile), os.path.join(current_filepath,catfile))
    for window in context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'FILE_BROWSER':
                with context.temp_override(window=window, area=area):
                    context.space_data.params.asset_library_ref = "ALL"
                    context.space_data.params.asset_library_ref = "LOCAL"
                    bpy.ops.asset.catalog_new()
                    bpy.ops.asset.catalog_undo()
        

        

def add_catalog_to_catalog_file(catalog_uuid, catalog_tree, catalog_name):
    catalog_filepath = get_current_file_catalog_filepath()
    with open(catalog_filepath, "a") as catalog_file:
        catalog_file.write(f"{str(catalog_uuid)}:{str(catalog_tree)}:{str(catalog_name)}\n")
        return

def ensure_catalog_exists(catalog_uuid, catalog_tree, catalog_name):
    catalog_filepath = get_current_file_catalog_filepath()
    if not has_catalogs(catalog_filepath):
        copy_catalog_file(catalog_filepath)
    if not is_catalog_in_catalog_file(catalog_uuid):
        add_catalog_to_catalog_file(catalog_uuid, catalog_tree, catalog_name)

def ensure_or_create_catalog_definition(tree):
    catalog_filepath = get_current_file_catalog_filepath()
    if not has_catalogs:
        copy_catalog_file(catalog_filepath)
    file_path = get_current_file_catalog_filepath()
    catalog_definition_lines_existing = list(iterate_over_catalogs(file_path))
    uuids_existing = [line.split(":")[0] for line in catalog_definition_lines_existing]
    catalog_trees_existing = [line.split(":")[1] for line in catalog_definition_lines_existing]
    with open(file_path, "a") as catalog_file:
        tree = str(tree)
        tree = tree.replace("\\", "/")
        if tree in catalog_trees_existing:
            uuid = uuids_existing[catalog_trees_existing.index(tree)]
        else:
            uuid = str(uuid4())
            catalog_name = tree.replace("/", "-")
            catalog_line = f"{uuid}:{tree}:{catalog_name}"
            catalog_file.write(catalog_line)
            catalog_file.write("\n")
            print(f"Created catalog definition {catalog_line} in {file_path}")
    return uuid

def is_catalog_in_catalog_file(uuid):
    return current_catalog_info_from_uuid(uuid) is not None

        
def current_catalog_info_from_uuid(uuid):
    catalog_filepath = get_current_file_catalog_filepath()
    for line in iterate_over_catalogs(catalog_filepath):
        this_uuid, tree, name = catalog_info_from_line(line)
        if this_uuid == uuid:
            return this_uuid, tree, name


def iterate_over_catalogs(catalog_filepath):
    folder = Path(catalog_filepath)
    catalogs =[]
    with folder.open() as f:
        for line in f.readlines():
            if line.startswith(("#", "VERSION", "\n")):
                continue
            cats =line.split("\n")[0]
            catalogs.append(cats)
        return catalogs
    


def catalog_line_from_uuid(uuid):
    catalog_filepath = get_current_file_catalog_filepath()
    for line in iterate_over_catalogs(catalog_filepath):
        this_uuid, _, _ = catalog_info_from_line(line)
        if this_uuid == uuid:
            return line

def remove_catalog_by_uuid(catalog_filepath,uuid):
    with open(catalog_filepath,'r') as catalog_file:
        lines = catalog_file.readlines()
    with open(catalog_filepath, "w") as catalog_file:
        for line in lines:
            if line.startswith(str(uuid)):
                continue
            catalog_file.write(line)

def get_current_file_catalogs():
    catalogs = []
    catalog_filepath = get_current_file_catalog_filepath()
    #print(catalog_filepath)
    if has_catalogs(catalog_filepath):
        for line in iterate_over_catalogs(catalog_filepath):
            uuid, tree, name = catalog_info_from_line(line)
            catalogs.append((uuid, tree, name))
    else:
        catalogs = [("",) * 3]
    return catalogs

def get_core_catalogs():
    context = bpy.context
    catalogs = []
    catalog_filepath = addon_info.get_core_cat_file()
    if has_catalogs(catalog_filepath):
        for line in iterate_over_catalogs(catalog_filepath):
            uuid, tree, name = catalog_info_from_line(line)
            catalogs.append((uuid, tree, name))
    else:
        catalogs = [("",) * 3]
    return catalogs

def compare_catalogs():
    added_cats_dict={}
    core_cats = get_core_catalogs()
    current_cats = get_current_file_catalogs()
    added_cats = [cat for cat in current_cats if cat not in core_cats]
    for uuid,tree,name in added_cats:
        added_cats_dict[tree]=uuid
    return added_cats_dict




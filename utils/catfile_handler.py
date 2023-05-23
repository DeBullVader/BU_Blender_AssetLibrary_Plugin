
import bpy
from pathlib import Path
import os
from uuid import uuid4
from . import addon_info

def read_lines_sequentially(filepath):
    with open(filepath) as file:
        while True:
            try:
                yield next(file)
            except StopIteration:
                break

class CatalogsHelper:
    CATALOGS_FILENAME = "blender_assets.cats.txt"

    def __init__(self):
        self.catalog_filepath = self.get_catalog_filepath()
    
    @classmethod
    def catalog_info_from_line(cls, catalog_line):
        return catalog_line.split(":")

    def get_catalog_filepath(self):
        root_folder = Path(bpy.data.filepath).parent
        catalog_filepath= str(root_folder) + os.sep + self.CATALOGS_FILENAME
        # print(f'this is  rootfolder : {root_folder}')
        # print(f'this is  catalog_filepath : {catalog_filepath}')
        if not os.path.exists(catalog_filepath):
        # if not catalog_filepath.exists():
            self.create_catalog_file(catalog_filepath)
            return catalog_filepath
        
        while not os.path.exists(catalog_filepath):
            if catalog_filepath.parent == catalog_filepath.parent.parent:  # Root of the disk
                return None
            catalog_filepath = catalog_filepath.parent.parent + os.sep + self.CATALOGS_FILENAME
        return catalog_filepath

    @property
    def has_catalogs(self):
        return self.catalog_filepath is not None and Path(self.catalog_filepath).exists()

    def create_catalog_file(self, filepath=None):
        if filepath is None:
            filepath = self.catalog_filepath
        with open(filepath, "w") as catalog_file:
            catalog_file.write("# This is an Asset Catalog Definition file for Blender.\n")
            catalog_file.write("#\n")
            catalog_file.write("# Empty lines and lines starting with `#` will be ignored.\n")
            catalog_file.write("# The first non-ignored line should be the version indicator.\n")
            catalog_file.write('# Other lines are of the format "UUID:catalog/path/for/assets:simple catalog name"\n')
            catalog_file.write("\n")
            catalog_file.write("VERSION 1\n")
            catalog_file.write("\n")

        print(f"Created catalog definition file at {filepath}")
        

    def add_catalog_to_catalog_file(self, catalog_uuid, catalog_tree, catalog_name):
        catalog_filepath = self.get_catalog_filepath(self)
        with open(catalog_filepath, "a") as catalog_file:
            catalog_file.write(f"{str(catalog_uuid)}:{str(catalog_tree)}:{str(catalog_name)}\n")
            return

    def ensure_catalog_exists(self, catalog_uuid, catalog_tree, catalog_name):
        if not self.has_catalogs:
            self.create_catalog_file()
        if not self.is_catalog_in_catalog_file(self,catalog_uuid):
            self.add_catalog_to_catalog_file(self,catalog_uuid, catalog_tree, catalog_name)

    def ensure_or_create_catalog_definition(self, tree):
        if not self.has_catalogs:
            self.create_catalog_file()
        catalog_definition_lines_existing = list(self.iterate_over_catalogs())
        uuids_existing = [line.split(":")[0] for line in catalog_definition_lines_existing]
        catalog_trees_existing = [line.split(":")[1] for line in catalog_definition_lines_existing]
        with open(self.catalog_filepath, "a") as catalog_file:
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
                print(f"Created catalog definition {catalog_line} in {self.catalog_filepath}")
        return uuid

    def is_catalog_in_catalog_file(self, uuid):
        return self.current_catalog_info_from_uuid(self,uuid) is not None

    def catalog_info_from_uuid(self, uuid):
        for line in self.iterate_over_catalogs(self):
            this_uuid, tree, name = self.catalog_info_from_line(line)
            if this_uuid == uuid:
                return this_uuid, tree, name
            
    def current_catalog_info_from_uuid(self, uuid):
        for line in self.iterate_over_current_catalogs(self):
            this_uuid, tree, name = self.catalog_info_from_line(line)
            if this_uuid == uuid:
                return this_uuid, tree, name
    
    def iterate_over_catalogs(self):
        context = bpy.context
        catfile = addon_info.get_cat_file(context)
        folder = Path(catfile)
        catalogs =[]
        with folder.open() as f:
            for line in f.readlines():
                if line.startswith(("#", "VERSION", "\n")):
                    continue
                cats =line.split("\n")[0]
                catalogs.append(cats)
            return catalogs
    def iterate_over_current_catalogs(self):
        context = bpy.context
        catfile = self.get_catalog_filepath(self)
        folder = Path(catfile)
        catalogs =[]
        with folder.open() as f:
            for line in f.readlines():
                if line.startswith(("#", "VERSION", "\n")):
                    continue
                # Each line contains : 'uuid:catalog_tree:catalog_name' + eol ('\n')
                # cats = line.split(":")[1].split("\n")[0]
                cats =line.split("\n")[0]
                catalogs.append(cats)
            return catalogs
        
    # def iterate_over_catalogs(self):
    #     for line in read_lines_sequentially(self.catalog_filepath):
    #         if line.startswith(("#", "VERSION", "\n")):
    #             continue
    #         yield line.split("\n")[0]

    def catalog_line_from_uuid(self, uuid):
        for line in self.iterate_over_catalogs():
            this_uuid, _, _ = self.catalog_info_from_line(line)
            if this_uuid == uuid:
                return line

    def remove_catalog_by_uuid(self, uuid):
        with open(self.catalog_filepath, "w") as catalog_file:
            for line in catalog_file.readlines():
                if line.startswith(str(uuid)):
                    continue
                catalog_file.write(line)

    @staticmethod
    def get_catalogs(filter_catalog=None,context=None):
        helper = CatalogsHelper()
        catalogs = []
        if helper.has_catalogs:
            for line in helper.iterate_over_catalogs():
                uuid, tree, name = helper.catalog_info_from_line(line)
                catalogs.append((uuid, tree, name))
        else:
            catalogs = [("",) * 3]
        # print(f'this is catalogs  {catalogs}')
        return catalogs
    
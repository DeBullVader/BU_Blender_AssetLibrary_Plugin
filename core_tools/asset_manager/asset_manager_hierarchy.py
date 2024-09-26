import bpy
class AssetHierarchy:
    def __init__(self, asset, asset_type):
        self.asset = asset
        self.asset_type = asset_type
        self.children = []
        self.minimized = False

def build_hierarchy(selected_assets, asset_type):
    hierarchy = []
    if asset_type == 'Objects':
        for obj in selected_assets:
            if obj.parent and obj.parent_type == 'OBJECT':
                parent_in_hierarchy = obj.parent in [h.asset for h in hierarchy]
                parent_in_hierarchy = next((h for h in hierarchy if h.asset.name == obj.parent.name), None)
                if parent_in_hierarchy:
                    parent_in_hierarchy.children.append(AssetHierarchy(obj, 'Objects'))
                   
                else:
                    obj_hierarchy = AssetHierarchy(obj.parent, 'Objects')
                    obj_hierarchy.children.append(AssetHierarchy(obj, 'Objects'))
                    hierarchy.append(obj_hierarchy)
            else:
                hierarchy.append(AssetHierarchy(obj, 'Objects'))
        # return [AssetHierarchy(asset, 'Object') for asset in selected_assets]
    
    elif asset_type == 'Materials':
        for obj in selected_assets:
            obj_hierarchy = AssetHierarchy(obj, 'Objects')
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    obj_hierarchy.children.append(AssetHierarchy(mat_slot.material, 'Materials'))
            if obj_hierarchy.children:
                hierarchy.append(obj_hierarchy)

    elif asset_type == 'Material Nodes':
        for obj in selected_assets:
            obj_hierarchy = AssetHierarchy(obj, 'Objects')
            for mat_slot in obj.material_slots:
                if mat_slot.material and mat_slot.material.node_tree:
                    mat_hierarchy = AssetHierarchy(mat_slot.material, 'Materials')
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == 'GROUP':
                            mat_hierarchy.children.append(AssetHierarchy(node, 'Material Nodes'))
                    if mat_hierarchy.children:
                        obj_hierarchy.children.append(mat_hierarchy)
            if obj_hierarchy.children:
                hierarchy.append(obj_hierarchy)

    elif asset_type == 'Geometry Nodes':
        for obj in selected_assets:
            obj_hierarchy = AssetHierarchy(obj, 'Objects')
            if obj.modifiers:
                for mod in obj.modifiers:
                    if mod.type == 'NODES':
                        obj_hierarchy.children.append(AssetHierarchy(mod.node_group, 'Geometry Nodes'))
                if obj_hierarchy.children:
                    hierarchy.append(obj_hierarchy)

    elif asset_type == 'Collections':
        unique_collections = []
        for obj in selected_assets:
            for collection in obj.users_collection:
                if collection.name in bpy.data.collections and collection not in unique_collections:
                    unique_collections.append(collection)
        return [AssetHierarchy(collection, 'Collections') for collection in unique_collections]
    return hierarchy
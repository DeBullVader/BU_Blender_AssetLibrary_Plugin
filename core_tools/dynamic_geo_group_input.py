import bpy
from bpy.app.handlers import persistent
from bpy.utils import register_classes_factory

##TODO: Add documentation
##TODO: add menu switch support 
##TODO: add custom properties to easy select which input to use for which option

    
class NODE_PT_custom_group_inputs(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Group"
    bl_label = "Interface"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        if snode is None:
            return False
        tree = snode.edit_tree
        if tree is None:
            return False
        if tree.is_embedded_data:
            return False
        if tree.type != 'GEOMETRY':
            return False
        
    def draw(self, context):
        layout = self.layout
        snode = context.space_data
        tree = snode.edit_tree
        col = layout.column()
        active_item = tree.interface.active
        if active_item is not None:
            layout.use_property_split = True
            layout.use_property_decorate = False
            if active_item.item_type == 'SOCKET':
                if tree.type == 'GEOMETRY':
                    if active_item.socket_type == "NodeSocketBool":
                        if 'INPUT' in active_item.in_out:
                            col.prop(active_item, 'is_switch', text="Is Switch")
def msgbus_callback(*args):
    
    # idx,mod,switch_sockets = args
    # switch =mod.node_group.interface.items_tree[idx]
    # print(switch.identifier)
    # state = mod[switch.identifier]  
    print("Switch changed!", args)
    # print(state)
    # This will print:
    # Something changed! (1, 2, 3)


def is_switch_callback(self,context):
    switch_sockets = []
    # owner = object()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for mod in bpy.context.object.modifiers:
        if mod.type != 'NODES':
            continue
        if mod:
            geo_mod = bpy.data.node_groups.get(mod.node_group.name)
            # print('geo_mod: ',mod.node_group.__dir__())
            item_tree = mod.node_group.interface.items_tree
            mod.node_group.interface_update(bpy.context)
            switch_sockets = [item for item in item_tree if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.socket_type == 'NodeSocketBool' and item.is_switch==True]
            for switch in switch_sockets:
                print('test',mod.node_group.nodes[0].outputs[switch.index].node.poll)
                print('test',mod.node_group.nodes[0].outputs[switch.index].node.socket_value_update)
                owner = mod
                subscribe_to = mod.node_group.nodes[0].outputs[switch.index]
                bpy.msgbus.subscribe_rna(
                    key=mod.node_group.nodes[0].outputs[switch.index].node.poll,
                    owner=None,
                    args=(),
                    notify=msgbus_callback,
                )
    # if mod:
    #     geo_mod = bpy.data.node_groups.get(mod.node_group.name)
    #     mod.node_group.interface_update(bpy.context)
    #     item_tree = mod.node_group.interface.items_tree
    #     switch_sockets = [item for item in item_tree if item.item_type == 'SOCKET' and item.in_out == 'INPUT' and item.socket_type == 'NodeSocketBool' and item.is_switch==True]
    #     # print('switch sockets: ',switch_sockets)
        
    #     if switch_sockets:
    #         #This doesnt work like this check https://blender.stackexchange.com/questions/224010/using-message-bus-to-trigger-events-based-on-custom-property-changes
    #         for idx,switch in enumerate(switch_sockets):
    #             print(switch.index)
               
    #             subscribe_to = bpy.types.GeometryNodeTree,str(switch.index)
    #             bpy.msgbus.subscribe_rna(
    #                 key=subscribe_to,
    #                 owner=owner,
    #                 args=(idx,mod,switch_sockets),
    #                 notify=msgbus_callback,
    #             )
        
    print('is switch callback')
    return

def update_visibility(mod,item_tree):
    
    print('updating visibility')
    for item in item_tree:
        if not item.item_type == 'SOCKET':
            continue
        if item.in_out == 'OUTPUT':
            continue
        if not item.socket_type == 'NodeSocketBool':
            continue
        if item.is_switch==True:
            switch_sockets.append(item)

    
    # for switch in switch_sockets:
    #     state = mod[switch.identifier]  
    #     print(switch.init_socket(type='NodeSocketBool').value)              
        # option1_sockets = [item for item in item_tree if item.description == switch.name + " option 1"]
        # option2_sockets = [item for item in item_tree if item.description == switch.name + " option 2"]
        # if option1_sockets:
        #     for socket in option1_sockets:
        #         socket.hide_in_modifier = not state
        # if option2_sockets:
        #     for socket in option2_sockets:
        #         socket.hide_in_modifier = state

@persistent
def GN_collapse_handler(dummy):
    # ub_node_groups = [ng for ng in bpy.data.node_groups if ng.name.startswith('UB_')]
    # input_nodes = [group for node in ub_node_groups for group in node.nodes if group.type == 'GROUP_INPUT']
      
    for mod in bpy.context.object.modifiers:
        if mod.type != 'NODES':
            continue
    # depsgraph = bpy.context.evaluated_depsgraph_get()
    # for update in depsgraph.updates:
    #     if update.id != bpy.context.object.evaluated_get(depsgraph):
    #         continue   
    #     print('evaluated_get: ',bpy.context.object.evaluated_get(depsgraph))
    #     update_visibility(mod,mod.node_group.interface.items_tree)


classes = (
    NODE_PT_custom_group_inputs, 
)
register_classes, unregister_classes = register_classes_factory(classes)
def register():
    register_classes()
    bpy.types.NodeTreeInterfaceSocketBool.is_switch = bpy.props.BoolProperty(name="Is Switch", default=False, update=lambda self,context:is_switch_callback(self,context))
    bpy.app.handlers.depsgraph_update_post.append(GN_collapse_handler)
    bpy.types.NODE_PT_node_tree_interface.append(NODE_PT_custom_group_inputs.draw)
    
def unregister():
    del bpy.types.NodeTreeInterfaceSocketBool.is_switch
    bpy.app.handlers.depsgraph_update_post.remove(GN_collapse_handler)
    bpy.types.NODE_PT_node_tree_interface.remove(NODE_PT_custom_group_inputs.draw)
    unregister_classes()

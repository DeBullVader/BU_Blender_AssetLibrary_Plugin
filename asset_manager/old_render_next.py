def render_next_asset(self, context):
        print('Rendering next previews')
        if not self.assets_to_render:
           print("No more assets to render")
           self.state = 'FINISHED'
           return
        print(f"{len(self.assets_to_render)} assets left to render")
        self.debug_render(context)
        asset = self.assets_to_render[0]
        try:
            
            current_pivot_transform =asset_bbox_logic.get_current_transform_pivotpoint()
            asset_bbox_logic.set_transform_pivot_point_to_bound_center()

            if context.scene.asset_props.asset_types == 'Objects':
                asset_copy = self.create_copy_of_current_asset(asset)
                if asset_copy.name not in self.preview_col.objects:
                    self.preview_col.objects.link(asset_copy)

                asset_copy =self.preview_col.objects.get(asset_copy.name)
                asset_copy.select_set(True)
                asset_copy.location = (0,0,0)

                asset_copy.rotation_euler = context.scene.asset_props.asset_example_rotation
                context.scene.camera.rotation_euler = context.scene.asset_props.render_camera_rotation
                scale_asset_to_render(context,context.scene,asset_copy)
                pivot_point =asset_bbox_logic.get_obj_center_pivot_point(asset)
                asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
                align_camera_to_selected_asset(context.scene.camera)
                asset.select_set(False)
                self.link_to_object_container(asset_copy)
                self.object_container.hide_render = False
                asset_to_render =self.object_container.objects.get(asset_copy.name)
                asset_to_render.hide_render = False

            if context.scene.asset_props.asset_types == 'Materials':
                shaderball=bpy.data.objects.get('UB_Shaderball')
                shaderball.data.materials.clear()
                shaderball.data.materials.append(asset)
                self.shader_ball_col.hide_render = False

            if context.scene.asset_props.asset_types == 'Collections':
                context.scene.camera.rotation_euler = context.scene.asset_props.render_camera_rotation
                source_col = bpy.data.collections.get(asset.name)
                for obj in source_col.objects:
                    obj.select_set(True)
                    obj.hide_render =False
               
                current_pivot_transform =asset_bbox_logic.get_current_transform_pivotpoint()
                asset_bbox_logic.set_transform_pivot_point_to_bound_center()

                col_scale_factor = asset_bbox_logic.calc_col_scale_factor(source_col)
                instance_obj = create_and_link_collection_instance(source_col)
                
                if instance_obj.name not in self.preview_col.objects:
                    self.preview_col.objects.link(instance_obj)

                instance_obj =self.preview_col.objects.get(instance_obj.name)
                instance_obj.rotation_euler = context.scene.asset_props.asset_example_rotation
                instance_obj.scale *= col_scale_factor
                bpy.context.view_layer.update()
               
                
                asset_bbox_logic.set_col_bottom_center(instance_obj,source_col,col_scale_factor)
                bpy.context.view_layer.update()
                instance_obj.location = Vector((0,0,0))

                pivot_point = asset_bbox_logic.get_col_center_pivot_point(source_col,col_scale_factor)

                for obj in source_col.objects:
                    obj.select_set(False)
                instance_obj.select_set(True)
                
                asset_bbox_logic.set_pivot_point_and_cursor(pivot_point)
                align_camera_to_selected_asset(context.scene.camera)
                
                self.link_to_object_container(instance_obj)
                instance_obj.select_set(False)
                bpy.context.view_layer.update()
                self.object_container.hide_render = False
                asset_to_render =self.object_container.objects.get(instance_obj.name)
                asset_to_render.hide_render = False
            
            if context.scene.asset_props.asset_types == 'Material Nodes':
                #Needs to be implemented
                pass
            if context.scene.asset_props.asset_types == 'Geometry Nodes':
                #Needs to be implemented
                pass
            
            

            asset_bbox_logic.restore_pivot_transform(current_pivot_transform)
            self.render_scene.render.filepath = self.asset_preview_path + self.preview_filenames[0]
            bpy.ops.render.render(scene='PreviewRenderScene', write_still=True,use_viewport=True)

        except Exception as e:
           print(f"Error rendering asset {asset.name}: {e}")
           self.cancelled('PreviewRenderScene', None)

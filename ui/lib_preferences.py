import bpy


def add_library_layout(self, context, greyout):
    layout = self.layout
    row = layout.row()
    row.label(text="Library file path setting")
    box = layout.box()
    box.prop(self,"lib_path")
    row = box.row()
    row.operator('bu.addlibrary', text = 'add library')
    row.enabled = greyout


def prefs_lib_reminder(self,context):
    def draw_warning(self,text):
        row = self.layout.row(align=True)
        if context.preferences.active_section == "ADDONS":
            row.alignment = "LEFT"
        else:
            row.alignment = "RIGHT"
        row.label(text=text, icon='ERROR')

    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name == "BU_AssetLibrary_Core":
            if context.preferences.active_section == "ADDONS":
                layout = self.layout
                add_library_layout(self, context, False)
                row = layout.row()
                row.label(text="Asset library location: " + lib.path, icon="CHECKMARK")
                
            return
        
    if context.preferences.active_section == "ADDONS":
        add_library_layout(self, context, True)
        draw_warning(
            self,
            'No asset library named "BU_AssetLibrary_Core", Please choose a directory above',
        )
    else:
        draw_warning(self, 'BU_AssetLibrary_Core: No asset library named "BU_AssetLibrary_Core", please create it!')           

def library_download_settings(self, context):
    lib_download_pref = bpy.context.preferences.addons['BU_Blender_AssetLibrary_Plugin'].preferences.automatic_or_manual
    layout = self.layout
    row = self.layout.row()
    row.label(text='Library download settings')
    print(lib_download_pref)
    box = layout.box()
    box.label(text='Do you want to automaticly download available assets?')
    row = box.row()
    row.prop(self, 'automatic_or_manual',expand=True)
    if lib_download_pref == 'automatic_download':
        box.label(text='Automatic will download and auto update the library when assets are available')
    else:
        box.label(text='Manual will setup thumbnails with empty blend files untill downloaded')
    row= box.row()
    row.operator('wm.downloadlibrary', text = 'Confirm Download Setting')
    

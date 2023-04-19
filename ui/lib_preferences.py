
def add_library_layout(self, context, greyout):
        row = self.layout.row()
        row.label(text="choose a path to store the library (thiss will be added to file paths)")
        row = self.layout.row()
        row.prop(self,"lib_path")
        col = row.column()
        col.operator('bu.addlibrary', text = 'add library')
        row.enabled = greyout


def prefs_lib_reminder(self,context):
    def draw_warning(self,text):
        row = self.layout.row(align=True)
        if context.preferences.active_section == "ADDONS":
            row.alignment = "CENTER"
        else:
            row.alignment = "RIGHT"
        row.label(text=text, icon='ERROR')

    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name == "BU_AssetLibrary_Core":
            if context.preferences.active_section == "ADDONS":
                add_library_layout(self, context, False)
                row = self.layout.row(align=True)
                row.alignment = "CENTER"
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
def ui(self, context, statusbar=True):
    props = context.window_manager.bu_props
    if props.progress_total:
        row = self.layout.row()
        row.prop(props,"progress_percent",text = props.progress_word, slider=True,)

        row.label(text = f' Amount of assets to download: {round(props.progress_total) }')
        row = self.layout.row()
        row.prop(props,'progress_downloaded_text', text = "Status: ")
        # if not props.progress_cancel:
            # row.operator("pha.cancel_download", text="", icon="CANCEL")
        if statusbar:
            self.layout.label(text="", icon="CHECKMARK")
        else:
            self.layout.separator()  # Space at end
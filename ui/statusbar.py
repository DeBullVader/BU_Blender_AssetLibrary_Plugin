
from threading import Thread, Event
from time import sleep
def ui(self, context, statusbar=True):
    props = context.window_manager.bu_props
    if props.progress_total:
        row = self.layout.row()
        row.prop(props,"progress_percent",text = props.progress_word, slider=True,)
    
        row.label(text = f' Amount of assets to download: {round(props.progress_total) }')
        row = self.layout.row()
        row.label( text = f" Status: {props.progress_downloaded_text}")
        # if not props.progress_cancel:
            # row.operator("pha.cancel_download", text="", icon="CANCEL")
        if statusbar:
            self.layout.label(text="", icon="CHECKMARK")
        else:
            self.layout.separator()

def ui_titlebar (self,context):
    props = context.window_manager.bu_props
    row = self.layout.row()
    if props.progress_total:
        row.label(text = f' Amount of assets to download: {round(props.progress_total) }')
        row.prop(props,"progress_percent",text = props.progress_word, slider=True,)
    if props.new_assets >= 1:
        row.label(text = f' There are {props.new_assets}  new assets available for download!!' )
    elif props.new_assets == 1:
        row.label(text = f' There is {props.new_assets} new asset available for download!!' )

    elif props.updated_assets >=1:
        row.label(text = f' There are {props.updated_assets} that have updates!!' )
    elif props.updated_assets ==1:
        row.label(text = f'{props.updated_assets} has an update!!' )
    elif props.new_assets == 0 and props.updated_assets ==0:
        row.label(text = f' Assets are up-to-date' )


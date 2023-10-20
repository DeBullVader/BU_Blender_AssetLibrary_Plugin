
from threading import Thread, Event
from time import sleep
import bpy

bpy.types.Scene.status_text = bpy.props.StringProperty(default="")

def get_status_texts(context,index):
    props = context.window_manager.bu_props
    status_texts = [
        f' ',
        f' Checking for updates...',
        f' All assets are up-to-date',
        f' There are {props.new_assets}  new assets available for download!!',
        f' There is {props.new_assets} new asset available for download!!',
        f' There are {props.updated_assets} that have updates!!',
        f'{props.updated_assets} has an update!!',
    ] 
    return status_texts[index] 
def ui(self, context, statusbar=True):
    props = context.window_manager.bu_props
    if props.progress_total:
        row = self.layout.row()
        row.prop(props,"progress_percent",text = props.progress_word, slider=True,)
    
        row.label(text = f' Amount of assets to download: {round(props.progress_total) }')
        row = self.layout.row()
        row.label( text = f" Status: {props.progress_downloaded_text}")
        if statusbar:
            self.layout.label(text="", icon="CHECKMARK")
        else:
            self.layout.separator()
def draw_progress(self, context):
    props = context.window_manager.bu_props
    layout = self.layout
    layout.label(text = context.scene.status_text)
    if props.progress_total:
        layout.prop(props,"progress_percent",text = props.progress_word, slider=True,)
        # self.layout.operator('wm.cancel_sync', text='Cancel Sync', icon='CANCEL')


def ui_titlebar (self,context):
    props = context.window_manager.bu_props
    row = self.layout.row()

    if props.progress_total:
        row.label(text = f' Amount of assets to download: {round(props.progress_total) }')
        row.prop(props,"progress_percent",text = props.progress_word, slider=True,)
    if props.new_assets > 1:
        row.label(text = get_status_texts(context,3))
    elif props.new_assets == 1:
        row.label(text = get_status_texts(context,4))
    elif props.updated_assets == 0:
        row.label(text = get_status_texts(context,2))
    elif props.updated_assets >=1:
        row.label(text = get_status_texts(context,5))
    elif props.updated_assets ==1:
        row.label(text = get_status_texts(context,6))



def ui_titlebar_upload (self,context):
    props = context.window_manager.bu_props
    row = self.layout.row()
    if props.progress_total:
        row.label(text = f' Amount of assets to Upload: {round(props.progress_total) }')
        row.prop(props,"progress_percent",text = props.progress_word, slider=True,)
    else:
        if props.assets_to_upload > 1:
            row.label(text = f' Processing Uploads' )
        elif props.assets_to_upload == 0:
            row.label(text = f' Select assets from the current file library to upload them' )


        


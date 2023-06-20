import bpy
from .. import icons
import textwrap

class BBS_Info_Panel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_INFO"
    bl_label = 'Baked Blender Suite Info'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BU Tools'

    def draw(self, context):
        i = icons.get_icons()
        layout = self.layout
        
        
        intro_text = 'The Baked Blender Pro Suite (BBPS) is an asset library that contains 3D models, materials, geometry node setups, particle systems, and eventually much more.'
        _label_multiline(
        context=context,
        text=intro_text,
        parent=layout
        )
        box = layout.box()
        split = box.split(factor = 0.3)
        row = split.row(align=True)

        box = row.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label( text = "Main social accounts!",)
        discord = box.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        twitter = box.operator('wm.url_open',text='Twitter',icon_value=i["twitter"].icon_id)
        reddit = box.operator('wm.url_open',text='Reddit',icon_value=i["reddit"].icon_id)
        row = split.row(align=True)
        box = row.box()
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label( text = "Our youtube has some handy beginner tutorials!",)
        youtube = box.operator('wm.url_open',text='Youtube',icon_value=i["youtube"].icon_id)
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="Whats new in Baked Blender Pro Suite V0.2.0",icon_value=i["bakeduniverse"].icon_id)
        update_video = box.operator('wm.url_open',text='Update V0.2.0',icon_value=i["youtube"].icon_id)
        row = box.row(align=True)
        row.alignment = 'CENTER'
        row.label(text="More information about BBPS is available at our Gitbook",icon_value=i["bakeduniverse"].icon_id)
        gitbook = box.operator('wm.url_open',text='Gitbook',icon='INFO')

        discord.url = 'https://discord.gg/bakeduniverse'
        twitter.url = 'https://twitter.com/BakedUniverse'
        youtube.url = 'https://youtube.com/@bakeduniverse'
        reddit.url = 'https://www.reddit.com/user/BakedUniverse/'
        update_video.url = 'https://www.youtube.com/watch?v=6cOQIpRq820'
        gitbook.url= 'https://bakeduniverse.gitbook.io/baked-blender-pro-suite/introduction/welcome-to-baked-blender-pro-suite'


def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)

def register():
    bpy.utils.register_class(BBS_Info_Panel)

def unregister():
    bpy.utils.unregister_class(BBS_Info_Panel)

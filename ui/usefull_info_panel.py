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
        row = layout.row()
        discord = self.layout.operator('wm.url_open',text='Discord',icon_value=i["discord"].icon_id)
        twitter = self.layout.operator('wm.url_open',text='Twitter',icon_value=i["twitter"].icon_id)
        reddit = self.layout.operator('wm.url_open',text='Reddit',icon_value=i["reddit"].icon_id)
        layout.label( text = "Our youtube has some handy beginner tutorials!",)
        youtube = self.layout.operator('wm.url_open',text='Youtube',icon_value=i["youtube"].icon_id)

        discord.url = 'https://discord.gg/bakeduniverse'
        twitter.url = 'https://twitter.com/BakedUniverse'
        youtube.url = 'https://youtube.com/@bakeduniverse'
        reddit.url = 'https://www.reddit.com/user/BakedUniverse/'

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

import bpy
import os
import subprocess
preview_collections = {}


def previews_register():
    import bpy.utils.previews

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    custom_icons = bpy.utils.previews.new()
    for f in os.listdir(icons_dir):
        if f.endswith(".png"):
            custom_icons.load(
                os.path.splitext(os.path.basename(f))[0],
                os.path.join(icons_dir, f),
                "IMAGE",
            )
    preview_collections["icons"] = custom_icons


def previews_unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


def get_icons():
    return preview_collections["icons"]

CACHE_PATH = os.path.join(os.path.dirname(__file__), "icons")

def load_yt_thumb_as_icon(url):
    img_path = os.path.join(CACHE_PATH,'latest_yt_thumb.png')
    subprocess.run(["curl", url, "-o", img_path])
    
    pass
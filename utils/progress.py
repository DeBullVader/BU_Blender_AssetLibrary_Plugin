import math
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

def init(context, num_items, word="Progress"):
    props = context.window_manager.bu_props
    props.progress_word = word
    props.progress_total = num_items
    props.progress_percent = 0
    props.progress_cancel = False

def update(context, prog, text, workspace):
    props = context.window_manager.bu_props
    props.progress_percent = math.floor(prog / max(1, props.progress_total) * 100)
   
    # workspace.status_text_set_internal(text)  # Forces statusbar redraw

def end(context):
    props = context.window_manager.bu_props
    props.progress_percent = 0
    props.progress_total = 0
    # context.workspace.status_text_set_internal(None)  # Forces statusbar redraw, remove text


def draw_progress_bar(x, y, width, height, progress):
    # Define the vertices of the progress bar background and fill
    vertices_bg = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    vertices_fill = [(x, y), (x + width * progress, y), (x + width * progress, y + height), (x, y + height)]

    # Define shaders
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch_bg = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices_bg})
    batch_fill = batch_for_shader(shader, 'TRI_FAN', {"pos": vertices_fill})

    # Draw background
    shader.bind()
    shader.uniform_float("color", (0.5, 0.5, 0.5, 1.0))  # Grey color
    batch_bg.draw(shader)

    # Draw fill
    shader.uniform_float("color", (0.0, 0.6, 1.0, 0.5))  # LightBlue
    batch_fill.draw(shader)
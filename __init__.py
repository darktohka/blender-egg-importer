bl_info = {
    "name": "Import Panda3D .egg models",
    "author": "rdb, loonatic, darktohka",
    "version": (3, 0, 0),
    "blender": (3, 2, 0),
    "location": "File > Import > Panda3D (.egg)",
    "description": "",
    "warning": "",
    "category": "Import-Export",
}

import bpy

if "loaded" in locals():
    import importlib
    importlib.reload(eggparser)
    importlib.reload(importer)
else:
    from . import eggparser
    from . import importer

loaded = True

import os.path
import bpy.types
from bpy import props
from bpy_extras.io_utils import ImportHelper


class EggImporterPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    backup_texpath: props.StringProperty(
        name="Texture path",
        subtype="FILE_PATH",
        description="Backup texture path to check if the texture can't be "
                    "found at the location of the .egg"
    )
    want_bsdf: props.BoolProperty(
        name="Use Principled BSDF",
        default=True,
        description="Determines whether materials will automatically use Principled BSDF. "
                    "If false, they won't have shading"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "backup_texpath")
        layout.prop(self, "want_bsdf")


class IMPORT_OT_egg(bpy.types.Operator, ImportHelper):
    """Import .egg Operator"""
    bl_idname = "import_scene.egg"
    bl_label = "Import .egg"
    bl_description = "Import a Panda3D .egg file"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".egg"
    filter_glob: props.StringProperty(default="*.egg;*.egg.pz;*.egg.gz", options={'HIDDEN'})

    directory: props.StringProperty(name="Directory", options={'HIDDEN'})
    files: props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN'})

    load_external: props.BoolProperty(
        name="Load external references",
        description="Loads other .egg files referenced by this file as separate scenes, "
                    "and instantiates them using collections."
    )
    auto_bind: props.BoolProperty(
        name="Auto bind",
        default=True,
        description="Automatically tries to bind actions to armatures."
    )

    def execute(self, context):
        context = importer.EggContext()
        context.info = lambda msg: self.report({'INFO'}, context.prefix_message(msg))
        context.warn = lambda msg: self.report({'WARNING'}, context.prefix_message(msg))
        context.error = lambda msg: self.report({'ERROR'}, context.prefix_message(msg))
        context.search_dir = self.directory
        roots = []

        for file in self.files:
            path = os.path.join(self.directory, file.name)
            root = context.read_file(path)
            roots.append(root)

        for root in roots:
            root.build_tree(context)
        context.assign_vertex_groups()

        if self.load_external:
            context.load_external_references()

        if self.auto_bind:
            context.auto_bind()

        context.final_report()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "load_external")
        row = layout.row()
        row.prop(self, "auto_bind")


def menu_func(self, context):
    self.layout.operator(IMPORT_OT_egg.bl_idname, text="Panda3D (.egg)")


classes = (IMPORT_OT_egg, EggImporterPreferences)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

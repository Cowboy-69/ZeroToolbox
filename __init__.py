# for reload
if "bpy" in locals():
    import importlib
    if "import_god" in locals():
        importlib.reload(import_god)

import os
import time

import bpy
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ImportHelper

from . import import_god

bl_info = {
    "name": "ZeroToolbox",
    "author": "Cowboy69",
    "blender": (2, 80, 0),
    "version": (1, 0),
    "description": "GOD file importer",
    "location": "File > Import",
    "category": "Import"
}


class Import_GOD(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.god"
    bl_description = 'Import file in GOD format'
    bl_label = "GOD (.god)"

    filter_glob : bpy.props.StringProperty(
        default = "*.god",
        options = {'HIDDEN'}
    )
    
    directory : bpy.props.StringProperty(
        maxlen = 1024,
        default = "",
        subtype = 'FILE_PATH',
        options = {'HIDDEN'}
    )
    
    files : bpy.props.CollectionProperty(
        type = bpy.types.OperatorFileListElement,
        options = {'HIDDEN'}
    )

    filepath : bpy.props.StringProperty(
         name = "File path",
         description = "GOD file path",
         maxlen = 1024,
         default = "",
         options = {'HIDDEN'}
     )

    meshRootBlock : bpy.props.EnumProperty(
        items =
            (
                ("MeshRootBlock13", "Version 13", "MeshRoot 13.0"),
                ("MeshRootBlock12", "Version 12", "MeshRoot 12.0"),
                ("MeshRootBlock11", "Version 11", "MeshRoot 11.0"),
                ("MeshRootBlock10", "Version 10", "MeshRoot 10.0"),
                ("MeshRootBlock9", "Version 9", "MeshRoot 9.0"),
                ("MeshRootBlock8", "Version 8", "MeshRoot 8.0"),
                ("MeshRootBlock7", "Version 7", "MeshRoot 7.0"),
                ("MeshRootBlock6", "Version 6", "MeshRoot 6.0"),
                ("MeshRootBlock5", "Version 5", "MeshRoot 5.0"),
                ("MeshRootBlock3", "Version 3", "MeshRoot 3.0"),
                ("MeshRootBlock2", "Version 2", "MeshRoot 2.0"),
                ("MeshRootBlock1", "Version 1", "MeshRoot 4.0"),
            ),
        name        = "Version",
        description = "MeshRoot block file key"
    )

    def draw(self, context):
        layout = self.layout
        layout.box().prop(self, "meshRootBlock")
        
    def execute(self, context):
        for file in [os.path.join(self.directory, file.name) for file in self.files] if self.files else [self.filepath]:
            import_god.start_import(
                                    {
                                     'filePath' : file,
                                     'meshRoot' : self.meshRootBlock,
                                    }
                                    )
                
        return {'FINISHED'}

    def invoke(self, context, event):
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def import_god_link(self, context):
    self.layout.operator(Import_GOD.bl_idname, text="GOD (.god)")


def register():
    register_class(Import_GOD)

    bpy.types.TOPBAR_MT_file_import.append(import_god_link)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(import_god_link)

    unregister_class(Import_GOD)

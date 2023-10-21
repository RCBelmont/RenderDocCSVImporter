import bpy

bl_info = {
    "name": "Renderdoc CSV Import",
    "description": "Description",
    "author": "RCBelmont",
    "version": (0, 0, 1),
    "blender": (3, 00, 0),
    "location": "View 3D > Sidebar > Edit Tab > RDCsvImport (panel)",
    "warning": "",
    "doc_url": "",
    "category": "Util",
}

def validate_file_or_path(value, context):
    # Custom validation function to check if the value is a valid file or path
    # You can implement your own validation logic here
    if value.endswith(('.jpg', '.png', '.txt')) or value.startswith(('path/to/', 'my_folder/')):
        return True
    else:
        return False


class RDCSVImporterProp(bpy.types.PropertyGroup):
    # bg_strength: bpy.props.FloatProperty(
    #     name='Strength', description="",
    #     default=1.0,
    #     max=10.0, min=0.0,
    #     get=lambda self: c_get(self, 'Strength'),
    #     set=lambda self, value: c_set(self, value, 'Strength', 'bg_strength')
    # )
    example_float_value: bpy.props.FloatProperty(
        name='ExampleValue', description="",
        default=1.0,
        max=10.0, min=0.0
    )
    csv_file_path: bpy.props.StringProperty(
        name='SavePath', description="Texture Save Path",
        subtype='NONE',
        update=validate_file_or_path
    )



class VIEW3D_PT_RENDERDOC_CSV(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'RD CSVImport'
    bl_category = 'RCBTool'

    def draw(self, context):
        layout = self.layout
        prop = context.scene.rd_csv_importer_prop
        ##layout.prop(prop, "example_float_value")
        layout.prop(prop, "csv_file_path")

        pass

    @classmethod
    def poll(cls, context):
        return True


class_to_register = (
    RDCSVImporterProp,
    VIEW3D_PT_RENDERDOC_CSV,
)


def register():
    for c in class_to_register:
        bpy.utils.register_class(c)
    bpy.types.Scene.rd_csv_importer_prop = bpy.props.PointerProperty(type=RDCSVImporterProp)


def unregister():
    for c in reversed(class_to_register):
        bpy.utils.unregister_class(c)

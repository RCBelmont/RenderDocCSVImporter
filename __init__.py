import os.path
import csv
import math
import os.path
import random
import subprocess

from mathutils import Vector
import bmesh

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


# region local method
def set_clipboard_contents(text):
    bpy.context.window_manager.clipboard = "DDDDD"



class VectorData:
    __slots__ = {
        "x",
        "y",
        "z",
        "w"
    }

    def __init__(self, x=0, y=0, z=0, w=0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def set_com_value(self, com, value):
        if com == 'x':
            self.x = value
        elif com == 'y':
            self.y = value
        elif com == 'z':
            self.z = value
        elif com == 'w':
            self.w = value

    def __str__(self):
        return "({},{},{},{})".format(self.x, self.y, self.z, self.w)

    def __repr__(self):
        return "({},{},{},{})".format(self.x, self.y, self.z, self.w)


def parse_csv_data(csv_path):
    with open(csv_path) as f:
        readout = list(csv.reader(f))
    title_list = []
    for title in readout[0]:
        title_list.append(title.strip())

    table_data_list = []
    for i in range(1, len(readout)):
        data_list = readout[i]
        table_data = {}
        table_data_list.append(table_data)
        for idx, data in enumerate(data_list):
            title = title_list[idx]
            title_com = title.split('.')
            if title_com[0] == 'VTX' or title_com[0] == 'IDX':
                table_data[title_com[0]] = int(data)
                continue
            if len(title_com) > 1:
                vec_com = title_com[1]
                if title_com[0] in table_data:
                    table_data[title_com[0]].set_com_value(vec_com, float(data))
                else:
                    vec_data = VectorData()
                    vec_data.set_com_value(vec_com, float(data))
                    table_data[title_com[0]] = vec_data
    return table_data_list


def get_all_vertex(csv_data_list):
    max_vert_idx = 0
    for data in csv_data_list:
        idx = data["IDX"]
        if idx > max_vert_idx:
            max_vert_idx = idx
    vert_list = [None] * (max_vert_idx + 1)
    for data in csv_data_list:
        idx = data["IDX"]
        pos_key = key_dic['pos']
        normal_key = key_dic['normal']
        if pos_key in data:
            pos = data[pos_key]
        else:
            pos = VectorData()
        if normal_key in data:
            normal = data[normal_key]
        else:
            normal = VectorData(z=1)
        vert_list[idx] = {'pos': pos, 'normal': normal}
    return vert_list


def get_k_v(dic, key, default):
    if key in dic:
        return dic[key]
    else:
        return default


def create_mesh_from_csv(csv_path):
    csv_data_list = parse_csv_data(csv_path)
    pure_date_list = []
    vert_list = get_all_vertex(csv_data_list)
    mesh = bpy.data.meshes.new("NewMesh")
    bm = bmesh.new()
    for v_data in vert_list:
        co = v_data['pos']
        rate = 0.0001 if b_overlay else 0
        r1 = random.uniform(-1, 1) * rate
        r2 = random.uniform(-1, 1) * rate
        bm.verts.new((co.x + r1, co.y, co.z + r2))
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    for i in range(0, len(csv_data_list), 3):
        d1 = csv_data_list[i]
        d2 = csv_data_list[i + 1]
        d3 = csv_data_list[i + 2]
        try:
            bm.faces.new((bm.verts[d1["IDX"]], bm.verts[d2["IDX"]], bm.verts[d3["IDX"]]))
            pure_date_list.append(d1)
            pure_date_list.append(d2)
            pure_date_list.append(d3)
        except:
            pass

    bm.faces.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    # Custom Normal
    custom_normal_list = []
    normal_key = key_dic['normal']
    for poly in mesh.polygons:
        poly.use_smooth = True
    for data in pure_date_list:
        norm = get_k_v(data, normal_key, None)
        if norm:
            v = Vector((norm.x, norm.y, norm.z))
            v = v.normalized()
            custom_normal_list.append((v.x, v.y, v.z))
            ##custom_normal_list.append((math.sqrt(0.5),0,math.sqrt(0.5)))
    mesh.use_auto_smooth = True
    if len(custom_normal_list) > 0:
        mesh.normals_split_custom_set(custom_normal_list)

    # UV
    key_list = list(key_dic.keys())
    idx = 1
    for key in key_list:
        if key.startswith("uv"):
            if key.endswith('_v4'):
                if key_dic[key] in pure_date_list[0]:
                    uv_layer = mesh.uv_layers.new(name="map{}".format(idx))
                    for i, data in enumerate(pure_date_list):
                        uv_data = data[key_dic[key]]
                        uv_layer.data[i].uv = (uv_data.x, uv_data.y)
                    idx += 1
                if key_dic[key] in pure_date_list[0]:
                    uv_layer = mesh.uv_layers.new(name="map{}".format(idx))
                    for i, data in enumerate(pure_date_list):
                        uv_data = data[key_dic[key]]
                        uv_layer.data[i].uv = (uv_data.z, uv_data.w)
                    idx += 1
            else:
                if key_dic[key] in pure_date_list[0]:
                    uv_layer = mesh.uv_layers.new(name="map{}".format(idx))
                    for i, data in enumerate(pure_date_list):
                        uv_data = data[key_dic[key]]
                        uv_layer.data[i].uv = (uv_data.x, uv_data.y)
                    idx += 1

    # # UV1
    # if key_dic['uv1'] in csv_data_list[0]:
    #     uv_layer = mesh.uv_layers.new(name="map1")
    #     for i, data in enumerate(csv_data_list):
    #         uv_data = data[key_dic['uv1']]
    #         uv_layer.data[i].uv = (uv_data.x, uv_data.y)
    # # UV2
    # if key_dic['uv2'] in csv_data_list[0]:
    #     uv_layer = mesh.uv_layers.new(name="map2")
    #     for i, data in enumerate(csv_data_list):
    #         uv_data = data[key_dic['uv2']]
    #         uv_layer.data[i].uv = (uv_data.x, uv_data.y)
    # # UV3
    # if key_dic['uv3'] in csv_data_list[0]:
    #     uv_layer = mesh.uv_layers.new(name="map3")
    #     for i, data in enumerate(csv_data_list):
    #         uv_data = data[key_dic['uv3']]
    #         uv_layer.data[i].uv = (uv_data.x, uv_data.y)
    # # UV4
    # if key_dic['uv4'] in csv_data_list[0]:
    #     uv_layer = mesh.uv_layers.new(name="map4")
    #     for i, data in enumerate(csv_data_list):
    #         uv_data = data[key_dic['uv4']]
    #         uv_layer.data[i].uv = (uv_data.x, uv_data.y)
    # Color
    if key_dic['v_color'] in pure_date_list[0]:
        color_layer = mesh.vertex_colors.new(name="ColorMap")
        for i, data in enumerate(pure_date_list):
            color = data[key_dic['v_color']]
            color_layer.data[i].color = (color.x, color.y, color.z, color.w)

    mesh.calc_tangents(uvmap="map1")
    obj = bpy.data.objects.new("NewObject", mesh)

    scene = bpy.context.scene
    scene.collection.objects.link(obj)
    return obj


# endregion

# region Operator
class OPT_TEST(bpy.types.Operator):
    bl_idname = "rd_csv_importer.test"
    bl_label = ""
    bl_options = {'REGISTER'}

    def execute(self, context):
        set_clipboard_contents("TRTTETETETET")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True


class OPT_RD_CSV_IMPORTER_COPY_KEY_WORDS(bpy.types.Operator):
    bl_idname = "rd_csv_importer.copy_key_words"
    bl_label = "Copy"
    bl_options = {'REGISTER'}
    key_words: bpy.props.StringProperty(
        default=""
    )

    def execute(self, context):
        set_clipboard_contents(self.key_words)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True


class OPT_RD_CSV_IMPORTER_DO_IMPORT(bpy.types.Operator):
    bl_idname = "rd_csv_importer.do_import"
    bl_label = "Import"
    bl_options = {'REGISTER'}

    def execute(self, context):

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        path = scene.rd_csv_importer_prop.csv_file_path
        if not path:
            return False
        if not os.path.exists(path):
            return False
        return True


class OPT_RD_CSV_IMPORTER_ADD_PROP_TYPE(bpy.types.Operator):
    bl_idname = "rd_csv_importer.add_prop_type"
    bl_label = "ADD"
    bl_options = {'REGISTER'}

    def execute(self, context):
        data_list = context.scene.rd_csv_importer_prop_type_list
        data_list.add()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True


class OPT_RD_CSV_IMPORTER_REMOVE_PROPER_TYPE(bpy.types.Operator):
    bl_idname = "rd_csv_importer.remove_prop_type"
    bl_label = ""
    bl_options = {'REGISTER'}
    clear_all: bpy.props.BoolProperty(
        default=False
    )
    remove_idx: bpy.props.IntProperty(
        default=1
    )

    def execute(self, context):

        if self.clear_all:
            context.scene.rd_csv_importer_prop_type_list.clear()
        else:
            data_list = context.scene.rd_csv_importer_prop_type_list
            max_idx = len(data_list) - 1
            del_idx = max(0, min(max_idx, self.remove_idx))
            data_list.remove(del_idx)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return True


# endregion

# region Property
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
        name='SavePath', description="CSV Path",
        subtype='NONE'
    )


class RDCSVImporterPropertyDefine(bpy.types.PropertyGroup):
    target_prop_type: bpy.props.EnumProperty(
        items=[("vert_color", "VertexColor", "Vertex Color", 0, 0),
               ("normal", "Normal", "Normal", 0, 1),
               ("uv", "UV", "UV Map", 0, 2)],
        name="Type"
    )
    target_prop_key: bpy.props.StringProperty(
        default="TEXCOORD0"
    )


# endregion
class VIEW_UL_PROP_LIST(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, fit_flag):
        if self.layout_type in {'DEFAULT', 'COMPACT', 'GRID'}:
            column = layout.column(align=True)
            row = column.row(align=True)
            split = row.split(factor=0.1)
            split.label(text="prop{}".format(index + 1))
            split.prop(item, "target_prop_type", text="")
            split.prop(item, "target_prop_key", text="")
            del_opt = split.operator("rd_csv_importer.remove_prop_type", text="Del")
            del_opt.clear_all = False
            del_opt.remove_idx = index


class VIEW_UL_KEY_WORDS_LIST(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, fit_flag):
        if self.layout_type in {'DEFAULT', 'COMPACT', 'GRID'}:
            column = layout.column(align=True)
            row = column.row(align=True)
            split = row.split(factor=0.1)
            split.label("ddddddd")
            split.operator("rd_csv_importer.copy_key_words").key_words = "TTTEEEE"


class VIEW3D_PT_RENDERDOC_CSV(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'RD CSVImport'
    bl_category = 'RCBTool'

    def draw(self, context):
        layout = self.layout

        prop = context.scene.rd_csv_importer_prop
        layout.prop(prop, "csv_file_path")
        layout.template_list("VIEW_UL_PROP_LIST", "", context.scene, "rd_csv_importer_prop_type_list", context.scene,
                             "rd_csv_importer_prop_type_idx")
        layout.operator("rd_csv_importer.add_prop_type")
        layout.operator("rd_csv_importer.remove_prop_type", text="ClearAll").clear_all = True
        layout.operator("rd_csv_importer.do_import")
        layout.operator("rd_csv_importer.test")

        pass

    @classmethod
    def poll(cls, context):
        return True


class_to_register = (
    RDCSVImporterPropertyDefine,
    RDCSVImporterProp,
    OPT_RD_CSV_IMPORTER_DO_IMPORT,
    OPT_RD_CSV_IMPORTER_ADD_PROP_TYPE,
    OPT_RD_CSV_IMPORTER_REMOVE_PROPER_TYPE,
    OPT_RD_CSV_IMPORTER_COPY_KEY_WORDS,
    OPT_TEST,
    VIEW_UL_PROP_LIST,
    VIEW_UL_KEY_WORDS_LIST,
    VIEW3D_PT_RENDERDOC_CSV,
)


def register():
    for c in class_to_register:
        bpy.utils.register_class(c)
    bpy.types.Scene.rd_csv_importer_prop_type_list = bpy.props.CollectionProperty(type=RDCSVImporterPropertyDefine)
    bpy.types.Scene.rd_csv_importer_prop_type_idx = bpy.props.IntProperty()
    bpy.types.Scene.rd_csv_importer_prop = bpy.props.PointerProperty(type=RDCSVImporterProp)
    bpy.types.WindowManager.rd_csv_importer_prop_key_words = bpy.props.CollectionProperty(bpy.types.StringProperty)


def unregister():
    for c in reversed(class_to_register):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.rd_csv_importer_prop_type_list
    del bpy.types.Scene.rd_csv_importer_prop_type_idx
    del bpy.types.Scene.rd_csv_importer_prop
    del bpy.types.WindowManager.rd_csv_importer_prop_key_words

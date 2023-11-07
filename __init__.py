import csv
import os.path
import os.path
import random

import bmesh
import bpy
from mathutils import Vector

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
def parse_csv_key_word(csv_path: str):
    temp_list = []

    def connect_list(l):
        for key_word in l:
            if key_word not in temp_list:
                temp_list.append(key_word)

    if os.path.exists(csv_path):
        if os.path.isdir(csv_path):
            for r, d, fs in os.walk(csv_path):
                for f in fs:
                    file_path = os.path.join(r, f)
                    if os.path.isfile(file_path) and file_path.endswith(".csv"):
                        result = _parse_csv_key_word(file_path)
                        if result:
                            connect_list(result)
        else:
            result = _parse_csv_key_word(csv_path)
            if result:
                connect_list(result)
    ret_list = []
    temp_dic = {}
    for key_world in temp_list:
        com_list = key_world.split('.')
        if com_list[0] not in temp_dic:
            temp_dic[com_list[0]] = 1
        else:
            temp_dic[com_list[0]] += 1
    return temp_dic


def _parse_csv_key_word(csv_path: str):
    if os.path.isfile(csv_path) and csv_path.endswith(".csv"):
        with open(csv_path) as f:
            readout = list(csv.reader(f))
        title_list = []
        for title in readout[0]:
            title_list.append(title.strip())
        return title_list
    return None


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


def get_all_vertex(csv_data_list, pos_key):
    max_vert_idx = 0
    for data in csv_data_list:
        idx = data["IDX"]
        if idx > max_vert_idx:
            max_vert_idx = idx
    vert_list = [None] * (max_vert_idx + 1)
    for data in csv_data_list:
        idx = data["IDX"]
        pos_key = pos_key
        if pos_key in data:
            pos = data[pos_key]
        else:
            pos = VectorData()
        vert_list[idx] = {'pos': pos}
    return vert_list


def get_k_v(dic, key, default):
    if key in dic:
        return dic[key]
    else:
        return default


def create_mesh_from_csv(context, csv_path, b_overlay):
    ## Key
    data_block = context.scene.rd_csv_importer_prop
    pos_key_word = data_block.position_key_word
    normal_key_word = data_block.normal_key_word
    vert_color_key_word = data_block.vertex_color_key_word
    uv_key_words = []
    for d in context.scene.rd_csv_importer_prop_type_list:
        uv_key_words.append(d.key_words)

    key_word_dic = parse_csv_key_word(csv_path)

    csv_data_list = parse_csv_data(csv_path)
    pure_date_list = []
    vert_list = get_all_vertex(csv_data_list, pos_key_word)
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
    normal_key = normal_key_word
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
    idx = 1
    for key in uv_key_words:
        if key in key_word_dic:
            com_count = key_word_dic[key]
            if com_count > 2:
                if key in pure_date_list[0]:
                    uv_layer = mesh.uv_layers.new(name="map{}".format(idx))
                    for i, data in enumerate(pure_date_list):
                        uv_data = data[key]
                        uv_layer.data[i].uv = (uv_data.x, uv_data.y)
                    idx += 1
                if key in pure_date_list[0]:
                    uv_layer = mesh.uv_layers.new(name="map{}".format(idx))
                    for i, data in enumerate(pure_date_list):
                        uv_data = data[key]
                        uv_layer.data[i].uv = (uv_data.z, uv_data.w)
                    idx += 1
            else:
                if key in pure_date_list[0]:
                    uv_layer = mesh.uv_layers.new(name="map{}".format(idx))
                    for i, data in enumerate(pure_date_list):
                        uv_data = data[key]
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
    if vert_color_key_word in pure_date_list[0]:
        color_layer = mesh.vertex_colors.new(name="ColorMap")
        for i, data in enumerate(pure_date_list):
            color = data[vert_color_key_word]
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


class OPT_PARSE_KEY_WORDS(bpy.types.Operator):
    bl_idname = "rd_csv_importer.parse_key_words"
    bl_label = "Parse Key Words"
    bl_options = {'REGISTER'}

    def execute(self, context):
        data_list = context.window_manager.rd_csv_importer_prop_key_words
        data_list.clear()
        csv_path = context.scene.rd_csv_importer_prop.csv_file_path
        result = parse_csv_key_word(csv_path)
        kv_list = list(result.items())
        for name, com_count in kv_list:
            data_obj = data_list.add()
            data_obj.key_word = name
            data_obj.com_count = com_count
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


class OPT_RD_CSV_IMPORTER_COPY_KEY_WORDS(bpy.types.Operator):
    bl_idname = "rd_csv_importer.copy_key_words"
    bl_label = "Copy"
    bl_options = {'REGISTER'}
    opt_type: bpy.props.StringProperty(
        default=""
    )
    key_words: bpy.props.StringProperty(
        default=""
    )

    def execute(self, context):
        prop_data = context.scene.rd_csv_importer_prop
        if self.opt_type == "pos":
            prop_data.position_key_word = self.key_words
        elif self.opt_type == "norm":
            prop_data.normal_key_word = self.key_words
        elif self.opt_type == "vert_color":
            prop_data.vertex_color_key_word = self.key_words
        elif self.opt_type == "uv":
            data_list = context.scene.rd_csv_importer_prop_type_list
            data_obj = data_list.add()
            data_obj.key_words = self.key_words
        elif self.opt_type == "copy":
            prop_data.position_key_word = self.key_words
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
        scene = context.scene
        path = scene.rd_csv_importer_prop.csv_file_path
        if os.path.exists(path):
            if os.path.isfile(path):
                block_overlay = scene.rd_csv_importer_prop.block_overlay
                create_mesh_from_csv(context, csv_path=path, b_overlay=block_overlay)
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
class PROP_RDCSVImporterKeyWordsULItemProp(bpy.types.PropertyGroup):
    key_word: bpy.props.StringProperty(
        description="TEXCOORD0"
    )
    com_count: bpy.props.IntProperty(
        default=1
    )


class PROP_RDCSVImporterProp(bpy.types.PropertyGroup):
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
    block_overlay: bpy.props.BoolProperty(
        name='Block Overlay',
        default=False
    )
    csv_file_path: bpy.props.StringProperty(
        name='SavePath', description="CSV Path",
        subtype='NONE'
    )
    position_key_word: bpy.props.StringProperty(
        name='Position', description="CSV Path",
    )
    normal_key_word: bpy.props.StringProperty(
        name='Normal', description="CSV Path",
    )
    vertex_color_key_word: bpy.props.StringProperty(
        name='VertColor', description="CSV Path",
    )


class PROP_PROP_RDCSVImporterPropertyDefine(bpy.types.PropertyGroup):
    key_words: bpy.props.StringProperty(
        default="TEXCOORD0"
    )


# endregion
class VIEW_UL_PROP_LIST(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, fit_flag):
        if self.layout_type in {'DEFAULT', 'COMPACT', 'GRID'}:
            column = layout.column(align=True)
            row = column.row(align=True)
            split = row.split(factor=0.1)
            split.label(text="uv{}".format(index + 1))
            split1 = split.split(factor=0.8)
            split1.prop(item, "key_words", text="")
            del_opt = split1.operator("rd_csv_importer.remove_prop_type", text="Del")
            del_opt.clear_all = False
            del_opt.remove_idx = index


class VIEW_UL_KEY_WORDS_LIST(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index, fit_flag):
        if self.layout_type in {'DEFAULT', 'COMPACT', 'GRID'}:
            column = layout.column(align=True)
            row = column.row(align=True)
            split = row.split(factor=0.5)
            split.label(text=item.key_word)
            btn_to_pos = split.operator("rd_csv_importer.copy_key_words", text='p')
            btn_to_pos.opt_type = 'pos'
            btn_to_pos.key_words = item.key_word

            btn_to_norm = split.operator("rd_csv_importer.copy_key_words", text='n')
            btn_to_norm.opt_type = 'norm'
            btn_to_norm.key_words = item.key_word

            btn_to_vert_color = split.operator("rd_csv_importer.copy_key_words", text='vc')
            btn_to_vert_color.opt_type = 'vert_color'
            btn_to_vert_color.key_words = item.key_word

            btn_to_uv = split.operator("rd_csv_importer.copy_key_words", text='uv')
            btn_to_uv.opt_type = 'uv'
            btn_to_uv.key_words = item.key_word

            btn_copy = split.operator("rd_csv_importer.copy_key_words", text='copy')
            btn_copy.opt_type = 'copy'
            btn_copy.key_words = item.key_word


class VIEW3D_PT_RENDERDOC_CSV(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = 'RD CSVImport'
    bl_category = 'RCBTool'

    def draw(self, context):
        layout = self.layout

        prop = context.scene.rd_csv_importer_prop
        layout.prop(prop, "csv_file_path")
        prop_box = layout.box()
        prop_box.prop(prop, 'position_key_word')
        prop_box.prop(prop, 'normal_key_word')
        prop_box.prop(prop, 'vertex_color_key_word')
        split = layout.split(factor=0.5)
        split.label(text="UV")
        split.operator("rd_csv_importer.add_prop_type")
        split.operator("rd_csv_importer.remove_prop_type", text="ClearAll").clear_all = True
        layout.template_list("VIEW_UL_PROP_LIST", "", context.scene, "rd_csv_importer_prop_type_list",
                             context.scene, "rd_csv_importer_prop_type_idx")
        layout.separator(factor=2)
        layout.operator("rd_csv_importer.parse_key_words")
        layout.template_list("VIEW_UL_KEY_WORDS_LIST", "", context.window_manager, "rd_csv_importer_prop_key_words",
                             context.window_manager, "rd_csv_importer_prop_key_words_idx")
        layout.separator(factor=2)
        layout.label(text="Import Setting")
        layout.prop(prop, "block_overlay")
        layout.operator("rd_csv_importer.do_import")
        pass

    @classmethod
    def poll(cls, context):
        return True


class_to_register = (
    PROP_PROP_RDCSVImporterPropertyDefine,
    PROP_RDCSVImporterProp,
    PROP_RDCSVImporterKeyWordsULItemProp,
    OPT_RD_CSV_IMPORTER_DO_IMPORT,
    OPT_RD_CSV_IMPORTER_ADD_PROP_TYPE,
    OPT_RD_CSV_IMPORTER_REMOVE_PROPER_TYPE,
    OPT_RD_CSV_IMPORTER_COPY_KEY_WORDS,
    OPT_TEST,
    OPT_PARSE_KEY_WORDS,
    VIEW_UL_PROP_LIST,
    VIEW_UL_KEY_WORDS_LIST,
    VIEW3D_PT_RENDERDOC_CSV,
)


def register():
    for c in class_to_register:
        bpy.utils.register_class(c)
    bpy.types.Scene.rd_csv_importer_prop_type_list = bpy.props.CollectionProperty(
        type=PROP_PROP_RDCSVImporterPropertyDefine)
    bpy.types.Scene.rd_csv_importer_prop_type_idx = bpy.props.IntProperty()
    bpy.types.Scene.rd_csv_importer_prop = bpy.props.PointerProperty(type=PROP_RDCSVImporterProp)
    bpy.types.WindowManager.rd_csv_importer_prop_key_words = bpy.props.CollectionProperty(
        type=PROP_RDCSVImporterKeyWordsULItemProp)
    bpy.types.WindowManager.rd_csv_importer_prop_key_words_idx = bpy.props.IntProperty()


def unregister():
    for c in reversed(class_to_register):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.rd_csv_importer_prop_type_list
    del bpy.types.Scene.rd_csv_importer_prop_type_idx
    del bpy.types.Scene.rd_csv_importer_prop
    del bpy.types.WindowManager.rd_csv_importer_prop_key_words
    del bpy.types.WindowManager.rd_csv_importer_prop_key_words_idx

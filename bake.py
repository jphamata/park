import bpy
import os

# --- CONFIGURAÇÕES ---
image_size = 1024
output_filename = 'baked_texture.jpg'
output_folder = os.path.expanduser("~/bake")
os.makedirs(output_folder, exist_ok=True)

# --- ENCONTRAR O PRIMEIRO OBJETO MESH VISÍVEL ---
obj = next((o for o in bpy.context.scene.objects if o.type == 'MESH' and o.visible_get()), None)
if not obj:
    raise Exception("Nenhum objeto do tipo MESH visível foi encontrado.")

print(f"Objeto selecionado: {obj.name}")
bpy.context.view_layer.objects.active = obj
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

# --- GARANTIR QUE HÁ UM UV MAP ---
if not obj.data.uv_layers:
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    print("UVs gerados automaticamente com Smart UV Project.")

# --- CRIAR IMAGEM PARA O BAKE ---
image_name = f"Bake_{obj.name}"
image = bpy.data.images.new(image_name, width=image_size, height=image_size)

# --- CONFIGURAR MATERIAL ---
if not obj.data.materials:
    mat = bpy.data.materials.new(name="BakedMaterial")
    obj.data.materials.append(mat)
else:
    mat = obj.active_material

if not mat.use_nodes:
    mat.use_nodes = True

nodes = mat.node_tree.nodes
tex_node = nodes.new(type='ShaderNodeTexImage')
tex_node.image = image
mat.node_tree.nodes.active = tex_node  # Necessário para o bake

# --- CONFIGURAR BAKE ---
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'  # Altere para 'GPU' se sua máquina permitir

scene.cycles.bake_type = 'COMBINED'
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
scene.render.bake.use_pass_color = True

# --- EXECUTAR O BAKE ---
bpy.ops.object.bake(type='COMBINED')

# --- SALVAR A IMAGEM ---
image.filepath_raw = os.path.join(output_folder, output_filename)
image.file_format = 'JPEG'
image.save()

print(f"Textura salva em: {image.filepath_raw}")
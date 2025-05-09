import bpy
import os

# Pasta onde você quer salvar as texturas
output_dir = os.path.expanduser("~/TexturasExtraidas/")
os.makedirs(output_dir, exist_ok=True)

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image is not None:
            image = node.image
            if image.packed_file:  # só salva se a imagem estiver embutida
                filename = image.name.replace("/", "_")
                filepath = os.path.join(output_dir, filename)
                image.filepath_raw = filepath
                image.file_format = 'PNG'
                image.save_render(filepath)
                print(f"Salvo: {filepath}")
# main.py
import glfw
from OpenGL.GL import *
import glm
import numpy as np
import time
import threading # Para input no terminal sem bloquear totalmente o GLFW

from shader_loader import Shader
from camera import Camera, Camera_Movement # camera.py precisa estar no mesmo diretório ou no PYTHONPATH
from texture_loader import load_texture   # texture_loader.py precisa estar no mesmo diretório
from model import Model                   # model.py precisa estar no mesmo diretório
from skybox import Skybox                 # skybox.py precisa estar no mesmo diretório

# --- Configurações Iniciais ---
largura, altura = 1280, 720

# --- Instância da Câmera ---
# A câmera será inicializada dentro de main() para evitar problemas de contexto GL não pronto
camera = None
lastX = largura / 2.0
lastY = altura / 2.0
firstMouse = True

# --- Timing ---
deltaTime = 0.0
lastFrame = 0.0

# --- Estado do Programa ---
polygonal_mode = False
selected_model_name = None
models = {}
instanced_models_dict = {} # Para grupos de objetos como cadeiras

# --- Callbacks ---
def framebuffer_size_callback(window, width, height):
    global largura, altura
    if height == 0: height = 1
    largura, altura = width, height
    glViewport(0, 0, width, height)

def key_callback(window, key, scancode, action, mods):
    global camera, polygonal_mode, selected_model_name, models, instanced_models_dict

    if action == glfw.PRESS or action == glfw.REPEAT:
        # Movimento da Câmera
        if key == glfw.KEY_W: camera.process_keyboard(Camera_Movement.FORWARD, deltaTime)
        if key == glfw.KEY_S: camera.process_keyboard(Camera_Movement.BACKWARD, deltaTime)
        if key == glfw.KEY_A: camera.process_keyboard(Camera_Movement.LEFT, deltaTime)
        if key == glfw.KEY_D: camera.process_keyboard(Camera_Movement.RIGHT, deltaTime)
        if key == glfw.KEY_SPACE: camera.process_keyboard(Camera_Movement.UP, deltaTime)
        if key == glfw.KEY_LEFT_SHIFT or key == glfw.KEY_RIGHT_SHIFT: camera.process_keyboard(Camera_Movement.DOWN, deltaTime)

        if key == glfw.KEY_P and action == glfw.PRESS:
            polygonal_mode = not polygonal_mode
            print(f"Modo Poligonal: {'Ligado' if polygonal_mode else 'Desligado'}")

        if selected_model_name:
            target_model = None
            if selected_model_name in models:
                target_model = models[selected_model_name]
            else:
                for group_name in instanced_models_dict:
                    if selected_model_name in instanced_models_dict[group_name]:
                        target_model = instanced_models_dict[group_name][selected_model_name]
                        break
            
            if target_model:
                translate_speed = 0.5 # Ajuste a velocidade de translação do objeto
                rotate_speed_obj = 5.0 # Graus para rotação do objeto
                scale_factor_obj = 0.05 # Fator para escala do objeto

                if key == glfw.KEY_J: target_model.translate(glm.vec3(-translate_speed, 0, 0))
                if key == glfw.KEY_L: target_model.translate(glm.vec3(translate_speed, 0, 0))
                if key == glfw.KEY_I: target_model.translate(glm.vec3(0, 0, -translate_speed))
                if key == glfw.KEY_K: target_model.translate(glm.vec3(0, 0, translate_speed))
                if key == glfw.KEY_U: target_model.translate(glm.vec3(0, translate_speed, 0))
                if key == glfw.KEY_O: target_model.translate(glm.vec3(0, -translate_speed, 0))

                if key == glfw.KEY_Z: target_model.rotate(rotate_speed_obj, glm.vec3(0, 1, 0))
                if key == glfw.KEY_X: target_model.rotate(-rotate_speed_obj, glm.vec3(0, 1, 0))
                
                if key == glfw.KEY_E: target_model.scale(glm.vec3(1 + scale_factor_obj))
                if key == glfw.KEY_R: target_model.scale(glm.vec3(max(0.01, 1 - scale_factor_obj))) # Evitar escala zero/negativa

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

def mouse_callback(window, xpos, ypos):
    global firstMouse, lastX, lastY, camera
    if camera is None: return # Se a câmera ainda não foi inicializada
    if firstMouse:
        lastX = xpos
        lastY = ypos
        firstMouse = False
    xoffset = xpos - lastX
    yoffset = lastY - ypos
    lastX = xpos
    lastY = ypos
    camera.process_mouse_movement(xoffset, yoffset)

def scroll_callback(window, xoffset, yoffset):
    global camera
    if camera is None: return
    camera.process_mouse_scroll(yoffset)

# --- Chão da Cidade ---
city_floor_vertices = np.array([
    -70.0, 0.0,  70.0,   0.0, 35.0,
     70.0, 0.0,  70.0,  35.0, 35.0,
     70.0, 0.0, -70.0,  35.0,  0.0,
    -70.0, 0.0,  70.0,   0.0, 35.0,
     70.0, 0.0, -70.0,  35.0,  0.0,
    -70.0, 0.0, -70.0,   0.0,  0.0
], dtype=np.float32)
city_floor_vao = None
city_floor_vbo = None
city_ground_texture_id = None

def setup_city_floor():
    global city_floor_vao, city_floor_vbo, city_ground_texture_id
    city_floor_vao = glGenVertexArrays(1)
    city_floor_vbo = glGenBuffers(1)
    glBindVertexArray(city_floor_vao)
    glBindBuffer(GL_ARRAY_BUFFER, city_floor_vbo)
    glBufferData(GL_ARRAY_BUFFER, city_floor_vertices.nbytes, city_floor_vertices, GL_STATIC_DRAW)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * city_floor_vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * city_floor_vertices.itemsize, ctypes.c_void_p(3 * city_floor_vertices.itemsize))
    glEnableVertexAttribArray(1)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    city_ground_texture_id = glGenTextures(1)
    if not load_texture("objetos/textures/city_ground.jpg", city_ground_texture_id): # Certifique-se que este arquivo existe
        print("Falha ao carregar textura do chão da cidade.")

def draw_city_floor(shader):
    if city_floor_vao and city_ground_texture_id:
        shader.use()
        model_matrix_floor = glm.mat4(1.0)
        shader.setMat4("model", model_matrix_floor)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, city_ground_texture_id)
        shader.setInt("texture1", 0)
        glBindVertexArray(city_floor_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        glBindTexture(GL_TEXTURE_2D, 0)

# --- Manipulação de Modelos via Terminal ---
def handle_model_manipulation_input():
    global selected_model_name, models, instanced_models_dict
    while True:
        time.sleep(0.2) # Pausa maior para não spammar o terminal
        print("\n--- Controle de Objetos ---")
        print("Modelos disponíveis (digite o número ou 'clear'):")
        idx = 0
        available_for_selection = []
        
        # Modelos principais
        sorted_model_names = sorted(models.keys())
        for name in sorted_model_names:
            print(f"{idx}: '{name}'")
            available_for_selection.append(name)
            idx += 1
        
        # Modelos "instanciados"
        for group_name in sorted(instanced_models_dict.keys()):
            for name in sorted(instanced_models_dict[group_name].keys()):
                print(f"{idx}: '{name}' (de {group_name})")
                available_for_selection.append(name) # Armazena o nome completo para seleção direta
                idx += 1
        
        print(f"Selecionado: {selected_model_name if selected_model_name else 'Nenhum'}")
        try:
            choice = input("Seleção: ")
            if choice.lower() == 'clear':
                selected_model_name = None
                print("Nenhum modelo selecionado.")
            else:
                choice_idx = int(choice)
                if 0 <= choice_idx < len(available_for_selection):
                    selected_model_name = available_for_selection[choice_idx]
                    print(f"Modelo '{selected_model_name}' selecionado.")
                    print("Use J,L,I,K,U,O (transladar); Z,X (rotacionar); E,R (escalar).")
                else:
                    print("Seleção inválida.")
        except ValueError:
            print("Entrada inválida.")
        except EOFError: # Caso o input seja interrompido
            break 
        except Exception as e:
            print(f"Erro no input: {e}")


# --- Função Principal ---
def main():
    global deltaTime, lastFrame, largura, altura, camera, firstMouse, lastX, lastY
    global polygonal_mode, selected_model_name, models, instanced_models_dict

    if not glfw.init(): print("Falha ao inicializar GLFW"); return
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(largura, altura, "Projeto 2 CG - ICMC", None, None)
    if not window: print("Falha ao criar janela GLFW"); glfw.terminate(); return

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    
    # Inicializa a câmera AQUI, após o contexto GL estar pronto
    camera = Camera(position=glm.vec3(0.0, 1.7, 35.0))


    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND) # Habilita blending para transparência (se texturas usarem canal alfa)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


    try:
        ourShader = Shader("shaders/vertex_shader.vs", "shaders/fragment_shader.fs")
        skyboxShader = Shader("shaders/skybox.vs", "shaders/skybox.fs")
    except Exception as e: print(f"Erro shaders: {e}"); glfw.terminate(); return

    # **DEFINA OS CAMINHOS CORRETOS AQUI**
    model_paths_textures = {
        "Hotel Building Old": ("objetos/hotel_building_old/hotel_building_old.obj", "objetos/hotel_building_old/Hotel_BaseColor.png"),
        "Old City Buildings": ("objetos/old_city_buildings/old_city_buildings.obj", "objetos/old_city_buildings/OldCity_BaseColor.png"),
        "Church": ("objetos/church/church.obj", "objetos/church/Church_BaseColor.png"),

        "Liam Human": ("objetos/human_liam/liam_human.obj", "objetos/human_liam/liam_BaseColor.png"),
        "John Human": ("objetos/human_john/john_human.obj", "objetos/human_john/john_BaseColor.png"),
        "Human Andrew": ("objetos/human_andrew/andrew_human.obj", "objetos/human_andrew/andrew_BaseColor.png"),
        "Human Phil": ("objetos/human_phil/phil_human.obj", "objetos/human_phil/phil_BaseColor.png"),
        "Women Juliette": ("objetos/human_juliette/juliette_human.obj", "objetos/human_juliette/juliette_BaseColor.png"),
        "Svenja Human": ("objetos/human_svenja/svenja_human.obj", "objetos/human_svenja/svenja_BaseColor.png"),
        "Human Kim": ("objetos/human_kim/kim_human.obj", "objetos/human_kim/kim_BaseColor.png"),
        "Human Lisa": ("objetos/human_lisa/lisa_human.obj", "objetos/human_lisa/lisa_BaseColor.png"),
        "Human Francine": ("objetos/human_francine/francine_human.obj", "objetos/human_francine/francine_BaseColor.png"),
        "Human Myriam": ("objetos/human_myriam/myriam_human.obj", "objetos/human_myriam/myriam_BaseColor.png"),
        "German Shepherd Dog": ("objetos/german_shepherd/german_shepherd.obj", "objetos/german_shepherd/Dog_BaseColor.png"),

        "Simple Office Chair": ("objetos/simple_office_chair/simple_office_chair.obj", "objetos/simple_office_chair/OfficeChair_BaseColor.png"),
        "Wooden Chair": ("objetos/wooden_chair/wooden_chair.obj", "objetos/wooden_chair/WoodenChair_BaseColor.png"),
        "Fire Keeper Staff": ("objetos/fire_keeper_staff/fire_keeper_staff.obj", "objetos/fire_keeper_staff/Staff_BaseColor.png"), # Pode precisar de ajuste de escala/textura
        "Treasure Chest": ("objetos/treasure_chest/treasure_chest.obj", "objetos/treasure_chest/Chest_BaseColor.png"),
        "Outdoor Table With Chess Board": ("objetos/outdoor_table_chess/outdoor_table_chess.obj", "objetos/outdoor_table_chess/ChessTable_BaseColor.png"),
        "Garden Corner With Bird House": ("objetos/garden_corner_birdhouse/garden_corner_birdhouse.obj", "objetos/garden_corner_birdhouse/GardenCorner_BaseColor.png"),
        "Square Metal Trashbin": ("objetos/square_metal_trashbin/square_metal_trashbin.obj", "objetos/square_metal_trashbin/Trashbin_BaseColor.png"),
        "Fire Hydrant": ("objetos/fire_hydrant/fire_hydrant.obj", "objetos/fire_hydrant/Hydrant_BaseColor.png"),
        "Garden Lamp": ("objetos/garden_lamp/garden_lamp.obj", "objetos/garden_lamp/GardenLamp_BaseColor.png"),
        "Statue (Photoscanned)": ("objetos/statue_photoscanned/statue_photoscanned.obj", "objetos/statue_photoscanned/Statue_BaseColor.png"),
        "Lion Statue": ("objetos/lion_statue/lion_statue.obj", "objetos/lion_statue/LionStatue_BaseColor.png"),
        "Chippendale Nautical Chart Table": ("objetos/chippendale_table/chippendale_table.obj", "objetos/chippendale_table/Table_BaseColor.png"),
        "Birdseye Maple Art Deco Table": ("objetos/art_deco_table/art_deco_table.obj", "objetos/art_deco_table/ArtDecoTable_BaseColor.png"),
        "Book War & Peace": ("objetos/book_war_peace/book_war_peace.obj", "objetos/book_war_peace/Book_BaseColor.png"),
    }

    for name, paths in model_paths_textures.items():
        obj_path, tex_path = paths
        print(f"Carregando: {name} de {obj_path}...")
        try:
            model_instance = Model(obj_filename=obj_path, texture_filename=tex_path, name=name)
            if model_instance.vao is not None: models[name] = model_instance
            else: print(f"  Falha ao inicializar VAO/VBO para {name}.")
        except Exception as e: print(f"  Erro Crítico ao carregar {name} ({obj_path}): {e}")

    # --- Posições e Escalas (AJUSTE!) ---
    building_scale = 0.4 # Aumentei um pouco para visibilidade
    human_scale = 0.9
    dog_scale = 0.8
    item_scale_s = 0.1
    item_scale_m = 0.2 # Aumentei um pouco as escalas de itens
    item_scale_l = 0.5
    chair_scale = 0.6

    church_pos = glm.vec3(-20, 0, -25) # Igreja mais para o fundo e esquerda
    if "Church" in models: models["Church"].set_position(church_pos.x, church_pos.y, church_pos.z); models["Church"].scale(glm.vec3(building_scale * 1.5)); models["Church"].rotate(-90, glm.vec3(0,1,0))

    if "Hotel Building Old" in models: models["Hotel Building Old"].set_position(20, 0, -25); models["Hotel Building Old"].scale(glm.vec3(building_scale * 1.3)); models["Hotel Building Old"].rotate(90, glm.vec3(0,1,0))
    if "Old City Buildings" in models: models["Old City Buildings"].set_position(0, 0, -45); models["Old City Buildings"].scale(glm.vec3(building_scale * 1.8)); # Fundo
    if "The Roebuck" in models: models["The Roebuck"].set_position(30, 0, 0); models["The Roebuck"].scale(glm.vec3(building_scale*1.1)); models["The Roebuck"].rotate(-90, glm.vec3(0,1,0)) # Direita

    # Itens na Igreja
    if "Church" in models: # Só adiciona itens se a igreja existir
        church_front_z_offset = 2.0 # Quão para dentro da igreja (considerando rotação)
        church_altar_z_offset = 7.0
        church_side_x_offset = 2.5

        num_chair_rows = 4
        chairs_per_row_side = 3 # Cadeiras por fileira de cada lado do corredor
        row_spacing = 1.2
        chair_spacing_in_row = 0.8
        
        base_office_chair = models.get("Simple Office Chair")
        if base_office_chair and base_office_chair.vao:
            instanced_models_dict["Simple Office Chair"] = {}
            for r_idx in range(num_chair_rows):
                for c_idx in range(chairs_per_row_side):
                    # Fileira Esquerda
                    chair_l_name = f"Simple Office Chair L{r_idx}-{c_idx}"
                    chair_l = Model(base_office_chair.obj_filepath, model_paths_textures["Simple Office Chair"][1], name=chair_l_name)
                    if chair_l.vao:
                        pos_l = church_pos + glm.vec3(-church_side_x_offset - c_idx * chair_spacing_in_row, 0, church_front_z_offset + r_idx * row_spacing)
                        chair_l.set_position(pos_l.x, pos_l.y, pos_l.z); chair_l.scale(glm.vec3(chair_scale)); # chair_l.rotate(0, glm.vec3(0,1,0)) # Já viradas para -Z por padrão
                        instanced_models_dict["Simple Office Chair"][chair_l_name] = chair_l
                    # Fileira Direita
                    chair_r_name = f"Simple Office Chair R{r_idx}-{c_idx}"
                    chair_r = Model(base_office_chair.obj_filepath, model_paths_textures["Simple Office Chair"][1], name=chair_r_name)
                    if chair_r.vao:
                        pos_r = church_pos + glm.vec3(church_side_x_offset + c_idx * chair_spacing_in_row, 0, church_front_z_offset + r_idx * row_spacing)
                        chair_r.set_position(pos_r.x, pos_r.y, pos_r.z); chair_r.scale(glm.vec3(chair_scale)); # chair_r.rotate(0, glm.vec3(0,1,0))
                        instanced_models_dict["Simple Office Chair"][chair_r_name] = chair_r
        
        base_wooden_chair = models.get("Wooden Chair")
        if base_wooden_chair and base_wooden_chair.vao:
            instanced_models_dict["Wooden Chair"] = {}
            wc1_name = "Wooden Chair Altar"
            wc1 = Model(base_wooden_chair.obj_filepath, model_paths_textures["Wooden Chair"][1], name=wc1_name)
            if wc1.vao: wc1.set_position(church_pos.x, church_pos.y, church_pos.z + church_altar_z_offset - 0.5); wc1.scale(glm.vec3(chair_scale*1.1)); instanced_models_dict["Wooden Chair"][wc1_name] = wc1

        if "Fire Keeper Staff" in models:
            staff_scale = 0.015; staff_y_offset = 0.8
            models["Fire Keeper Staff"].set_position(church_pos.x - 1.2, church_pos.y + staff_y_offset, church_pos.z - 1.5); models["Fire Keeper Staff"].scale(glm.vec3(staff_scale)); models["Fire Keeper Staff"].rotate(10, glm.vec3(1,0,0.2))
            staff2_name = "Fire Keeper Staff 2" # Criar como modelo separado se ainda não existir
            if staff2_name not in models and "Fire Keeper Staff" in models:
                 models[staff2_name] = Model(models["Fire Keeper Staff"].obj_filepath, model_paths_textures["Fire Keeper Staff"][1], name=staff2_name)
            if staff2_name in models: models[staff2_name].set_position(church_pos.x + 1.2, church_pos.y + staff_y_offset, church_pos.z - 1.5); models[staff2_name].scale(glm.vec3(staff_scale)); models[staff2_name].rotate(10, glm.vec3(1,0,-0.2))

        if "Treasure Chest" in models: models["Treasure Chest"].set_position(church_pos.x, church_pos.y, church_pos.z + church_altar_z_offset + 1); models["Treasure Chest"].scale(glm.vec3(item_scale_m*0.4))
        if "Chippendale Nautical Chart Table" in models: models["Chippendale Nautical Chart Table"].set_position(church_pos.x + 2.5, church_pos.y, church_pos.z + church_altar_z_offset -1); models["Chippendale Nautical Chart Table"].scale(glm.vec3(item_scale_m*0.6)); models["Chippendale Nautical Chart Table"].rotate(0, glm.vec3(0,1,0))
        if "Birdseye Maple Art Deco Table" in models: # Altar
            models["Birdseye Maple Art Deco Table"].set_position(church_pos.x, church_pos.y, church_pos.z + church_altar_z_offset); 
            models["Birdseye Maple Art Deco Table"].scale(glm.vec3(item_scale_m*0.5))
            if "Book War & Peace" in models: # Em cima da mesa art deco
                altar_table_pos = models["Birdseye Maple Art Deco Table"].model_matrix[3].xyz
                models["Book War & Peace"].set_position(altar_table_pos.x, altar_table_pos.y + 0.15, altar_table_pos.z); # Ajuste Y
                models["Book War & Peace"].scale(glm.vec3(item_scale_s*0.3)); models["Book War & Peace"].rotate(15, glm.vec3(0,1,0))

    # Itens Externos (relativos ao centro da cena 0,0,0 ou a um ponto de referência)
    ext_ref_point = glm.vec3(5, 0, 10) # Ponto de referência para itens externos
    if "Outdoor Table With Chess Board" in models: models["Outdoor Table With Chess Board"].set_position(ext_ref_point.x, ext_ref_point.y, ext_ref_point.z); models["Outdoor Table With Chess Board"].scale(glm.vec3(item_scale_m*1.5))
    if "Garden Corner With Bird House" in models: models["Garden Corner With Bird House"].set_position(ext_ref_point.x - 8, 0, ext_ref_point.z + 5); models["Garden Corner With Bird House"].scale(glm.vec3(item_scale_l*0.8))
    if "Square Metal Trashbin" in models: models["Square Metal Trashbin"].set_position(ext_ref_point.x + 5, 0, ext_ref_point.z - 2); models["Square Metal Trashbin"].scale(glm.vec3(item_scale_s*2.0))
    if "Fire Hydrant" in models: models["Fire Hydrant"].set_position(ext_ref_point.x - 3, 0, ext_ref_point.z + 8); models["Fire Hydrant"].scale(glm.vec3(item_scale_s*1.5))
    if "Garden Lamp" in models: models["Garden Lamp"].set_position(ext_ref_point.x + 2, 0, ext_ref_point.z + 7); models["Garden Lamp"].scale(glm.vec3(item_scale_m*1.2))
    if "Statue (Photoscanned)" in models: models["Statue (Photoscanned)"].set_position(0, 0, 15); models["Statue (Photoscanned)"].scale(glm.vec3(item_scale_l*0.7)); models["Statue (Photoscanned)"].rotate(180, glm.vec3(0,1,0))
    if "Lion Statue" in models: models["Lion Statue"].set_position(10, 0, 0); models["Lion Statue"].scale(glm.vec3(item_scale_l*0.8)); models["Lion Statue"].rotate(-90, glm.vec3(0,1,0))

    # Personagens
    human_names = ["Liam Human", "John Human", "Human Andrew", "Human Phil", "Women Juliette",
                   "Svenja Human", "Human Kim", "Human Lisa", "Human Francine", "Human Myriam"]
    human_spawn_area_center = glm.vec3(0, 0, 10) # Centro da área de spawn dos humanos
    human_spawn_radius = 15.0
    for i, name in enumerate(human_names):
        if name in models:
            angle = (i / len(human_names)) * 2 * glm.pi()
            dist = np.random.uniform(human_spawn_radius * 0.3, human_spawn_radius)
            x = human_spawn_area_center.x + dist * glm.cos(angle)
            z = human_spawn_area_center.z + dist * glm.sin(angle)
            models[name].set_position(x, 0, z)
            models[name].scale(glm.vec3(human_scale))
            models[name].rotate(np.random.uniform(0,360), glm.vec3(0,1,0))

    if "German Shepherd Dog" in models:
        models["German Shepherd Dog"].set_position(2, 0, 8)
        models["German Shepherd Dog"].scale(glm.vec3(dog_scale))
        models["German Shepherd Dog"].rotate(60, glm.vec3(0,1,0))

    skybox_faces = [ # Certifique-se que estes caminhos estão corretos
        "objetos/skybox/right.jpg", "objetos/skybox/left.jpg",
        "objetos/skybox/top.jpg", "objetos/skybox/bottom.jpg",
        "objetos/skybox/front.jpg", "objetos/skybox/back.jpg"
    ]
    try: skybox = Skybox(skybox_faces)
    except Exception as e: print(f"Erro skybox: {e}"); glfw.terminate(); return
    
    setup_city_floor()

    input_thread = threading.Thread(target=handle_model_manipulation_input, daemon=True)
    input_thread.start()

    while not glfw.window_should_close(window):
        currentFrame = time.time()
        deltaTime = currentFrame - lastFrame
        if deltaTime == 0: deltaTime = 0.0001 
        lastFrame = currentFrame

        glfw.poll_events()

        if polygonal_mode: glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else: glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glClearColor(0.5, 0.55, 0.6, 1.0) # Céu um pouco mais nublado
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view = camera.get_view_matrix()
        projection = camera.get_projection_matrix(largura, altura)

        skybox.draw(skyboxShader, view, projection)

        ourShader.use()
        ourShader.setMat4("view", view)
        ourShader.setMat4("projection", projection)
        draw_city_floor(ourShader)

        for model_instance in models.values():
            if model_instance and model_instance.vao:
                model_instance.draw(ourShader)
        
        for group_name in instanced_models_dict:
            for instance_model in instanced_models_dict[group_name].values():
                 if instance_model and instance_model.vao:
                    instance_model.draw(ourShader)

        glfw.swap_buffers(window)

    print("Encerrando...")
    # Limpeza de recursos OpenGL (melhorias podem ser feitas aqui)
    # ... (código de limpeza como na resposta anterior) ...
    del skybox
    for model_instance in models.values():
        if model_instance: del model_instance
    for group_name in instanced_models_dict:
        for instance_model in instanced_models_dict[group_name].values():
            if instance_model: del instance_model
    
    if city_floor_vao: glDeleteVertexArrays(1, [city_floor_vao])
    if city_floor_vbo: glDeleteBuffers(1, [city_floor_vbo])
    if city_ground_texture_id: glDeleteTextures(1, [city_ground_texture_id])

    if 'ourShader' in locals() and ourShader.ID is not None: del ourShader
    if 'skyboxShader' in locals() and skyboxShader.ID is not None: del skyboxShader
    
    glfw.terminate()

if __name__ == "__main__":
    main()
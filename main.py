# main.py
import glfw
from OpenGL.GL import *
import glm
import numpy as np
import time

from shader_loader import Shader
from camera import Camera, Camera_Movement
from texture_loader import load_texture
from model import Model # A classe Model permanece a mesma da correção anterior
from skybox import Skybox

# --- Configurações Iniciais ---
largura, altura = 1200, 800

# --- Instância da Câmera ---
camera = Camera(position=glm.vec3(0.0, 2.0, 25.0))
lastX = largura / 2.0
lastY = altura / 2.0
firstMouse = True

# --- Timing ---
deltaTime = 0.0
lastFrame = 0.0

# --- Callbacks (mesmos da Etapa 2) ---
def framebuffer_size_callback(window, width, height):
    global largura, altura
    if height == 0: height = 1
    largura, altura = width, height
    glViewport(0, 0, width, height)

def key_callback(window, key, scancode, action, mods):
    global camera
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    if action == glfw.PRESS or action == glfw.REPEAT:
        if key == glfw.KEY_W: camera.process_keyboard(Camera_Movement.FORWARD, deltaTime)
        if key == glfw.KEY_S: camera.process_keyboard(Camera_Movement.BACKWARD, deltaTime)
        if key == glfw.KEY_A: camera.process_keyboard(Camera_Movement.LEFT, deltaTime)
        if key == glfw.KEY_D: camera.process_keyboard(Camera_Movement.RIGHT, deltaTime)

def mouse_callback(window, xpos, ypos):
    global firstMouse, lastX, lastY, camera
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
    camera.process_mouse_scroll(yoffset)

# --- Chão da Cidade (Quad) ---
city_floor_vertices = np.array([
    # positions         # texture Coords
    -60.0, 0.0,  60.0,   0.0, 30.0, # Aumentei a área do chão
     60.0, 0.0,  60.0,  30.0, 30.0,
     60.0, 0.0, -60.0,  30.0,  0.0,

    -60.0, 0.0,  60.0,   0.0, 30.0,
     60.0, 0.0, -60.0,  30.0,  0.0,
    -60.0, 0.0, -60.0,   0.0,  0.0
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
    # SUBSTITUA "objetos/textures/city_ground.jpg" PELO CAMINHO DA SUA TEXTURA DE CHÃO
    if not load_texture("objetos/textures/city_ground.jpg", city_ground_texture_id):
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

# --- Função Principal ---
def main():
    global deltaTime, lastFrame, largura, altura, camera, firstMouse, lastX, lastY

    if not glfw.init(): print("Falha ao inicializar GLFW"); return
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(largura, altura, "Projeto 2 - Etapa 2 Revisada", None, None)
    if not window: print("Falha ao criar janela GLFW"); glfw.terminate(); return

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glEnable(GL_DEPTH_TEST)

    try:
        ourShader = Shader("shaders/vertex_shader.vs", "shaders/fragment_shader.fs")
        skyboxShader = Shader("shaders/skybox.vs", "shaders/skybox.fs")
    except Exception as e: print(f"Erro shaders: {e}"); glfw.terminate(); return

    models = {}
    model_paths_textures = {
        "Hotel Building Old": ("objetos/HotelBuildingOld/HotelBuildingOld.obj", "objetos/HotelBuildingOld/Hotel_BaseColor.png"),
        "Old City Buildings": ("objetos/OldCityBuildings/OldCityBuildings.obj", "objetos/OldCityBuildings/OldCity_BaseColor.png"), # Pode ser um conjunto de prédios
        "Church": ("objetos/Church/Church.obj", "objetos/Church/Church_BaseColor.png"),

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
    }

    for name, paths in model_paths_textures.items():
        obj_path, tex_path = paths
        print(f"Carregando: {name} de {obj_path} com textura {tex_path}")
        try:
            model_instance = Model(obj_filename=obj_path, texture_filename=tex_path, name=name)
            if model_instance.vao is not None:
                 models[name] = model_instance
            else:
                print(f"Modelo {name} não pôde ser inicializado corretamente.")
        except Exception as e:
            print(f"Erro Crítico ao carregar {name} ({obj_path}): {e}")

    # --- Posições e Escalas (AJUSTE ESTES VALORES!) ---
    building_scale_general = 0.5 # Escala base para edifícios, ajuste conforme os modelos
    human_scale = 0.8
    dog_scale = 0.7

    # Edifícios ao redor de uma praça/área central
    if "Hotel Building Old" in models:
        models["Hotel Building Old"].set_position(-15, 0, -15)
        models["Hotel Building Old"].scale(glm.vec3(building_scale_general * 1.2)) # Um pouco maior
        models["Hotel Building Old"].rotate(45, glm.vec3(0,1,0))

    if "Old City Buildings" in models: # Pode ser um grupo de prédios
        models["Old City Buildings"].set_position(15, 0, -20)
        models["Old City Buildings"].scale(glm.vec3(building_scale_general * 1.5)) # Maior se for um conjunto
        models["Old City Buildings"].rotate(-30, glm.vec3(0,1,0))

    if "Church" in models:
        models["Church"].set_position(-20, 0, 10) # À esquerda e um pouco para frente
        models["Church"].scale(glm.vec3(building_scale_general * 1.3))
        models["Church"].rotate(15, glm.vec3(0,1,0))


    # Personagens (distribua pela "praça" ou calçadas)
    human_positions = [
        (-3, 0, 5), (3, 0, 4), (0, 0, 8), (2, 0, 10), (-5, 0, 7),
        (7, 0, 6), (-1, 0, 12), (4, 0, 3), (-6, 0, 9), (0, 0, 2)
    ]
    human_names = ["Liam Human", "John Human", "Human Andrew", "Human Phil", "Women Juliette",
                   "Svenja Human", "Human Kim", "Human Lisa", "Human Francine", "Human Myriam"]

    for i, name in enumerate(human_names):
        if name in models:
            x, y, z = human_positions[i % len(human_positions)]
            models[name].set_position(x, y, z)
            models[name].scale(glm.vec3(human_scale))
            models[name].rotate(np.random.uniform(-45,45), glm.vec3(0,1,0))

    if "German Shepherd Dog" in models:
        models["German Shepherd Dog"].set_position(-1, 0, 7) # Perto de algum humano
        models["German Shepherd Dog"].scale(glm.vec3(dog_scale))
        models["German Shepherd Dog"].rotate(30, glm.vec3(0,1,0))


    skybox_faces = [
        "objetos/skybox/right.jpg", "objetos/skybox/left.jpg",
        "objetos/skybox/top.jpg", "objetos/skybox/bottom.jpg",
        "objetos/skybox/front.jpg", "objetos/skybox/back.jpg"
    ]
    try: skybox = Skybox(skybox_faces)
    except Exception as e: print(f"Erro skybox: {e}"); glfw.terminate(); return

    setup_city_floor() # Configura o chão da cidade

    while not glfw.window_should_close(window):
        currentFrame = time.time()
        deltaTime = currentFrame - lastFrame
        if deltaTime == 0: deltaTime = 0.0001
        lastFrame = currentFrame

        glfw.poll_events()
        glClearColor(0.5, 0.5, 0.55, 1.0) # Cor de fundo um pouco mais urbana/cinza
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view = camera.get_view_matrix()
        projection = camera.get_projection_matrix(largura, altura)

        skybox.draw(skyboxShader, view, projection)

        ourShader.use()
        ourShader.setMat4("view", view)
        ourShader.setMat4("projection", projection)
        draw_city_floor(ourShader) # Desenha o chão da cidade

        for model_instance in models.values():
            if model_instance and model_instance.vao:
                model_instance.draw(ourShader)

        glfw.swap_buffers(window)

    del skybox
    for model_instance in models.values():
        if model_instance: del model_instance

    if city_floor_vao: glDeleteVertexArrays(1, [city_floor_vao])
    if city_floor_vbo: glDeleteBuffers(1, [city_floor_vbo])
    if city_ground_texture_id: glDeleteTextures(1, [city_ground_texture_id])

    if 'ourShader' in locals() and ourShader.ID is not None: del ourShader
    if 'skyboxShader' in locals() and skyboxShader.ID is not None: del skyboxShader
    glfw.terminate()

if __name__ == "__main__":
    main()
# model.py
from OpenGL.GL import *
import numpy as np
import glm
from obj_loader import load_model_from_file
from texture_loader import load_texture # Importa o carregador de textura

class Model:
    def __init__(self, obj_filename, texture_filename=None, name="model"): # Adicionado texture_filename aqui
        self.vao = None
        self.vbo_vertices = None
        self.vbo_texcoords = None
        self.vertex_count = 0
        self.model_matrix = glm.mat4(1.0)
        self.texture_id = None
        self.name = name
        self.obj_filepath = obj_filename

        model_data = load_model_from_file(obj_filename)
        if model_data is None:
            print(f"Falha ao carregar dados do modelo: {obj_filename}")
            return

        processed_vertices = []
        processed_texcoords = []

        raw_vertices = np.array(model_data['vertices'], dtype=np.float32) if model_data['vertices'] else np.array([])
        raw_texcoords = np.array(model_data['texcoords'], dtype=np.float32) if model_data['texcoords'] else None

        if not model_data['faces']:
            print(f"Aviso: Modelo {obj_filename} não possui faces.")
            return

        for face_v_indices, face_t_indices, _ in model_data['faces']:
            for i in range(len(face_v_indices)):
                v_idx = face_v_indices[i]
                if 0 <= v_idx < len(raw_vertices):
                    processed_vertices.extend(raw_vertices[v_idx])
                else:
                    print(f"Aviso: Índice de vértice inválido {v_idx} em {obj_filename}")
                    processed_vertices.extend([0.0, 0.0, 0.0])

                if raw_texcoords is not None and face_t_indices:
                    t_idx = face_t_indices[i]
                    if 0 <= t_idx < len(raw_texcoords):
                        processed_texcoords.extend(raw_texcoords[t_idx])
                    else:
                        processed_texcoords.extend([0.0, 0.0])
                else:
                    processed_texcoords.extend([0.0, 0.0])

        if not processed_vertices:
            print(f"Aviso: Nenhum dado de vértice processado para {obj_filename}")
            return

        final_vertices_np = np.array(processed_vertices, dtype=np.float32)
        final_texcoords_np = np.array(processed_texcoords, dtype=np.float32)
        self.vertex_count = len(final_vertices_np) // 3

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, final_vertices_np.nbytes, final_vertices_np, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        if final_texcoords_np.size > 0:
            self.vbo_texcoords = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_texcoords)
            glBufferData(GL_ARRAY_BUFFER, final_texcoords_np.nbytes, final_texcoords_np, GL_STATIC_DRAW)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(1)
        else:
            glDisableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        # Carrega a textura AQUI, dentro do construtor
        if texture_filename:
            self.texture_id = glGenTextures(1) # Gera o ID da textura
            if not load_texture(texture_filename, self.texture_id): # Passa o ID para load_texture
                print(f"Falha ao carregar textura {texture_filename} para {self.name}")
                glDeleteTextures(1, [self.texture_id])
                self.texture_id = None
    
    # Método set_texture ainda pode ser útil se você quiser mudar a textura depois
    def set_texture(self, texture_id_new):
        if self.texture_id: # Se já existe uma textura, deleta a antiga
            glDeleteTextures(1, [self.texture_id])
        self.texture_id = texture_id_new

    def draw(self, shader):
        if self.vao is None or self.vertex_count == 0:
            return

        shader.use()
        shader.setMat4("model", self.model_matrix)

        if self.texture_id is not None:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            shader.setInt("texture1", 0)
        else:
            glBindTexture(GL_TEXTURE_2D, 0)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        glBindVertexArray(0)

    def set_position(self, x, y, z):
        self.model_matrix = glm.translate(glm.mat4(1.0), glm.vec3(x, y, z))

    def translate(self, t_vec):
        self.model_matrix = glm.translate(self.model_matrix, t_vec)

    def rotate(self, angle_degrees, axis_vec):
        self.model_matrix = glm.rotate(self.model_matrix, glm.radians(angle_degrees), axis_vec)

    def scale(self, s_vec):
        self.model_matrix = glm.scale(self.model_matrix, s_vec)

    def set_transform(self, matrix):
         self.model_matrix = matrix

    def __del__(self):
        try:
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
            if self.vbo_vertices:
                glDeleteBuffers(1, [self.vbo_vertices])
            if self.vbo_texcoords:
                glDeleteBuffers(1, [self.vbo_texcoords])
            if self.texture_id: # Somente deleta se foi criado
                glDeleteTextures(1, [self.texture_id])
        except Exception as e:
            pass
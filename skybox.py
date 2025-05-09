# skybox.py
from OpenGL.GL import *
import numpy as np
import glm
from texture_loader import load_cubemap

# Vértices do cubo para o skybox (sem coords de textura, usamos a posição como coord)
skyboxVertices = np.array([
    # positions
    -1.0,  1.0, -1.0,
    -1.0, -1.0, -1.0,
     1.0, -1.0, -1.0,
     1.0, -1.0, -1.0,
     1.0,  1.0, -1.0,
    -1.0,  1.0, -1.0,

    -1.0, -1.0,  1.0,
    -1.0, -1.0, -1.0,
    -1.0,  1.0, -1.0,
    -1.0,  1.0, -1.0,
    -1.0,  1.0,  1.0,
    -1.0, -1.0,  1.0,

     1.0, -1.0, -1.0,
     1.0, -1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0, -1.0,
     1.0, -1.0, -1.0,

    -1.0, -1.0,  1.0,
    -1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
     1.0, -1.0,  1.0,
    -1.0, -1.0,  1.0,

    -1.0,  1.0, -1.0,
     1.0,  1.0, -1.0,
     1.0,  1.0,  1.0,
     1.0,  1.0,  1.0,
    -1.0,  1.0,  1.0,
    -1.0,  1.0, -1.0,

    -1.0, -1.0, -1.0,
    -1.0, -1.0,  1.0,
     1.0, -1.0, -1.0,
     1.0, -1.0, -1.0,
    -1.0, -1.0,  1.0,
     1.0, -1.0,  1.0
], dtype=np.float32)

class Skybox:
    def __init__(self, face_paths):
        self.vao = None
        self.vbo = None
        self.cubemapTexture = load_cubemap(face_paths)
        if self.cubemapTexture is None:
            print("Falha ao carregar textura do cubemap.")
            return

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, skyboxVertices.nbytes, skyboxVertices, GL_STATIC_DRAW)

        # Vertex positions - Location 0
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * skyboxVertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(self, shader, view, projection):
        if self.vao is None or self.cubemapTexture is None: return

        glDepthFunc(GL_LEQUAL)  # Change depth function so depth test passes when values are equal to depth buffer's content
        shader.use()

        # Remove translation part from the view matrix for the skybox
        view_mat3 = glm.mat3(view)
        view_skybox = glm.mat4(view_mat3)

        shader.setMat4("view", view_skybox)
        shader.setMat4("projection", projection)

        # skybox cube
        glBindVertexArray(self.vao)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_CUBE_MAP, self.cubemapTexture)
        # O shader skybox precisa de um uniform samplerCube chamado 'skybox'
        shader.setInt("skybox", 0) # Informa ao shader para usar a unidade de textura 0

        glDrawArrays(GL_TRIANGLES, 0, 36)
        glBindVertexArray(0)
        glDepthFunc(GL_LESS) # Set depth function back to default

    def __del__(self):
        if self.vao:
            glDeleteVertexArrays(1, [self.vao])
        if self.vbo:
            glDeleteBuffers(1, [self.vbo])
        if self.cubemapTexture:
             glDeleteTextures(1, [self.cubemapTexture])
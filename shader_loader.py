# shader_loader.py
from OpenGL.GL import *
import glm
import numpy as np # Necessário para type checking em setMat4

class Shader:
    def __init__(self, vertexPath: str, fragmentPath: str):
        self.ID = None # Inicializa ID
        # 1. retrieve the vertex/fragment source code from filePath
        try:
            # open files
            with open(vertexPath) as vShaderFile, open(fragmentPath) as fShaderFile:
                # read file's buffer contents into strings
                vertexCode = vShaderFile.read()
                fragmentCode = fShaderFile.read()

            # 2. compile shaders
            # vertex shader
            vertex = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vertex, vertexCode)
            glCompileShader(vertex)
            self.checkCompileErrors(vertex, "VERTEX")
            # fragment Shader
            fragment = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fragment, fragmentCode)
            glCompileShader(fragment)
            self.checkCompileErrors(fragment, "FRAGMENT")
            # shader Program
            self.ID = glCreateProgram()
            glAttachShader(self.ID, vertex)
            glAttachShader(self.ID, fragment)
            glLinkProgram(self.ID)
            self.checkCompileErrors(self.ID, "PROGRAM")
            # delete the shaders as they're linked into our program now and no longer necessary
            glDeleteShader(vertex)
            glDeleteShader(fragment)

        except IOError as e:
            print(f"ERROR::SHADER::FILE_NOT_SUCCESFULLY_READ: {e}")
        except Exception as e:
             print(f"ERROR::SHADER: {e}")


    # activate the shader
    # ------------------------------------------------------------------------
    def use(self) -> None:
        if self.ID is not None:
            glUseProgram(self.ID)
        else:
            print("Shader program not initialized.")

    # utility uniform functions
    # ------------------------------------------------------------------------
    def setBool(self, name: str, value: bool) -> None:
         if self.ID is not None:
            glUniform1i(glGetUniformLocation(self.ID, name), int(value))
         else:
            print("Shader program not initialized.")
    # ------------------------------------------------------------------------
    def setInt(self, name: str, value: int) -> None:
        if self.ID is not None:
            glUniform1i(glGetUniformLocation(self.ID, name), value)
        else:
            print("Shader program not initialized.")
    # ------------------------------------------------------------------------
    def setFloat(self, name: str, value: float) -> None:
        if self.ID is not None:
            glUniform1f(glGetUniformLocation(self.ID, name), value)
        else:
            print("Shader program not initialized.")
    # ------------------------------------------------------------------------
    def setMat4(self, name: str, mat: glm.mat4) -> None:
        if self.ID is not None:
            # Verifica se mat é um array numpy ou um objeto glm.mat4
            if isinstance(mat, (glm.mat4, np.ndarray)):
                 # A função glUniformMatrix4fv espera um ponteiro para os dados da matriz.
                 # O PyGLM ou numpy array deve ser passado corretamente.
                 # GL_TRUE indica que a matriz está em formato column-major (padrão do OpenGL e GLM).
                 # Se sua matriz estiver em row-major, use GL_FALSE e transponha-a antes.
                 # O exemplo original usava GL_TRUE, vamos manter, mas lembre-se que glm é column-major.
                 # A conversão para np.array pode causar a necessidade de transpor dependendo de como é feita.
                 # É mais seguro usar GL_FALSE e passar glm.value_ptr(mat) se mat for glm.mat4
                 # Mas para manter consistência com Aula 13 que usava np.array() e GL_TRUE:
                 mat_np = np.array(mat)
                 glUniformMatrix4fv(glGetUniformLocation(self.ID, name), 1, GL_TRUE, mat_np)

                 # Alternativa mais segura com PyGLM puro (requer GL_FALSE):
                 # glUniformMatrix4fv(glGetUniformLocation(self.ID, name), 1, GL_FALSE, glm.value_ptr(mat))
            else:
                print("ERROR::SHADER::setMat4: mat is not a glm.mat4 or numpy array")
        else:
            print("Shader program not initialized.")

    # ------------------------------------------------------------------------
    def setVec3(self, name: str, vec: glm.vec3) -> None:
        if self.ID is not None:
             if isinstance(vec, glm.vec3):
                 glUniform3fv(glGetUniformLocation(self.ID, name), 1, glm.value_ptr(vec))
             else:
                 print("ERROR::SHADER::setVec3: vec is not a glm.vec3")
        else:
            print("Shader program not initialized.")

    # utility function for checking shader compilation/linking errors.
    # ------------------------------------------------------------------------
    def checkCompileErrors(self, shader: int, type: str) -> None:
        success = None
        infoLog = None
        if (type != "PROGRAM"):
            success = glGetShaderiv(shader, GL_COMPILE_STATUS)
            if (not success):
                infoLog = glGetShaderInfoLog(shader)
                print("ERROR::SHADER_COMPILATION_ERROR of type: " + type + "\n" + infoLog.decode() + "\n -- --------------------------------------------------- -- ")
        else:
            if self.ID is not None:
                success = glGetProgramiv(self.ID, GL_LINK_STATUS)
                if (not success):
                    infoLog = glGetProgramInfoLog(self.ID)
                    print("ERROR::PROGRAM_LINKING_ERROR of type: " + type + "\n" + infoLog.decode() + "\n -- --------------------------------------------------- -- ")
            else:
                 print("ERROR::SHADER::checkCompileErrors: Shader program ID is None during linking check.")
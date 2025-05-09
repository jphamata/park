# texture_loader.py
from OpenGL.GL import *
from PIL import Image
import os # Para verificar se o arquivo existe

def load_texture(path, texture_id):
    if not os.path.exists(path):
        print(f"Error: Texture file not found at {path}")
        return None # Ou gerar uma textura padrão
    try:
        glBindTexture(GL_TEXTURE_2D, texture_id)
        # Set the texture wrapping parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # Set texture filtering parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # load image
        img = Image.open(path)
        img = img.convert("RGB") # Garante que está em RGB
        img_width = img.width
        img_height = img.height
        image_data = img.tobytes("raw", "RGB", 0, -1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_width, img_height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
        # glGenerateMipmap(GL_TEXTURE_2D) # Opcional: Gerar mipmaps
        return texture_id
    except FileNotFoundError:
        print(f"ERROR::TEXTURE::FILE_NOT_FOUND: {path}")
        return None
    except Exception as e:
        print(f"ERROR::TEXTURE::LOAD_FAILED: {path} - {e}")
        return None


def load_cubemap(faces_paths):
    """ Carrega 6 texturas para um cubemap. faces_paths deve ser uma lista
        de 6 caminhos na ordem: right, left, top, bottom, front, back. """
    textureID = glGenTextures(1)
    glBindTexture(GL_TEXTURE_CUBE_MAP, textureID)

    for i, path in enumerate(faces_paths):
        if not os.path.exists(path):
            print(f"Error: Cubemap face file not found at {path}")
            # Poderia carregar uma textura padrão ou lançar um erro
            continue # Pula esta face se não encontrada

        try:
            img = Image.open(path)
            # Alguns skyboxes podem ter canais alfa ou estar em formatos diferentes
            img = img.convert("RGB")
            img_width, img_height = img.size
            image_data = img.tobytes("raw", "RGB", 0, -1)

            # GL_TEXTURE_CUBE_MAP_POSITIVE_X + i assume a ordem correta das faces
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGB, img_width, img_height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
        except FileNotFoundError:
            print(f"ERROR::CUBEMAP::FILE_NOT_FOUND: {path}")
        except Exception as e:
            print(f"ERROR::CUBEMAP::LOAD_FAILED: {path} - {e}")


    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)

    return textureID
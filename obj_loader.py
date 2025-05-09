# obj_loader.py

def triangulate_face(indices):
    """Converte uma face com N vértices (N>3) em triângulos."""
    if len(indices) == 3:
        return indices # Já é um triângulo
    triangles = []
    # Fan triangulation: conecta o primeiro vértice com todos os outros pares consecutivos
    v0 = indices[0]
    for i in range(1, len(indices) - 1):
        triangles.extend([v0, indices[i], indices[i+1]])
    return triangles


def load_model_from_file(filename):
    """Loads a Wavefront OBJ file.
       Retorna um dicionário com listas de vértices, texcoords e normais (ainda não usado),
       e uma lista de faces processadas (já trianguladas)."""
    vertices = []
    texcoords = []
    normals = [] # Ainda não usado, mas bom ter para o futuro
    faces = [] # Armazenará tuplas (v_indices, t_indices, n_indices)

    try:
        with open(filename, "r") as f:
            for line in f:
                if line.startswith('#'): continue
                values = line.split()
                if not values: continue

                if values[0] == 'v':
                    vertices.append(list(map(float, values[1:4])))
                elif values[0] == 'vt':
                    texcoords.append(list(map(float, values[1:3])))
                elif values[0] == 'vn':
                    normals.append(list(map(float, values[1:4])))
                elif values[0] == 'f':
                    face_v = []
                    face_t = []
                    face_n = []
                    for v_str in values[1:]:
                        w = v_str.split('/')
                        face_v.append(int(w[0]) - 1) # Vertex index (OBJ é 1-based)
                        if len(w) >= 2 and w[1]:
                            face_t.append(int(w[1]) - 1) # Texture index
                        else:
                             face_t.append(-1) # Indica ausência de tex coord
                        if len(w) >= 3 and w[2]:
                            face_n.append(int(w[2]) - 1) # Normal index
                        else:
                            face_n.append(-1) # Indica ausência de normal

                    # Triangula a face se necessário
                    v_indices_triangulated = triangulate_face(face_v)
                    t_indices_triangulated = triangulate_face(face_t) if face_t and -1 not in face_t else [-1] * len(v_indices_triangulated)
                    n_indices_triangulated = triangulate_face(face_n) if face_n and -1 not in face_n else [-1] * len(v_indices_triangulated)


                    # Adiciona as faces trianguladas
                    for i in range(0, len(v_indices_triangulated), 3):
                         faces.append(
                             (v_indices_triangulated[i:i+3],
                              t_indices_triangulated[i:i+3] if t_indices_triangulated[0] != -1 else [],
                              n_indices_triangulated[i:i+3] if n_indices_triangulated[0] != -1 else [])
                              )

    except FileNotFoundError:
        print(f"ERROR::OBJ_LOADER::FILE_NOT_FOUND: {filename}")
        return None
    except Exception as e:
        print(f"ERROR::OBJ_LOADER::LOAD_FAILED: {filename} - {e}")
        return None

    return {'vertices': vertices, 'texcoords': texcoords, 'normals': normals, 'faces': faces}
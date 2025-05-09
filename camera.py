import glm
import math

class Camera_Movement:
    FORWARD = 0
    BACKWARD = 1
    LEFT = 2
    RIGHT = 3
    UP = 4    # Adicionado para movimento vertical
    DOWN = 5  # Adicionado para movimento vertical


YAW         = -90.0
PITCH       =  0.0
SPEED       =  15.0 # AUMENTADA A VELOCIDADE
SENSITIVITY =  0.1
ZOOM        =  45.0

class Camera:
    def __init__(self, position=glm.vec3(0.0, 1.0, 3.0), up=glm.vec3(0.0, 1.0, 0.0), yaw=YAW, pitch=PITCH):
        self.Position = position
        self.Front = glm.vec3(0.0, 0.0, -1.0)
        self.Up = glm.vec3(0.0, 1.0, 0.0)
        self.Right = glm.vec3(1.0, 0.0, 0.0)
        self.WorldUp = up
        self.Yaw = yaw
        self.Pitch = pitch
        self.MovementSpeed = SPEED
        self.MouseSensitivity = SENSITIVITY
        self.Zoom = ZOOM
        self.updateCameraVectors()

        # Limites da cena (ajuste conforme o tamanho do seu skybox/chão)
        self.min_x = -58.0
        self.max_x = 58.0
        self.min_y = 0.5  # Altura mínima acima do chão
        self.max_y = 50.0 # Altura máxima
        self.min_z = -58.0
        self.max_z = 58.0


    def get_view_matrix(self):
        return glm.lookAt(self.Position, self.Position + self.Front, self.Up)

    def get_projection_matrix(self, width, height):
        aspect_ratio = width / height if height > 0 else 1.0
        near = 0.1
        far = 200.0 # Aumentar o far plane para ver objetos mais distantes
        if near <= 0: near = 0.1
        if far <= near: far = near + 100.0
        fov_rad = glm.radians(max(1.0, min(90.0, self.Zoom)))
        return glm.perspective(fov_rad, aspect_ratio, near, far)

    def process_keyboard(self, direction, deltaTime):
        velocity = self.MovementSpeed * deltaTime
        new_position = glm.vec3(self.Position) # Copia a posição atual

        if direction == Camera_Movement.FORWARD:
            new_position += self.Front * velocity
        if direction == Camera_Movement.BACKWARD:
            new_position -= self.Front * velocity
        if direction == Camera_Movement.LEFT:
            new_position -= self.Right * velocity
        if direction == Camera_Movement.RIGHT:
            new_position += self.Right * velocity
        if direction == Camera_Movement.UP: # Movimento vertical
            new_position += self.WorldUp * velocity
        if direction == Camera_Movement.DOWN: # Movimento vertical
            new_position -= self.WorldUp * velocity

        # Restringe o movimento aos limites definidos
        new_position.x = glm.clamp(new_position.x, self.min_x, self.max_x)
        new_position.y = glm.clamp(new_position.y, self.min_y, self.max_y)
        new_position.z = glm.clamp(new_position.z, self.min_z, self.max_z)
        
        self.Position = new_position


    def process_mouse_movement(self, xoffset, yoffset, constrainPitch = True):
        xoffset *= self.MouseSensitivity
        yoffset *= self.MouseSensitivity

        self.Yaw   += xoffset
        self.Pitch += yoffset

        if constrainPitch:
            if self.Pitch > 89.0: self.Pitch = 89.0
            if self.Pitch < -89.0: self.Pitch = -89.0
        self.updateCameraVectors()

    def process_mouse_scroll(self, yoffset):
        self.Zoom -= yoffset
        if self.Zoom < 1.0: self.Zoom = 1.0
        if self.Zoom > 90.0: self.Zoom = 90.0

    def updateCameraVectors(self):
        front = glm.vec3()
        front.x = glm.cos(glm.radians(self.Yaw)) * glm.cos(glm.radians(self.Pitch))
        front.y = glm.sin(glm.radians(self.Pitch))
        front.z = glm.sin(glm.radians(self.Yaw)) * glm.cos(glm.radians(self.Pitch))
        self.Front = glm.normalize(front)
        self.Right = glm.normalize(glm.cross(self.Front, self.WorldUp))
        self.Up    = glm.normalize(glm.cross(self.Right, self.Front))
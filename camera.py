# camera.py
import glm
import math

# Defines several possible options for camera movement. Used as abstraction to stay away from window-system specific input methods
class Camera_Movement:
    FORWARD = 0
    BACKWARD = 1
    LEFT = 2
    RIGHT = 3

# Default camera values
YAW         = -90.0
PITCH       =  0.0
SPEED       =  2.5
SENSITIVITY =  0.1
ZOOM        =  45.0 # FOV

class Camera:
    def __init__(self, position = glm.vec3(0.0, 0.0, 3.0), up = glm.vec3(0.0, 1.0, 0.0), yaw = YAW, pitch = PITCH):
        self.Position = position
        self.Front = glm.vec3(0.0, 0.0, -1.0)
        self.Up = glm.vec3(0.0, 1.0, 0.0) # Será recalculado
        self.Right = glm.vec3(1.0, 0.0, 0.0) # Será recalculado
        self.WorldUp = up
        # euler Angles
        self.Yaw = yaw
        self.Pitch = pitch
        # camera options
        self.MovementSpeed = SPEED
        self.MouseSensitivity = SENSITIVITY
        self.Zoom = ZOOM # FOV
        self.updateCameraVectors()

    def get_view_matrix(self):
        return glm.lookAt(self.Position, self.Position + self.Front, self.Up)

    def get_projection_matrix(self, width, height):
         # Garantir que aspect ratio não seja zero
        aspect_ratio = width / height if height > 0 else 1.0
        # Garantir que near e far não sejam iguais ou negativos
        near = 0.1
        far = 100.0
        if near <= 0: near = 0.1
        if far <= near: far = near + 100.0

        # Garantir que fov esteja dentro de um intervalo razoável
        fov_rad = glm.radians(max(1.0, min(90.0, self.Zoom))) # Limita FOV entre 1 e 90 graus

        return glm.perspective(fov_rad, aspect_ratio, near, far)

    def process_keyboard(self, direction, deltaTime):
        velocity = self.MovementSpeed * deltaTime
        if direction == Camera_Movement.FORWARD:
            self.Position += self.Front * velocity
        if direction == Camera_Movement.BACKWARD:
            self.Position -= self.Front * velocity
        if direction == Camera_Movement.LEFT:
            self.Position -= self.Right * velocity
        if direction == Camera_Movement.RIGHT:
            self.Position += self.Right * velocity
        # Não permitir que a câmera "afunde" no chão (simplificado)
        # self.Position.y = max(self.Position.y, 0.0)

    def process_mouse_movement(self, xoffset, yoffset, constrainPitch = True):
        xoffset *= self.MouseSensitivity
        yoffset *= self.MouseSensitivity

        self.Yaw   += xoffset
        self.Pitch += yoffset

        # make sure that when pitch is out of bounds, screen doesn't get flipped
        if constrainPitch:
            if self.Pitch > 89.0:
                self.Pitch = 89.0
            if self.Pitch < -89.0:
                self.Pitch = -89.0

        # update Front, Right and Up Vectors using the updated Euler angles
        self.updateCameraVectors()

    def process_mouse_scroll(self, yoffset):
        self.Zoom -= yoffset
        if self.Zoom < 1.0:
            self.Zoom = 1.0
        if self.Zoom > 90.0: # Aumentado o limite superior do FOV
            self.Zoom = 90.0

    def updateCameraVectors(self):
        # calculate the new Front vector
        front = glm.vec3()
        front.x = glm.cos(glm.radians(self.Yaw)) * glm.cos(glm.radians(self.Pitch))
        front.y = glm.sin(glm.radians(self.Pitch))
        front.z = glm.sin(glm.radians(self.Yaw)) * glm.cos(glm.radians(self.Pitch))
        self.Front = glm.normalize(front)
        # also re-calculate the Right and Up vector
        self.Right = glm.normalize(glm.cross(self.Front, self.WorldUp))  # normalize the vectors, because their length gets closer to 0 the more you look up or down which results in slower movement.
        self.Up    = glm.normalize(glm.cross(self.Right, self.Front))
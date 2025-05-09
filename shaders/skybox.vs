#version 330 core
layout (location = 0) in vec3 aPos;

out vec3 TexCoords;

uniform mat4 projection;
uniform mat4 view; // View sem translação será passada aqui

void main()
{
    TexCoords = aPos;
    vec4 pos = projection * view * vec4(aPos, 1.0);
    // Truque para garantir que o skybox esteja sempre atrás de tudo
    gl_Position = pos.xyww;
}
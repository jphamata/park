#version 330 core
out vec4 FragColor;

in vec3 TexCoords;

uniform samplerCube skybox; // Uniform para a textura cubemap

void main()
{
    FragColor = texture(skybox, TexCoords);
}
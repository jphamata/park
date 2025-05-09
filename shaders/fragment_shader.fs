#version 330 core
out vec4 FragColor;

in vec2 TexCoord; // Recebe do vertex shader

uniform sampler2D texture1; // Uniform para a textura 2D

void main()
{
    FragColor = texture(texture1, TexCoord); // Usa a textura
    // Para testar sem textura: FragColor = vec4(1.0f, 0.5f, 0.2f, 1.0f); // Cor laranja
}
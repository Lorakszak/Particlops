#version 330 core

in vec3 v_color;
in float v_alpha;
flat in float v_shape;

out vec4 fragColor;

void main() {
    vec2 coord = gl_PointCoord * 2.0 - 1.0;
    int shape = int(v_shape + 0.5);
    float dist;

    if (shape == 1) {
        // Square
        dist = max(abs(coord.x), abs(coord.y));
    } else if (shape == 2) {
        // Triangle (equilateral, pointing up)
        float tx = abs(coord.x) * 0.866025 + coord.y * 0.5;
        float ty = -coord.y;
        dist = max(tx, ty) * 0.8 + 0.2;
    } else if (shape == 3) {
        // Diamond -- scaled by 1/sqrt(2) so it fills the sprite like square
        dist = (abs(coord.x) + abs(coord.y)) * 0.707;
    } else if (shape == 4) {
        // Star (5-point, polar cosine lobes)
        float angle = atan(coord.y, coord.x);
        float r = length(coord);
        float star_r = 0.5 + 0.5 * cos(angle * 5.0);
        dist = r / star_r;
    } else if (shape == 5) {
        // Ring
        float r = length(coord);
        dist = abs(r - 0.6) / 0.15;
    } else {
        // Circle (default, shape == 0)
        dist = length(coord);
    }

    if (dist > 1.0) {
        discard;
    }

    float alpha = v_alpha * (1.0 - smoothstep(0.5, 1.0, dist));
    fragColor = vec4(v_color, alpha);
}

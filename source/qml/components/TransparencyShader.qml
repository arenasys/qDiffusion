	
import QtQuick 2.0

Item {
    id: root
    property real gridSize: 15.0
    layer.enabled: true
    layer.effect: ShaderEffect {
        property real gridSize: root.gridSize
        vertexShader: "
            uniform highp mat4 qt_Matrix;
            attribute highp vec4 qt_Vertex;
            attribute highp vec2 qt_MultiTexCoord0;
            varying highp vec2 coord;
            void main() {
                coord = qt_Vertex.xy;
                gl_Position = qt_Matrix * qt_Vertex;
            }"
        fragmentShader: "
            varying highp vec2 coord;
            uniform float gridSize;
            void old_main() {
                vec2 pos = floor(coord / gridSize);
                gl_FragColor.xyz = vec3(0.2, 0.2, 0.2) + mod(pos.x + mod(pos.y, 2.0), 2.0) * 0.2;
                gl_FragColor.w = 1.0;
            }
            void main() {
                vec2 pos = coord;
                gl_FragColor.xyz = vec3(0.11, 0.11, 0.11);
                if(mod(pos.x+1.0, gridSize) <= 1.0 || mod(pos.y+1.0, gridSize) <= 1.0) {
                    gl_FragColor.xyz = vec3(0.16, 0.16, 0.16);
                    if(mod(pos.x+1.0, 2.0*gridSize) <= 1.0 || mod(pos.y+1.0, 2.0*gridSize) <= 1.0) {
                        gl_FragColor.xyz = vec3(0.25, 0.25, 0.25);
                    }
                }

                gl_FragColor.w = 1.0;
            }"
    }
}
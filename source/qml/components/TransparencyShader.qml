	
import QtQuick 2.0

Item {
    id: root
    property real gridSize: 15.0
    layer.enabled: true
    layer.effect: ShaderEffect {
        property real gridSize: root.gridSize
        property size textureSize: Qt.size(root.width, root.height)
        vertexShader: "
            uniform highp mat4 qt_Matrix;
            uniform highp vec2 textureSize;
            attribute highp vec4 qt_Vertex;
            attribute highp vec2 qt_MultiTexCoord0;
            varying highp vec2 coord;
            void main() {
                coord = qt_Vertex.xy;//- floor(textureSize/2.0);
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
                vec2 pos = floor(coord / gridSize);
                gl_FragColor.xyz = vec3(0.11, 0.11, 0.11) + mod(pos.x + mod(pos.y, 2.0), 2.0) * 0.007;
                if(mod(coord.x+1.0, gridSize) <= 1.0 || mod(coord.y+1.0, gridSize) <= 1.0) {
                    gl_FragColor.xyz = vec3(0.17, 0.17, 0.17);
                    if(mod(coord.x+1.0, 2.0*gridSize) <= 1.0 || mod(coord.y+1.0, 2.0*gridSize) <= 1.0) {
                        gl_FragColor.xyz = vec3(0.23, 0.23, 0.23);
                    }
                }

                gl_FragColor.w = 1.0;
            }"
    }
}
	
import QtQuick 2.0

ShaderEffect {
    property var fSize: Qt.size(width, height)
    property var fColor: Qt.vector4d(1, 1, 1, 1)
    vertexShader: "
        uniform highp mat4 qt_Matrix;
        attribute highp vec4 qt_Vertex;
        attribute highp vec2 qt_MultiTexCoord0;
        varying highp vec2 fCoord;
        void main() {
            fCoord = qt_Vertex.xy;
            gl_Position = qt_Matrix * qt_Vertex;
        }"
    fragmentShader: "
        uniform lowp sampler2D source;
        uniform lowp float qt_Opacity;
        varying highp vec2 fCoord;
        uniform highp vec2 fSize;
        uniform highp vec4 fColor;
        void main() {
            vec4 c = fColor;

            bool t0 = texture2D(source, (fCoord + vec2(-1.0, -1.0))/fSize).a >= 0.5;
            bool t1 = texture2D(source, (fCoord + vec2(0.0, -1.0))/fSize).a >= 0.5;
            bool t2 = texture2D(source, (fCoord + vec2(1.0, -1.0))/fSize).a >= 0.5;
            bool t3 = texture2D(source, (fCoord + vec2(-1.0, 0.0))/fSize).a >= 0.5;
            bool t4 = texture2D(source, (fCoord + vec2(0.0, 0.0))/fSize).a >= 0.5;
            bool t5 = texture2D(source, (fCoord + vec2(1.0, 0.0))/fSize).a >= 0.5;
            bool t6 = texture2D(source, (fCoord + vec2(-1.0, 1.0))/fSize).a >= 0.5;
            bool t7 = texture2D(source, (fCoord + vec2(0.0, 1.0))/fSize).a >= 0.5;
            bool t8 = texture2D(source, (fCoord + vec2(1.0, 1.0))/fSize).a >= 0.5;

            bool nearEdge = !(t0 == t1 && t0 == t2 && t0 == t3 && t0 == t4 && t0 == t5 && t0 == t6 && t0 == t7 && t0 == t8);
            bool onEdge = nearEdge && t4;

            vec4 o;
            if(onEdge) {
                o = c;
            } else {
                o = texture2D(source, fCoord/fSize);
            }

            gl_FragColor = o * qt_Opacity;
        }"
}
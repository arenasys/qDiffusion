	
import QtQuick 2.0

ShaderEffect {
    property var fSize: Qt.size(width, height)
    property real fDashOffset: 0.0
    property real fDashLength: 6.0
    property bool fDashStroke: true
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
        uniform float fDashOffset;
        uniform float fDashLength;
        uniform bool fDashStroke;
        void main() {
            vec4 c;
            if(fDashStroke) {
                float f = floor(mod((fDashOffset/2.0) + (fCoord.x + fCoord.y)/fDashLength, 2.0));
                c = vec4(f,f,f,1.0);
            } else {
                c = texture2D(source, fCoord/fSize);
            }

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
                vec4 o = vec4(0.0, 0.0, 0.0, 0.0);
            }

            gl_FragColor = o * qt_Opacity;
        }"
}
# glsl 120 # extension GL_ARB_texture_rectangle : enable
OculusWarpVert = """
    #version 120

    // GLSL(120,
    uniform vec2 EyeToSourceUVScale;
    uniform vec2 EyeToSourceUVOffset;
    uniform mat4 EyeRotationStart;
    uniform mat4 EyeRotationEnd;

    varying vec4 oColor;
    varying vec2 oTexCoord0;
    varying vec2 oTexCoord1;
    varying vec2 oTexCoord2;

    void main()
    {
        gl_Position.x = gl_Vertex.x;
        gl_Position.y = gl_Vertex.y;
        gl_Position.z = .0;
        gl_Position.w = 1.0;

        // Vertex inputs are in TanEyeAngle space for the R,G,B channels (i.e. after chromatic aberration and distortion).
        // These are now "real world" vectors in direction (x,y,1) relative to the eye of the HMD.
        vec3 TanEyeAngleR = vec3 ( gl_Normal.x, gl_Normal.y, 1.0 );
        vec3 TanEyeAngleG = vec3 ( gl_Color.r, gl_Color.g, 1.0 );
        vec3 TanEyeAngleB = vec3 ( gl_Color.b, gl_Color.a, 1.0 );

        mat3 EyeRotation;
        EyeRotation[0] = mix ( EyeRotationStart[0], EyeRotationEnd[0], gl_Vertex.z ).xyz;
        EyeRotation[1] = mix ( EyeRotationStart[1], EyeRotationEnd[1], gl_Vertex.z ).xyz;
        EyeRotation[2] = mix ( EyeRotationStart[2], EyeRotationEnd[2], gl_Vertex.z ).xyz;

        vec3 TransformedR = EyeRotation * TanEyeAngleR;
        vec3 TransformedG = EyeRotation * TanEyeAngleG;
        vec3 TransformedB = EyeRotation * TanEyeAngleB;

        // Project them back onto the Z=1 plane of the rendered images.
        float RecipZR = 1.0 / TransformedR.z;
        float RecipZG = 1.0 / TransformedG.z;
        float RecipZB = 1.0 / TransformedB.z;
        vec2 FlattenedR = vec2 ( TransformedR.x * RecipZR, TransformedR.y * RecipZR );
        vec2 FlattenedG = vec2 ( TransformedG.x * RecipZG, TransformedG.y * RecipZG );
        vec2 FlattenedB = vec2 ( TransformedB.x * RecipZB, TransformedB.y * RecipZB );

        // These are now still in TanEyeAngle space.
        // Scale them into the correct [0-1],[0-1] UV lookup space (depending on eye)
        vec2 SrcCoordR = FlattenedR * EyeToSourceUVScale + EyeToSourceUVOffset;
        vec2 SrcCoordG = FlattenedG * EyeToSourceUVScale + EyeToSourceUVOffset;
        vec2 SrcCoordB = FlattenedB * EyeToSourceUVScale + EyeToSourceUVOffset;

        oTexCoord0 = SrcCoordR;
        oTexCoord0.y = 1.0-oTexCoord0.y;
        oTexCoord1 = SrcCoordG;
        oTexCoord1.y = 1.0-oTexCoord1.y;
        oTexCoord2 = SrcCoordB;
        oTexCoord2.y = 1.0-oTexCoord2.y;

        //Vignette
        oColor = vec4(gl_Normal.z, gl_Normal.z, gl_Normal.z, gl_Normal.z);
    }
"""
                               
OculusWarpFrag = """
    #version 120

    // GLSL(120, 
    uniform sampler2DRect Texture;
    uniform vec2 TextureScale;
    uniform float fade;
    varying vec4 oColor;
    varying vec2 oTexCoord0;
    varying vec2 oTexCoord1;
    varying vec2 oTexCoord2;
    
    void main()
    {
      gl_FragColor.r = oColor.r * texture2DRect(Texture, oTexCoord0 * TextureScale).r;
      gl_FragColor.g = oColor.g * texture2DRect(Texture, oTexCoord1 * TextureScale).g;
      gl_FragColor.b = oColor.b * texture2DRect(Texture, oTexCoord2 * TextureScale).b;
      gl_FragColor.a = fade;
    }
"""

HLSL_vert = '''Example vert_shader

float2 EyeToSourceUVScale, EyeToSourceUVOffset;
float4x4 EyeRotationStart, EyeRotationEnd;
float2 TimewarpTexCoord(float2 TexCoord, float4x4 rotMat)
{
    // Vertex inputs are in TanEyeAngle space for the R,G,B channels (i.e. after chromatic
    // aberration and distortion). These are now "real world" vectors in direction (x,y,1)
    // relative to the eye of the HMD. Apply the 3x3 timewarp rotation to these vectors.
    float3 transformed = float3( mul ( rotMat, float4(TexCoord.xy, 1, 1) ).xyz);
    // Project them back onto the Z=1 plane of the rendered images.
    float2 flattened = (transformed.xy / transformed.z);
    // Scale them into ([0,0.5],[0,1]) or ([0.5,0],[0,1]) UV lookup space (depending on eye)
    return(EyeToSourceUVScale * flattened + EyeToSourceUVOffset);
}
void main(in float2 Position : POSITION, in float timewarpLerpFactor : POSITION1,
in float Vignette : POSITION2, in float2 TexCoord0 : TEXCOORD0,
in float2 TexCoord1 : TEXCOORD1, in float2 TexCoord2 : TEXCOORD2,
out float4 oPosition : SV_Position, out float2 oTexCoord0 : TEXCOORD0,
out float2 oTexCoord1 : TEXCOORD1, out float2 oTexCoord2 : TEXCOORD2,
out float oVignette : TEXCOORD3)
{
    float4x4 lerpedEyeRot = lerp(EyeRotationStart, EyeRotationEnd, timewarpLerpFactor);
    oTexCoord0 = TimewarpTexCoord(TexCoord0,lerpedEyeRot);
    oTexCoord1 = TimewarpTexCoord(TexCoord1,lerpedEyeRot);
    oTexCoord2 = TimewarpTexCoord(TexCoord2,lerpedEyeRot);
    oPosition = float4(Position.xy, 0.5, 1.0);
}
'''
HLSL_frag = ''' Example frag_shader

Texture2D Texture : register(t0);
SamplerState Linear : register(s0);
float4 main(in float4 oPosition : SV_Position, in float2 oTexCoord0 : TEXCOORD0,
in float2 oTexCoord1 : TEXCOORD1, in float2 oTexCoord2 : TEXCOORD2,
in float oVignette : TEXCOORD3) : SV_Target
{
    // 3 samples for fixing chromatic aberrations
    float R = Texture.Sample(Linear, oTexCoord0.xy).r;
    float G = Texture.Sample(Linear, oTexCoord1.xy).g;
    float B = Texture.Sample(Linear, oTexCoord2.xy).b;
    return (oVignette*float4(R,G,B,1));
}
'''
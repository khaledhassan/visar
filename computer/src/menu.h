#ifndef GUARD_IPOFLIQNVOQNLFXQ
#define GUARD_IPOFLIQNVOQNLFXQ

#include <oglplus/gl.hpp>

namespace visar {
  namespace menu {
    class Menu : public rendering::IModule {
      public:
        Menu(void) { }
        void draw() {
          // Vertex shader
          oglplus::VertexShader vs;
        
          // Set the vertex shader source
          vs.Source(" \
            #version 130\n \
            in vec3 Position; \
            varying vec3 verpos; \
            void main(void) { \
              gl_Position = vec4(Position, 1.0); \
              verpos = Position; \
            } \
          ");
          
          // Compile it
          vs.Compile();
          
          // Fragment shader
          oglplus::FragmentShader fs;
          
          // Set the fragment shader source
          fs.Source(" \
            #version 130\n \
            out vec4 fragColor; \
            varying vec3 verpos; \
            void main(void) \
            { \
              fragColor = vec4(1.0, 1.0, 1.0, 1.0); \
            } \
          ");
          
          // Compile it
          fs.Compile();
          
          // Program
          oglplus::Program prog;
          
          // Attach the shaders to the program
          prog.AttachShader(vs);
          prog.AttachShader(fs);
          
          //  Link and use it
          prog.Link();
          prog.Use();
          
          // A vertex array object for the menu rectangle
          oglplus::VertexArray menu;
          
          // VBO for the menu's vertices
          oglplus::Buffer verts;
          
          // Bind the VBO for the menu
          menu.Bind();
          
          /*GLfloat menu_verts[24] = {
            -1.0f, 1.0f, 0.0f,
            -.9f, 1.0f, 0.0f,
            -.9f, -1.0f, 0.0f,
            -1.0f, 1.0f, 0.0f,
            -.9f, -1.0f, 0.0f,
            -1.0f, -1.0f, 0.0f,
          };*/
          
          GLfloat menu_verts[24] = {
            -1.0f, 1.0f, 0.0f,
            1.0f, 1.0f, 0.0f,
            1.0f, -1.0f, 0.0f,
            -1.0f, 1.0f, 0.0f,
            1.0f, -1.0f, 0.0f,
            -1.0f, -1.0f, 0.0f,
          };
          
          // Bind the VBO for the menu verticies
          verts.Bind(oglplus::Buffer::Target::Array);
          
          // Upload the data
          oglplus::Buffer::Data(oglplus::Buffer::Target::Array, 24, menu_verts);
          
          // Setup the vertex attribs array for the vertices
          oglplus::VertexArrayAttrib vert_attr(prog, "Position");
          vert_attr.Setup<oglplus::Vec3f>();
          vert_attr.Enable();
          
          oglplus::Context::DrawArrays(oglplus::PrimitiveType::Triangles, 0, 6);
        }
    };
  }
}

#endif

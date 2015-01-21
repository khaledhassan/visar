import numpy as np
from vispy.gloo import Program, gl
from vispy import app, gloo
import threading

HUD_DEPTH = 0.2 # minimum depth
FPS = 1 # hopefully not too optimistic (not doing anything)

VERT_SHADER_TEX = """ //texture vertex shader
attribute vec3 position;
attribute vec2 texcoord;
varying vec2 v_texcoord;

void main(void){
    v_texcoord = texcoord; //send tex coordinates
    gl_Position = vec4(position.xyz, 1.0);
}"""

FRAG_SHADER_TEX = """ // texture fragment shader
uniform sampler2D texture;
varying vec2 v_texcoord;

void main(){
    gl_FragColor = texture2D(texture, v_texcoord);
}"""

# full renderable 2D area
vPosition_full = np.array([[-1.0, -1.0, 0.0], [+1.0, -1.0, 0.0],
                           [-1.0, +1.0, 0.0], [+1.0, +1.0, 0.0]], np.float32)
vTexcoord_full = np.array([[0.0, 0.0], [0.0, 1.0],
                           [1.0, 0.0], [1.0, 1.0]], np.float32)

renderer = None # singleton, don't reference this or declare an instance of the class
                      
# thread locking for updating stuff
renderingLock = threading.Lock()
def renderLock(func):
  def locked(*args, **kwargs):
    global renderingLock
    renderingLock.acquire()
    result = func(*args, **kwargs)
    renderingLock.release()
    return result
  return locked
                      
class Renderer(app.Canvas): # canvas is a GUI object
  def __init__(self, size=(560,420)):    
    self.renderList = [] # list of modules to render
    self.updateQueue = [] # list of updates to perform
    
    # initialize gloo context
    app.Canvas.__init__(self, keys='interactive')
    self.size = size # get the size
            
    # create texture to render modules to
    shape = self.size[1], self.size[0]
    self._rendertex = gloo.Texture2D(shape=shape+(3,))
  
    # create Frame Buffer Object, attach color/depth buffers
    self._fbo = gloo.FrameBuffer(self._rendertex, gloo.RenderBuffer(shape))
    
    # create texture rendering program
    self.tex_program = gloo.Program(VERT_SHADER_TEX, FRAG_SHADER_TEX)
  
    # create program to render the results (TEST ONLY, same as before)
    # JAKE: replace this with your shaders
    self._program2 = gloo.Program(VERT_SHADER_TEX, FRAG_SHADER_TEX)
    self._program2['position'] = gloo.VertexBuffer(vPosition_full)
    self._program2['texcoord'] = gloo.VertexBuffer(vTexcoord_full)
    self._program2['texture']  = self._rendertex
    
    # set an update timer to run every FPS
    self.interval = 1/FPS
    self._timer = app.Timer('auto',connect=self.on_timer, start=True)
  
  def on_resize(self, event):
    width, height = event.size
    gloo.set_viewport(0,0,width,height)
    
  def on_draw(self, event):
    # draw scene to FBO instead of output buffer
    with self._fbo:
      gloo.set_clear_color('black')
      gloo.clear(color=True, depth=True)
      gloo.set_viewport(0,0, *self.size)
      # render each of the modules
      for module in self.renderList:   
        if(module.textured and module.positioned):  # make sure it's ready
          module.program.draw('triangle_strip')     # draw the module
        else: print module
    
    # draw to full screen
    gloo.set_clear_color('black')
    gloo.clear(color=True,depth=True)
    self._program2.draw('triangle_strip')
  
  # update the display
  @renderLock  
  def on_timer(self, event):
    for module in self.updateQueue:
      module.doUpdate()   # update all modules
    self.updateQueue = [] # clear the queue
    self.update() # update self    
    
  # run preliminary update, then start rendering
  def startRender(self):
    #for module in self.updateQueue:
    #  module.doUpdate()
    self.show()
    app.run()

# enforce singleton pattern
def getRenderer():
  global renderer
  if (renderer is None): 
    renderer = Renderer()
  return renderer
  
# class for texture rendering  
class Drawable:
  @renderLock
  def __init__(self):
    self.program = gloo.Program(VERT_SHADER_TEX, FRAG_SHADER_TEX)
    self.program['texcoord'] = gloo.VertexBuffer(vTexcoord_full) # assume full usage
    self.textured = False
    self.positioned = False
    self.updates = [] # list of updates to perform
    renderer.renderList.append(self) # add to render stack
  
  # set the texture
  @renderLock
  def setTexture(self, data):
    self.addUpdate(('texture', gloo.Texture2D(data))) # queue the texture

  
  # set the verticies, make sure they're 3d and less than the hud depth
  @renderLock
  def setVerticies(self, verticies):
    for v in verticies: # add a default depth to verticies
      if(len(v) < 3): v.append(HUD_DEPTH)
      elif(v[2] < HUD_DEPTH): v[2] = HUD_DEPTH
    self.addUpdate(('position',verticies)) # define the position
  
  # add update to list
  def addUpdate(self, update):
    self.updates.append(update)       # add the update
    renderer.updateQueue.append(self) # add update to queue
  
  # perform updates
  def doUpdate(self):
    for update in self.updates: # get all updates
      if update[0] == 'texture': # determine type
        self.program['texture'] = update[1]
        self.textured = True
      elif update[0] == 'position':
        self.program['position'] = update[1]
        self.positioned = True
    self.updates = [] # reset the list
  
  # pull render off of stack (would put in destructor, but wouldn't get called)
  @renderLock
  def stopRendering(self):
    renderer.renderList.remove(self)
  
  

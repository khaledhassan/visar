from subprocess import *
import time, os
import threading
import socket
import interface

AUDIO_PROGRAM = '../c/audio' # path to audio module
CONTROL_CLIENT = 19101        # TCP comms port for handshaking (client)
CONTROL_SERVER = 19102        # TCP comms port for handshaking (server)
AUDIO_SERVER   = 19103        # UDP port for audio data (server mode)
AUDIO_CLIENT   = 19104        # UDP port for audio data (client mode)
AUDIO_WAIT_TM  = .05          # wait 50ms between operations
SERVER_TIMEOUT = 1            # timeout for server socket (in seconds)

# thread locking
lock = threading.RLock()
def thread_lock(func):
  def locked_func(*args,**kwargs):
    global lock
    lock.acquire()
    ret = func(*args, **kwargs)
    lock.release()
    return ret
  return locked_func

# audio controller class, interfaces with other units and the standalone audio module
# interface events send string tuples (status, host/argument)
class AudioController(interface.Interface):
  def __init__(self):
    interface.Interface.__init__(self)
    self.connection = None    # connection state (host, port, mode)
    self.voice_event = None   # event handler for voice comms
    self.child = Popen(AUDIO_PROGRAM, bufsize=0, stdin=PIPE, stdout=PIPE, universal_newlines=True) # open subprocess
    self.kill_flag = False
    self.input_buffer = ''
    
    # create the socket objects
    self.c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # create the thread objects and start the threads
    self.comms  = threading.Thread(target=self.comms_thread)
    self.parse  = threading.Thread(target=self.parse_thread)
    self.server = threading.Thread(target=self.server_thread)
    self.comms.start()
    self.parse.start()
    self.server.start()
    
  
  def destroy(self):
    self.kill_flag = True # kill the process
    
    # send shutdown to child process
    lock.acquire()
    self.child.stdin.write('shutdown\n') # shutdown thread when the module dies
    lock.release()
    
    self.c_sock.close() # close the socket
  
  # start audio communication with network device
  @thread_lock
  def start(self, host, port=AUDIO_SERVER, mode='both'):
    if(self.connection is not None):
      print 'Error, conection already active' + self.connection
      return None;
  
    self.connection = (host, port, mode) # store connection information
    command = 'start ' + mode + ' -host ' + host + ' -port ' + str(AUDIO_CLIENT) + '\n'
    self.child.stdin.write(command) # send start command
    
    self.do_updates('Connected', host) # notify connection success
  

  # connect to to client using a name
  
  
  # stop audio communication
  @thread_lock
  def stop(self):
    self.child.stdin.write('stop both\n')    # send stop command
    if(self.voice_event is not None): self.connection = ('voice', None, 'mic') # check if voice was active (prevents shutdown)
    else: self.connection = None              # connection is no longer active
    
    self.do_updates('Disconnected',None) # notify connection termination
  
  @thread_lock
  def set_volume(self, volume):
    '''Set the speaker volume for the system.
       Volume must be integer between 0 and 100
    '''
    
    #check range and type of volume
    if (type(volume) is not int) or volume > 100 or volume < 0: 
      print 'Invalid Volume: ' + str(volume)
      return
    
    self.child.stdin.write('set -volume ' + str(volume) + ' \n')
    
    
  # start the voice controller, requires an event handler
  # Events are passed back as tuples of (type, command/error text)
  @thread_lock
  def start_voice(self, event):
    self.child.stdin.write('voice_start\n')
    self.voice_event = event
    if(self.connection is None):
      self.connection = ('voice', None, 'mic') # connection is in voice mode
  
  # stops the voice controller
  def stop_voice(self):
    global lock
    lock.acquire()
    self.child.stdin.write('voice_stop\n')
    lock.release()
    self.voice_event.do_updates(('VCERR','stopped_vc')) # send shutdown update
    self.voice_event = None # remove the event handler
    if(self.connection is not None and self.connection[0] == 'voice'): 
      self.connection = None  # clear the connection state
  
  # thread to handle communicating with child process
  def comms_thread(self):
    while(not self.kill_flag): self.do_comms() # do the comms
    print 'shutdown'
  
  # do the communcation to child process
  def do_comms(self):
    try: 
      out = os.read(self.child.stdout.fileno(),80) # get data out
      global lock
      lock.acquire()
      self.input_buffer += out # append responses to input buffer
      lock.release()
    except: print 'Comms Error, Possibly the result of a shutdown'
  
  # thread to handle parsing the output from the child process
  def parse_thread(self):
    while(not self.kill_flag): 
      time.sleep(AUDIO_WAIT_TM) # wait between operations
      self.do_parse(self.split_parse_buffer()) # parse the input
  
  # split the parse into seperate commands
  @thread_lock
  def split_parse_buffer(self):
    comms = self.input_buffer.split('\n') # split the input on newlines
    self.input_buffer = comms.pop()  # put the last result back on the buffer (might be incomplete)
    return comms    # return the comands
  
  # iterate over input and parse commands
  def do_parse(self, parse):
    for line in parse:
      part = line.split(':') # split line across colon
      if len(part) < 2: part.insert(0,'') # make sure we have 2 inputs
      if(self.voice_event is not None): 
        self.voice_event.do_updates((part[0], part[1])) # send the event
  
  # server handler thread
  def server_thread(self):
    self.s_sock.bind(('',CONTROL_SERVER))
    self.s_sock.listen(1)
    self.s_sock.settimeout(SERVER_TIMEOUT) # timeout after 1 second
    global lock # use the global lock object
    while(not self.kill_flag):
      try: conn, addr = self.s_sock.accept() # accept a connection
      except: continue  # loop on timeout
      data = conn.recv(1024) # get input from socket
      datas = data.split('\n') # split the input args
      lock.acquire()
      self.connection(addr[0], AUDIO_CLIENT, datas[0]) # setup connection
      command = 'start ' + datas[0] + ' -host ' + addr[0] + ' -port ' + str(AUDIO_SERVER) + '\n'
      self.child.stdin.write(command) # send start command
      lock.release()
      while conn is not None:
        try:
          if(conn.recv(10) == 'shutdown\n'): # wait for shutdown
            conn.close() # close the socket
            conn = None # set it to none so loop exits
        except: pass # ignore timeouts
      
      # shutdown the module
      lock.acquire()
      self.child.stdin.write('stop both\n')    # send stop command
      if(voice_event is not None): self.connection = ('voice', None, 'mic') # check if voice was active (prevents shutdown)
      else: self.connection = None              # connection is no longer active
      lock.release()


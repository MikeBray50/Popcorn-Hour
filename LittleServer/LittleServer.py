"""
My Popcorn Hour Library - Python - The Little Server That Could alpha
Display html pages and able to run remote commands via web server.
'shutdown' is a reserved command which is used to close the server
Note: this must run form the popcorn hour device itself

Configuration: see 'config.xml' for setup of server port and commands

HTML example:
- Create file called "index.html' (this is also used as default file)
- Add the following text to the file
  <html>
    <head>
      <title>Popcorn Hour Commander</title>
    </head>
    <body bgcolor="LightSkyBlue">
      <center>
        <h1>Popcorn Hour Commander</h1>
        <br />
        <a href="/command?id=shuffle&arg=/share/Video/Music">Music</a>
      </center>
    </body>
  </html>
- This shows an html with a single link which runs the command 'shuffle' with an argument
- In 'config.xml' the command should be configured something like:
  <command id="shuffle" run="python /share/Scripts/ShuffleThis.py" args="true" />

Run:
- For a single run use telnet to connect to device
- use 'cd' to navigate to the directory containing the script
- run 'nohup python LittleServer.py &'
- This runs the script in the background and allows exiting telnet without closing the server

Install
- This allows the server to start everytime the device start
- Locate 'start_app.sh' on the drive root which contains the script
- Append the following to the END of the file
  #Run little server
  cd [full path of script directory]
  nohup python LittleServer.py &
- For example replace [full...] with /share/LittleServer 

Disclaimer:
The code is free to use and modify.
You may distribute freely but not commercially
I take no responsibility to any harm caused to your device
I'm not affiliated with Syabas, Cloud Media or any other Popcorn Hour related organization.
The code is in alpha mode and only been tested on a single device (A-400)

Author: Shachar Mossek
User:   sm2k
Mail:   shachar.mossek@gmail.com
Date:   11/08/2013 (11-AUG-2013)
"""

#Imports
from xml.dom.minidom import parseString #xml
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer #Web server
from os import curdir, sep #html files
import urlparse #Web server
import commands #command processing
import sys #shutdown

#Classes
class Command:
    """
    Command data
    """
    def __init__(self, id, run, allowArgs):
        """Initialize command"""
        self._id = id
        self._run = run
        try:
            self._allowArgs = allowArgs.lower() == 'true'
        except:
            self._allowArgs = False

    def getId(self):
        """Get command id"""
        return self._id

    def getRun(self):
        """Get command run path"""
        return self._run

    def getAllowArgs(self):
        """Get whether command allowArgs"""
        return self._allowArgs

class Config:
    """
    Configuration class
    Reads from configuration xml
    """
    def __init__(self):
        """Initialize with default"""
        self._port = 7070
        self._dir = ''
        self._commands = {}
        self._commandPrefix = 'nohump '
        self._commandSuffix = ' &'

    def load(self, path='config.xml'):
        try:
            #read file
            f = open(path, 'r')
            data = f.read()
            f.close()
            #Parse data
            root = parseString(data)
            #Extract port
            nodes = root.getElementsByTagName('port')
            if not nodes == None and len(nodes) > 0:
                self._port = int(nodes[0].firstChild.data)
            #Extract directory
            nodes = root.getElementsByTagName('dir')
            if not nodes == None and len(nodes) > 0:
                data = nodes[0].firstChild
                if not data == None:
                    self._dir = str(data.data)
            #Commands
            nodes = root.getElementsByTagName('commands')
            if not nodes == None and len(nodes) > 0:
                node = nodes[0]
                self._commandPrefix = node.attributes.get('prefix').firstChild.data
                self._commandSuffix = node.attributes.get('suffix').firstChild.data
                node = node.firstChild
                while not node == None:
                    if node.nodeName == 'command':
                        id = node.attributes.get('id') #.firstChild.data
                        run = node.attributes.get('run')
                        if not id == None and not run == None:
                            id = id.firstChild.data
                            run = run.firstChild.data
                            args = node.attributes.get('args')
                            if args == None:
                                args = 'False'
                            else:
                                args = args.firstChild.data
                            self._commands[id] = Command(id, run, args)
                    node = node.nextSibling
            return True
        except:
            return False

    def getPort(self):
        """Get server port"""
        return self._port

    def getDir(self):
        """Get server directory"""
        return self._dir

    def getPrefix(self):
        """Get command prefix"""
        return self._commandPrefix

    def getSuffix(self):
        """Get command suffix"""
        return self._commandSuffix

    def isCommand(self, command):
        """Get if command supported"""
        return self._commands.has_key(command)

    def getCommand(self, command):
        """Get command data"""
        data = None
        try:
            data = self._commands.get(command)
        except:
            data = None
        return data

class WebServer(BaseHTTPRequestHandler):
    """Little web server"""
    def __init__(self, config, *args):
        """Initialize web server"""
        self._config = config
        BaseHTTPRequestHandler.__init__(self, *args)

    def _runCommand(self, id, query):
        """Run command"""
        #Build command path
        command = self._config.getCommand(id)
        path = ''
        item = self._config.getPrefix()
        if not item == None: path += item
        path += command.getRun()
        if command.getAllowArgs() and query.has_key('arg'):
            for arg in query.get('arg'):
                path += ' ' + arg
        item = self._config.getSuffix()
        if not item == None: path += item
        #Run command
        commands.getoutput(path)

    def do_GET(self):
        """Handle get requests"""
        try:
            url = urlparse.urlparse(self.path)
            if url.path == '/command':
                query = urlparse.parse_qs(url.query)
                if not query.has_key('id'):
                    self.send_response(400, 'No command id')
                    return
                id = query.get('id')[0]
                if id == 'shutdown':
                    self.send_response(204)
                    print 'shutdown requested...'
                    self.server.server_close()
                    return
                if not self._config.isCommand(id):
                    self.send_response(405, id + ' is not supported')
                    return
                #Handle command
                try:
                    self._runCommand(id, query)
                    self.send_response(204)
                except:
                    self.send_response(424)
            elif url.path == '/' or url.path.endswith('.htm') or url.path.endswith('.html'):
                path = curdir + sep
                if not self._config.getDir() == None and len(self._config.getDir()) > 0:
                    path += self._config.getDir() + sep
                if url.path == '/':
                    path += 'index.html'
                else:
                    path += url.path[1:]
                f = open(path)
                #Response and headers
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                #Write content
                self.wfile.write(f.read())
                f.close()
            else:
                raise NotImplementedError()
        except:
            self.send_error(404)

    def do_POST(self):
        """Handle post requests"""
        pass

    def log_message(self, format, *args):
        """Ignore log messages, otherwise written to screen"""
        return

def webServerCreator(config):
    """Web server with configuration argument creator """
    return lambda *args: WebServer(config, *args)

#Main
def main():
    """
    Main entry point
    """
    #Load configuration
    config = Config()
    if not config.load():
        print 'Failed to load configuration, using default'
    #Start server
    try:
        handler = webServerCreator(config)
        server = HTTPServer(('', config.getPort()), handler)
        print 'Starting server...'
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Shutting down server...'
        server.socket.close()

if __name__ == '__main__':
    main()

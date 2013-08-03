"""
My Popcorn Hour Library - Python - ShuffleThis alpha
Given a local directory, extract videos and plays video in shuffled (random) order
Note: this must run form the popcorn hour device itself

Run example: 
- Copy this file to internal hard-drive/usb stick
- telent to the device
- 'cd' to script directory
- run 'python ShuffleThis.py [directory]'
  where the [directory] is your video directory on the device

Disclaimer:
The code is free to use and modify.
You may distribute freely but not commercially
I take no responsibility to any harm caused to your device
I'm not affiliated with Syabas, Cloud Media or any other Popcorn Hour related organization.
The code is in alpha mode and only been tested on a single device (A-400)

Author: Shachar Mossek
User:   sm2k
Mail:   shachar.mossek@gmail.com
Date:   03/08/2013 (03-AUG-2013)
"""

# Imports
import sys #prints
import os #directory
import httplib #TheDavidBox
import urllib  #TheDavidBox
from xml.dom.minidom import parseString #TheDavidBox
from random import shuffle #Shuffle

#Classes
#TODO move TheDavidBox api to file/package (+imports)
class TheDavidBox(object):
    """TheDavidBox (partial) API python implementation
       The class is not exception safe to keep it lightweight
    """
    #TODO allow free form query and extract (change some of the private to public)

    def __init__(self, host = '127.0.0.1', port = '8008'):
        """Initialize API"""
        self._conn = httplib.HTTPConnection(host + ':' + port)
       
    def close(self):
        """ Close API connection """
        if not self._conn == None:
            self._conn.close()
            self._conn = None

    def __api(self, paramString):
        """ Call API with arguments
        Args:
            paramString: Parameters string
            
        Returns: Tuple of Status, Reason and Data of response.
                 Returns None if connection is closed
        """
        if self._conn == None:
            return None
        self._conn.request("GET", '/' + paramString)
        response = self._conn.getresponse()
        data = None
        if response.status == 200:
            data = response.read()
        return (response.status, response.reason, data);

    def __extractReturnValue(self, data):
        """Extract return value

        Args:
            data: ml response data of API request

        Returns: Return value of None on error
        """
        if data == None: return
        root = parseString(data)
        #Extract return value
        retValue = root.getElementsByTagName('returnValue')
        if retValue == None or len(retValue) == 0: return
        retValue = retValue[0].firstChild
        return int(retValue.data)

    def __extractResponse(self, data):
        """Extract response node if return value is valid

        Args:
            data: Xml response data of API request

        Returns: Response nodes or None if error
        """
        if data == None: return
        root = parseString(data)
        #Extract return value
        retValue = root.getElementsByTagName('returnValue')
        if retValue == None or len(retValue) == 0: return
        retValue = retValue[0].firstChild
        retValue = int(retValue.data)
        if retValue <> 0: return
        #Extract response
        response = root.getElementsByTagName('response')
        if response == None or len(response) == 0: return
        response = response[0]
        return response.childNodes

    def __extractDictionary(self, data):
        """Extract API response into a dictionary
        Args:
            data: Xml response data of API request

        Returns: Response as dictionary or None if error
        """
        data = self.__extractResponse(data)
        if data == None: return
        result = {}
        for node in data:
            result[node.nodeName] = node.firstChild.data
        return result

    def __extractList(self, data):
        """Extract API response into values list
        Args:
            data: Xml response data of API request

        Returns: Response as list or None if error
        """
        data = self.__extractResponse(data)
        if data == None: return
        result = []
        for node in data:
            result.append(node.firstChild.data)
        return result

    def __call(self, module, function, args = []):
        """Call API

        Args:
            module: API module
            function: API module function
            Args: API module function arguments

        Returns: Same as __call(self, paramString)
        """
        params = []
        params.append(module);
        params.append('?arg0=' + urllib.quote(function));
        i = 0
        for arg in args:
            i += 1
            params.append('&arg' + str(i) + '=' + urllib.quote(arg)); #TODO support better concat
        return self.__api(''.join(params))

    def __system(self, function, args = []):
        """Call system module function

        Args:
           function: System function
           Args: System function (optional) arguments 

        Returns: Same as __call(self, paramString)
        """
        return self.__call('system', function, args)

    def __sendKey(self, key, data = None):
        """Send key to system

        Args:
           Key to send

        Returns: Same as __call(self, paramString)
        """
        args = []
        args.append(key)
        if not data == None: args.append(data)
        return self.__system('send_key', args)

    def __playback(self, function, args = []):
        """Call playback module function

        Args:
           function: Playback function
            Args: Playback function (optional) arguments 

        Returns: Same as __call(self, paramString)
        """
        return self.__call('playback', function, args)

    def getPlayInfo(self):
        """Get currently playing video info

        Returns: Currently played data (dictionary) or None if error or no file playing
                 Important Keys: 'title', 'fullPath', 'currentStatus', 'currentTime', 'totalTime'
        """
        data = self.__playback('get_current_vod_info')
        if not data == None:
            data = self.__extractDictionary(data[2])
        return data

    def play(self, path, title = None):
        """Play video file

        Args:
            path: Video file full path to play
            title: Optional video title

        Returns: True if video started playing or False otherwise
        """
        args = []
        #Create arguments
        #title
        if title == None: title = 'Title'
        args.append(title)
        #Path
        if not path.startswith('http://') and not path.startswith('file://'):
            path = 'file://' + path
        args.append(path)
        #Constant arguments
        args.append('show') #Show video
        args.append('0') #No skip
        args.append('0') #No prebuffer
        #HTTP cache
        cache = path.startswith('http://')
        if cache: args.append('enable') 
        else: args.append('disable')
        #Call API
        data = self.__playback('start_vod', args)
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def enqueue(self, path, title = None):
        """Play video file

        Args:
            path: Video file full path to play
            title: Optional video title

        Returns: True if video enqueued or False otherwise
        """
        args = []
        #Create arguments
        #title
        if title == None: title = 'Title'
        args.append(title)
        #Path
        if not path.startswith('http://') and not path.startswith('file://'):
            path = 'file://' + path
        args.append(path)
        #Constant arguments
        args.append('show') #Show video
        args.append('start_zero') #No skip
        #Call API
        data = self.__playback('insert_vod_queue', args)
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def resume(self):
        """Resume currently played file

        Returns: True if resumed otherwise False
        """
        data = self.__playback('resume_vod')
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def pause(self):
        """Pause currently played file

        Returns: True if pause otherwise False
        """
        data = self.__playback('pause_vod')
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def stop(self):
        """Stop playback

        Returns: True if stopped otherwise False
        """
        data = self.__playback('stop_vod')
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def next(self):
        """Play next item in queue

        Returns: True if playing next otherwise False
        """
        data = self.__sendKey('next')
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def previous(self):
        """Play previous item in queue

        Returns: True if playing next otherwise False
        """
        data = self.__sendKey('prev')
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def getKeys(self):
        """Get list of available system keys
        Key can be used by sendKey method

        Returns: List of available keys or None on error
        """
        data = self.__system('list_key')
        if not data == None:
            data = self.__extractList(data[2])
        return data

    def sendKey(self, key):
        """Send key to system

        Args:
            key: Key to send, see getKeys for available keys

        Returns: True if key snet otherwise False
        """
        data = self.__sendKey(key)
        if not data == None:
            data = self.__extractReturnValue(data[2])
        return data == 0

    def getSupportedVideoFormats(self):
        """Get supported video formats

        Returns: List of supported video formats or None on error
        """
        data = self.__playback('list_vod_supported_format')
        if not data == None:
            data = self.__extractList(data[2])
        return data

class fileRetriver:
    def __init__(self, supportedFormats = None):
        """Initialize file retriver"""
        if not supportedFormats == None:
            for i in range(len(supportedFormats)):
                format = supportedFormats[i].lower()
                if not format.startswith('.'): format = '.' + format
                supportedFormats[i] = format
        self._formats = supportedFormats

    def shuffleList(self, list):
        """Shuffle list in place"""
        shuffle(list)

    def getFiles(self, dir, recursive = True):
        """Get files recursively in directory.
        Supported formats are from constructor

        Args:
            dir: Directory to search

        Return: List of files in directory
        """
        list = []
        try:
            for root, subs, files in os.walk(dir):
                for file in files:
                    if self._formats == None:
                        list.append(os.path.join(root, file))
                    else:
                        lowerFile = file.lower()
                        for format in self._formats:
                            if lowerFile.endswith(format):
                                list.append(os.path.join(root, file))
                                break
        except:
            pass
        return list

#Main
def main():
    """
    Main entry point
    """
    #Extract directory
    if len(sys.argv) <> 2:
        print 'Usage: ShuffleThis [directory]'
        return
    #Get files #TODO support remote (smb/nfs) and playlists (m3u, pls)
    fr = fileRetriver([ 'avi', 'mkv', 'mp4', 'flv' ]) #TODO from configuration
    files = fr.getFiles(sys.argv[1])
    count = len(files)
    if count == 0:
        print 'No video files found'
        return
    fr.shuffleList(files)
    #Play
    api = TheDavidBox() #TODO port should be from configuration
    api.stop()
    api.play(files[0])
    for i in range(1, count):
        api.enqueue(files[i])

if __name__ == '__main__':
    main()

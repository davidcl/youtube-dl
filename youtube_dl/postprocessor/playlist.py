import os
import xml.etree.ElementTree as ET

from .common import PostProcessor

class PlaylistGeneratorPP(PostProcessor):
    def __init__(self, downloader=None, filename=None):
        PostProcessor.__init__(self, downloader)
        if filename is None:
            self._filename = 'playlist.m3u'
        else:
            self._filename = filename
        try:
            os.remove(self._filename)
        except:
            pass
        
        playlistformat = self._filename.rpartition(u'.')[2] # not os.path.splitext, since the latter does not work on unicode in all setups
        if playlistformat is None:
            self._playlistformat = 'm3u'
        else:
            self._playlistformat = playlistformat
            
        if self._playlistformat == 'm3u':
            pass
        elif self._playlistformat == 'pls':
            self._entries = []
        elif self._playlistformat == 'xspf':
            attrs = {'version': '1', 'xmlns': 'http://xspf.org/ns/0/'}
            self._etreeroot = ET.Element('playlist', attrs)
            ET.SubElement(self._etreeroot, 'trackList')
    
    def run(self, information):
        if self._playlistformat == 'm3u':
            self.generate_m3u(information)
        elif self._playlistformat == 'pls':
            self.generate_pls(information)
        elif self._playlistformat == 'xspf':
            self.generate_xspf(information)
        return True,information

    def generate_m3u(self, information):
        try:
            fd = open(self._filename, 'a')
            try:
                lines = []
                stat = os.fstat(fd.fileno())
                if stat.st_size == 0:
                    lines.append(u'#EXTM3U')
                descr = u'#EXTINF:{}, {} - {}'.format(information['duration'], information['uploader'], information['fulltitle'])
                lines.append(descr)
                lines.append(information['filepath'])
                lines = u'\n'.join(lines).encode('utf-8')
                fd.write(lines)
                fd.write(u'\n')
            finally:
                fd.close();
        except IOError:
            pass

    def generate_pls(self, information):
        self._entries.append(information)
        
        # Always write the whole file due to the footer
        lines = [u'[playlist]']
        for index, information in enumerate(self._entries):
            lines.append(u'File%d=%s' % (index+1, information['filepath']))
            lines.append(u'Title%d=%s - %s' % (index+1, information['uploader'], information['fulltitle']))
        lines.append(u'NumberOfEntries=%d' % len(self._entries))
        lines.append(u'Version=2')
        
        try:
            fd = open(self._filename, 'w')
            try:
                lines = u'\n'.join(lines).encode('utf-8')
                fd.write(lines)
                fd.write(u'\n')
            finally:
                fd.close();
        except IOError:
            pass

    def generate_xspf(self, information):
        track = ET.SubElement(self._etreeroot[0], 'track')
        
        ET.SubElement(track, 'location').text = information['filepath']
        ET.SubElement(track, 'identifier').text = information['id']
        ET.SubElement(track, 'title').text = information['fulltitle']
        ET.SubElement(track, 'creator').text = information['uploader']
        ET.SubElement(track, 'annotation').text = information['description']
        ET.SubElement(track, 'image').text = information['thumbnail']
        ET.SubElement(track, 'album').text = information['playlist']
        ET.SubElement(track, 'duration').text = str(information['duration'])
        
        # Always write the whole file to use etree serialization
        ET.ElementTree(self._etreeroot).write(self._filename, encoding='UTF-8')


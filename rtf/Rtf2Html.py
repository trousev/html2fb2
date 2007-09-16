"""
Convert RTF file to HTML
"""
import RtfParser
import sys

output_encoding = sys.getdefaultencoding()

class Destination:
    def __init__(self,foutput,parser):
        self.foutput = foutput
        self.name = 'Destination'
        self.parser = parser
        self.ansicpg = None

    def __repr__(self):
        return self.name
    
    def putChar(self,str):
        pass

    def doControl(self,token,arg):
        pass

    def pushState(self,list):
        list.append(self)

    def popState(self,list):
        list.pop()

    def close(self):
        pass

class RtfDestination(Destination):
    tags = {'b' : ['<b>','</b>'],
            'i' : ['<i>','</i>'],
            'strike' : ['<strike>','</strike>'],
            'ul' : ['<u>','</u>'],
            'fs' : ['<font>','</font>'],
            'f' : ['<font>','</font>'],
            'cf' : ['<font>','</font>'],
            'ql' : ["<div align='left'>",'</div>'],
            'qr' : ["<div align='right'>",'</div>'],
            'qj' : ["<div align='justify'>",'</div>'],
            'qc' : ["<div align='center'>",'</div>']}
    
    def __init__(self, foutput, parser, fontTable=None, colorTable=None):
        Destination.__init__(self, foutput, parser)
        self.name = 'Rtf'
        self.fontCounter = 0
        self.styles = ['']
        self.italic = False
        if fontTable:
            self.fontTable = fontTable
        else:
            self.fontTable = FontTableDestination(self.foutput,self.parser)
        if colorTable:
            self.colorTable = colorTable
        else:
            self.colorTable = ColorTableDestination(self.foutput,self.parser)
        self.reset()

    def reset(self):
        self.close()
        for token in self.tags.keys():
            setattr(self,token,False)
    
    def doControl(self,token,arg):
        if token in ['*','stylesheet','info']:
            #skip everything
            self.parser.setDest(Destination(self.foutput,self.parser))
        elif token == 'rtf':
            pass
        elif token in ['ansi','mac','pc','pca']:
            self.charcaterSet = token
            if token == 'pc':
                self.ansicpg = 'cp437'
            elif token == 'pca':
                self.ansicpg = 'cp850'
            elif token == 'ansi':
                self.ansicpg = 'latin_1'
        elif token == 'ansicpg':
            self.ansicpg = 'cp'+arg
        elif token == 'fonttbl':
            self.parser.setDest(self.fontTable)
        elif token == 'colortbl':
            self.parser.setDest(self.colorTable)
        elif token == 'par':
            self.foutput.write('<br>')
        elif token in  ('b','i','strike','ql','qr','qj','qc'):
            #bold italic strike
            open = self.tags[token][0]
            close = self.tags[token][1]
            self.treatIt(token,arg,open,close)
        elif token == 'ul':
            #underline
            self.foutput.write('<u>')
            self.styles.append('ul')
        elif token == 'ulnone':
            self.foutput.write('</u>')
            self.styles.pop()
        elif token == 'fs':
            #font size
            if self.styles and self.styles[-1] == 'fs':
                self.foutput.write("</font>")
                self.styles.pop()
            size = int(arg) / 2
            size = size - 9
            if size >= 0:
                size = '+' + str(size)
            else:
                size = str(size)
            self.foutput.write("<font size='%s'>\n" % (size,))
            self.styles.append('fs')
        elif token == 'f':
            #font
            font = self.fontTable.getFont(int(arg))
            #self.foutput.write("<span style='%s'>\n" % font.getStyle())
        elif token == 'cf':
            #foreground color
            color = self.colorTable.getColor(int(arg) - 1)
            if self.styles and self.styles[-1] == 'cf':
                self.foutput.write("</font>")
                self.styles.pop()
            self.foutput.write("\n<font color='%s'>" % str(color))
            self.styles.append('cf')
        elif token in  ['pard','plain']:
            self.reset()
        else:
            #skip unknown tag
            #print token, arg
            pass

    def treatIt(self,token,arg,open,close):
        toggle = getattr(self,token)
        if toggle:
            self.foutput.write('%s\n' % close)
            self.styles.pop()
        else:
            self.foutput.write('%s\n' % open)
            self.styles.append(token)
        setattr(self,token,not toggle)

    def putChar(self,str):
        if str == '\r':
            self.foutput.write('<br>')
        else:
            self.foutput.write(str.encode(output_encoding,'xmlcharrefreplace'))

    def close(self):
        #close all pending types
        foutput = self.foutput
        tags = self.tags
        styles = self.styles
        styles.reverse()
        for token in styles:
            if token in tags:
                foutput.write('%s\n' % tags[token][1])
        self.styles = ['']

    def pushState(self,list):
        newRtf = RtfDestination(self.foutput, self.parser, self.fontTable, self.colorTable)
        list.append(newRtf)

    def popState(self,list):
        self.close()
        list.pop()

class Font:
    def __init__(self):
        self.name = ''

    def getStyle(self):
        return ''

class FontTableDestination(Destination):
    def __init__(self,foutput,parser):
        Destination.__init__(self,foutput,parser)
        self.fontTable = []
        self.name = 'FontTable'

    def getFont(self,index):
        return self.fontTable[index]
    
    def putChar(self,str):
        font = self.fontTable[-1]
        font.name = font.name + str

    def doControl(self,token,arg):
        if token == 'f':
            self.fontTable.append(Font())
        elif  token in ['fnil','froman','fswiss','fmodern','fscript','fdecor','ftech','fbidi']:
            self.fontTable[-1].family = token
        elif token == 'fcharset':
            self.fontTable[-1].charset = arg
        else:
            font = self.fontTable[-1]
            setattr(font,token,arg)

class Color:
    def __init__(self):
        self.red = 0
        self.green = 0
        self.blue = 0

    def __str__(self):
        r = hex(self.red)[2:]
        if len(r) == 1:
            r = '0' + r 
        g = hex(self.green)[2:]
        if len(g) == 1:
            g = '0' + g
        b = hex(self.blue)[2:]
        if len(b) == 1:
            b = '0' + b
        return '#%s%s%s' % (r,g,b)

    def __repr__(self):
        return '%i %i %i' % (self.red,self.green,self.blue)

class ColorTableDestination(Destination):
    def __init__(self,foutput,parser):
        Destination.__init__(self,foutput,parser)
        self.name = 'ColorTable'
        self.colorTable = []

    def getColor(self,index):
        return self.colorTable[index]
    
    def putChar(self,str):
        if str == ';':
            self.colorTable.append(Color())

    def doControl(self,token,arg):
        if len(self.colorTable) == 0:
            self.colorTable.append(Color())
        color = self.colorTable[-1]
        setattr(color,token,int(arg))
                
class Rtf2Html(RtfParser.RtfParser):
    def __init__(self,foutput):
        RtfParser.RtfParser.__init__(self)
        self.foutput = foutput
        self.destinations = [RtfDestination(foutput,self)]
        self._ansicpg = 'latin_1'
        self.foutput.write('<head>\n    <meta http-equiv="Content-Type" content="text/html; charset=%s">\n</head>\n' % output_encoding)
        self.foutput.write('<html><body>\n')
        
        
    def setAnsiCpg(self,codePage):
        self._ansicpg = codePage or self._ansicpg

    def getAnsiCpg(self):
        try:
            return "cp%d" % int(self._ansicpg)
        except:
            return self._ansicpg

    ansicpg = property(getAnsiCpg,setAnsiCpg,doc='the code page used')

    def getChar(self,code):
        return unicode(chr(code),self.ansicpg)

    def getNonBreakingSpace(self):
        return "&nbsp;"

    def append(self,arg):
        self.destinations.append(arg)

    def pop(self):
        return self.destinations.pop()

    def setDest(self,dest):
        self.destinations[-1] = dest

    def pushState(self):
        dest = self.destinations[-1]
        dest.pushState(self)
        self.ansicpg = dest.ansicpg

    def popState(self):
        dest = self.destinations[-1]
        dest.popState(self)

    def putChar(self,ch):
        dest = self.destinations[-1]
        dest.putChar(ch)

    def doControl(self,token,arg):
        dest = self.destinations[-1]
        dest.doControl(token,arg)

    def close(self):
        for dest in self.destinations:
            dest.close()
        self.foutput.write('</body></html>\n')

def getHtml(rtf):
    """ get the Html from a string that contain Rtf """
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO
    s = StringIO.StringIO()
    parser = Rtf2Html(s)
    parser.feed(rtf)
    parser.close()
    return s.getvalue()

if __name__ == '__main__':
    import CmdLine
    CmdLine.main(Rtf2Html)

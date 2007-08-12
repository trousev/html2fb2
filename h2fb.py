#!/usr/bin/python2.3
# -*- coding: koi8-r -*- 
from sgmllib import SGMLParser
import sys
from types import DictType, TupleType, ListType
import re, tempfile, os, base64, time

version='0.1.0'

# Module wide values
_SENTENCE_FIN  = u'\'".!?:\xBB\u2026'   # \xBB == >>, \u2026 == ...
_HEAD_CHARS    = u'0123456789VXILM*@'
_DIAL_START    = u'-\u2013\u2014'       # MINUS, N DASH, M DASH
_DIAL_START2   = u')-\u2013\u2014 .;'
_CH_REPL_AMP   = u'\x00'
_CH_REPL_LT    = u'\x01'
_CH_REPL_GT    = u'\x02'
_CH_LEFT_Q     = u'\\1\xab'
_CH_RIGHT_Q    = u'\xbb\\1'
_CH_FLOW       = u' '
_CH_DOTS       = u'\u2026'
_CH_TIRE       = u'\u2013'
_RE_LQUOTES    = re.compile('([ (;-])"')
_RE_RQUOTES    = re.compile('"([ <&.,;?!)-])')
_RE_LQUOTES2   = re.compile('^((?:<[^>]*>)*)"',re.M)
_RE_RQUOTES2   = re.compile('"((?:<[^>]*>)*)$',re.M)
_RE_TAG        = re.compile('<[^>]*>')
_RE_ROMAN      = re.compile('^m?m?m?(c[md]|d?c{0,3})(x[lc]|l?x{0,3})(i[xv]|v?i{0,3})$', re.I)
_RE_EL         = re.compile('<empty-line/>\s*(</section>)')
# Flags
_TAG_SKIP     = 0x0001
_TAG_STRONG   = 0x0004
_TAG_EM       = 0x0008
_TAG_NOTSKIP  = 0x0010
_TAG_ENDP     = 0x0020
_TAG_STARTP   = 0x0002
_TAG_PRE      = 0x0040 
_TAG_HEADER   = 0x0080
_TAG_INP      = 0x0100
_TAG_ID       = 0x0200

_TAGS={
    'a'           : _TAG_INP,
    'abbr'        : 0,
    'acronym'     : 0,
    'address'     : 0,
    'align'       : 0,
    'applet'      : 0,
    'area'        : 0,
    'b'           : _TAG_STRONG,
    'base'        : 0,
    'basefont'    : 0,
    'bdo'         : 0,
    'bgsound'     : 0,
    'big'         : 0,
    'blink'       : 0,
    'blockquote'  : 0,
    'body'        : 0,
    'br'          : _TAG_STARTP|_TAG_ENDP,
    'button'      : 0,
    'caption'     : 0,
    'center'      : 0,
    'cite'        : _TAG_EM|_TAG_ID,
    'code'        : 0,
    'col'         : 0,
    'colgroup'    : 0,
    'comment'     : 0,
    'dd'          : 0,
    'del'         : 0,
    'dfn'         : 0,
    'dir'         : 0,
    'div'         : 0,
    'dl'          : 0,
    'dt'          : 0,
    'em'          : _TAG_EM,
    'embed'       : 0,
    'fieldset'    : 0,
    'font'        : 0,
    'form'        : _TAG_SKIP,
    'frame'       : 0,
    'frameset'    : 0,
    'h1'          : _TAG_HEADER,
    'h2'          : _TAG_HEADER,
    'h3'          : _TAG_HEADER,
    'h4'          : _TAG_HEADER,
    'h5'          : _TAG_HEADER,
    'h6'          : _TAG_HEADER,
    'head'        : _TAG_SKIP,
    'hr'          : _TAG_ENDP,
    'html'        : 0,
    'i'           : _TAG_EM,
    'iframe'      : 0,
    'ilayer'      : 0,
    'img'         : _TAG_ENDP,
    'input'       : 0,
    'ins'         : 0,
    'isindex'     : 0,
    'kbd'         : 0,
    'keygen'      : 0,
    'label'       : 0,
    'layer'       : 0,
    'legend'      : 0,
    'li'          : 0,
    'link'        : 0,
    'listing'     : _TAG_PRE,
    'map'         : 0,
    'marquee'     : 0,
    'menu'        : 0,
    'meta'        : 0,
    'multicol'    : 0,
    'nextid'      : 0,
    'nobr'        : 0,
    'noembed'     : _TAG_SKIP,
    'noframes'    : _TAG_SKIP,
    'nolayer'     : 0,
    'nosave'      : 0,
    'noscript'    : _TAG_SKIP,
    'object'      : 0,
    'ol'          : 0,
    'optgroup'    : 0,
    'option'      : 0,
    'p'           : _TAG_STARTP|_TAG_ENDP,
    'param'       : 0,
    'plaintext'   : _TAG_PRE,
    'pre'         : 0,
    'q'           : 0,
    'rb'          : 0,
    'rbc'         : 0,
    'rp'          : 0,
    'rt'          : 0,
    'rtc'         : 0,
    'ruby'        : 0,
    's'           : 0,
    'samp'        : 0,
    'script'      : _TAG_SKIP,
    'select'      : 0,
    'server'      : 0,
    'servlet'     : 0,
    'small'       : 0,
    'spacer'      : 0,
    'span'        : 0,
    'strike'      : 0,
    'strong'      : _TAG_STRONG|_TAG_INP,
    'style'       : _TAG_SKIP,
    'sub'         : 0,
    'sup'         : 0,
    'table'       : 0,
    'tbody'       : 0,
    'td'          : 0,
    'textarea'    : 0,
    'tfoot'       : 0,
    'th'          : 0,
    'thead'       : 0,
    'title'       : _TAG_NOTSKIP,
    'tr'          : _TAG_STARTP,
    'tt'          : 0,
    'u'           : 0,
    'ul'          : 0,
    'var'         : _TAG_EM,
    'wbr'         : 0,
    'xmp'         : _TAG_PRE,
    #fb2 tags. ignored while parsing
    'emphasis'    : _TAG_INP,
    'section'     : _TAG_ID,
    'poem'        : _TAG_ID,
    'epigraph'    : _TAG_ID,
    }

try:
    import wx
    if wx.GetApp() is None:
        _app = wx.PySimpleApp()
    _IMG_LIB='wxPython'
    def convert2png(filename):
        retv=''
        img = wx.Bitmap(filename, wx.BITMAP_TYPE_ANY)
        if img.Ok():
            img = wx.ImageFromBitmap(img)
            of= tempfile.mktemp()
            if img.SaveFile(of,  wx.BITMAP_TYPE_PNG):
                retv=open(of).read()
            os.unlink(of)
        return retv
except ImportError:
    try:    
        from PIL import Image
        _IMG_LIB='PIL'
        def convert2png(filename):
            retv = ''
            try:
                of = tempfile.mktemp()
                Image.open(filename).save(of,'PNG')
                retv=open(of).read()
                os.unlink(of)
            except:
                pass
            return retv
    except ImportError:
        _IMG_LIB='None'
        convert2png = None


class MyHTMLParser(SGMLParser):
    """HTML parser.
    Originated from standard htmllib
    """

    from htmlentitydefs import name2codepoint
    entitydefs={}
    for (name, codepoint) in name2codepoint.iteritems():
        entitydefs[name] = unichr(codepoint)
    del name, codepoint, name2codepoint
    entitydefs['nbsp']=u' '
    def reset(self):
        SGMLParser.reset(self)
        self.nofill = 1                 # PRE active or not
        self.oldnofill = 0              # for saving nofill flag (for section title, for example)
        self.out = []                   # Result
        self.data = ''                  # Currently parsed text data
        self.skip = ''                  # Skip all all between tags. End tag here
        self.nstack = [[],[]]           # Stack for nesting tags control. first el. is tags stack, second - correspond. attrs
        self.save = ''                  # Storage for data between tags pair
        self.saving = False             # Saving in progress flag
        self.ishtml = False             # data type
        self.asline = (0,0,0)           # [counted lines, > 80, < 80]
        self.ids = {}                   # links ids
        self.nextid=1                   # next note id
        self.notes=[]                   # notes
        self.descr={}                   # description
        self.bins=[]                    # images (binary objects)
        self.informer=None              # informer (for out messages)
        
    # --- Main processing method
    def process(self, params):
        ''' Process all data '''
        self.params=params
        if params.has_key('informer'):
            self.informer=params['informer']
        secs = time.time()
        self.msg('HTML to FictionBook converter, ver. %s\n' % version)
        self.msg("Reading data...\n")
        data=params['data']
        self.href_re = re.compile(".*?%s#(.*)" % unicode(params['file-name'], params['sys-encoding']))
        try:
            self.header_re = params['header-re'].strip() and re.compile(params['header-re'])
        except:
            self.header_re = None
        if not data:
            try:
                f = open(params['file-name'])
            except:
                self.msg("Get data from stdin",2)
                f = sys.stdin
        data=f.read()
        f.close()
        if not data:
            return ''
        self.msg('Preprocessing...\n')
        data = self.pre_process(data)
        self.msg('Parsing...\n')
        self.feed(data+'</p>')
        self.close()
        self.msg('Formatting...\n')
        self.detect_epigraphs()
        self.detect_verses()
        self.detect_paragraphs()
        self.msg('Postprocessing...\n')
        self.post_process()
        self.msg('Building result document...\n')
        self.out= '<?xml version="1.0" encoding="%s"?>\n' \
                   '<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:xlink="http://www.w3.org/1999/xlink">\n' % \
                   self.params['encoding-to'] + \
                   (self.make_description() + \
                    '<body>%s</body>' % self.out + \
                    self.make_notes()).encode(self.params['encoding-to'],'xmlcharrefreplace') + \
                    self.make_bins() + '</FictionBook>'
        self.msg("Total process time is %.2f secs\n" % (time.time() - secs))
        return self.out
    # --- Tag handling, need for parsing
    def unknown_starttag(self, tag, attrs):
        '''
        Handle unknown start ttag
        '''
        if _TAGS.has_key(tag) or self.skip:
            self.handle_starttag(tag, None, attrs)
        else:
            self.handle_data(self.tag_repr(tag, attrs))

    def unknown_endtag(self, tag):
        '''
        Handle unknown end ttag
        '''
        if _TAGS.has_key(tag) or self.skip:
            self.handle_endtag(tag, None)
        else:
            self.handle_data("</%s>" % tag)

    def handle_data(self, data):
        '''
        Handle data stream
        '''
        data = data.replace('&',_CH_REPL_AMP).replace('<',_CH_REPL_LT).replace('>',_CH_REPL_GT)
        if self.saving:
            self.save += data
        else:
            self.data += data
 
    def handle_starttag(self, tag, method, attrs):
        '''
        Handle all start tags
        '''
        try:
            flag = _TAGS[tag]
        except:
            flag = 0
        if self.skip and not flag & _TAG_NOTSKIP:
            return
        if flag & _TAG_SKIP:
            self.skip = tag
        if not method:
            if flag & _TAG_EM:
                method = self.start_em
            if flag & _TAG_STRONG:
                method = self.start_strong
            if flag & _TAG_PRE:
                method = self.start_pre
            if flag & _TAG_STARTP:
                method = self.do_p
            if flag & _TAG_HEADER:
                method = self.start_h1
        if method:
            method(attrs)
        # if detected tag, but text still non-html - set text as html
        if not self.ishtml and \
           not flag & (_TAG_EM|_TAG_STRONG|_TAG_INP) and \
           tag != 'h6':
            self.end_paragraph()
            self.ishtml = True
            self.nofill = 0

    def handle_endtag(self, tag, method):
        '''
        Handle all end tags
        '''
        try:
            flag = _TAGS[tag]
        except:
            flag = 0
        if self.skip and self.skip == tag:
            self.skip=''
            self.data=''
            return
        if not method:
            if flag & _TAG_EM:
                method=self.end_em
            if flag & _TAG_STRONG:
                method=self.end_strong
            if flag & _TAG_PRE:
                method=self.end_pre
            if flag & _TAG_ENDP:
                method = self.end_paragraph
            if flag & _TAG_HEADER:
                method = self.end_h1
        if method:
            method()

    def start_title(self, attrs):
        ''' Save document title - start'''
        self.start_saving()

    def end_title(self):
        ''' End saving document title '''
        self.descr['title'] = ' '.join(self.stop_saving().split()).strip()
        
    def do_meta(self, attrs):
        '''
        Handle meta tags - try get document author
        '''
        name=''
        content=''
        for opt, val in attrs:
            if opt=='name':
                name=val
            elif opt=='content':
                content=val.strip()
        if name=='author' and content:
            self.descr['author']=content

    def do_p(self, attrs):
        '''Handle tag P'''
        self.end_paragraph()
        self.mark_start_tag('p')
        
    def start_pre(self, attrs):
        ''' Handle tag PRE '''
        self.nofill = self.nofill + 1
        self.do_p(None)
        
    def end_pre(self):
        ''' Handle tag /PRE '''
        self.end_paragraph()
        self.nofill = max(0, self.nofill - 1)
        
    def start_em(self, attrs):
        ''' Handle tag EM '''
        self.mark_start_tag('emphasis')
        
    def end_em(self):
        ''' Handle tag /EM '''
        self.mark_end_tag('emphasis')
        
    def start_strong(self, attrs):
        ''' Handle tag STRONG '''
        self.mark_start_tag('strong')
        
    def end_strong(self):
        ''' Handle tag /STRONG '''
        self.mark_end_tag('strong')
        
    def start_a(self, attrs):
        ''' Handle tag A '''
        for attrname, value in attrs:
            value = value.strip()
            if attrname == 'href':
                res = self.href_re.match(value)
                if res:
                    value=self.make_id(res.group(1))
                    try:
                        self.ids[value][1]+=1
                    except:
                        self.ids[value]=[0,1]
                    value="#"+value
                if self.params['skip-ext-links'] and not res:
                    return
                self.mark_start_tag('a', [('xlink:href',value)])
            if attrname == 'name':
                value = self.make_id(value)
                self.data+="<id %s>" % value
                try:
                    self.ids[value][0]+=1
                except:
                    self.ids[value]=[1,0]
    def end_a(self):
        ''' Handle tag /A '''
        self.mark_end_tag('a')

    def start_h1(self, attrs):
        ''' Handle tag H1-H6 '''
        self.end_paragraph()
        self.out.extend(['</section>','<section>','<title>'])
        self.mark_start_tag('p')
        self.oldnofill, self.nofill = self.nofill, 0
        
    def end_h1(self):
        ''' Handle tag /H1-/H6 '''
        self.end_paragraph()
        self.out.append('</title>')
        self.nofill = self.oldnofill
        self.mark_start_tag('p')

    def do_img(self, attrs):
        ''' Handle images '''
        if not self.params['convert-images']:
            return
        src = None
        for attrname, value in attrs:
            if attrname == 'src':
                src = value
        data = self.convert_image(src)#src.encode(self.params['sys-encoding']))
        if data:
            self.end_paragraph()
            src=os.path.basename(src)
            self.out.append(self.tag_repr('image', [('xlink:href','#'+src)], True))
            self.bins.append((src, data))

    def report_unbalanced(self, tag):
        ''' Handle unbalansed close tags'''
        self.handle_data('</%s>\n' % tag)
        
    def unknown_charref(self, ref):
        ''' Handle unknown char refs '''
        # FIX: Don't know, how to handle it
        self.msg('Unknown char ref %s\n' % ref, 1)
        
    def unknown_entityref(self, ref):
        ''' Handle unknown entity refs '''
        # FIX: Don't know, how to handle it
        self.msg('Unknown entity ref %s\n' % ref, 1)

    # --- Methods for support parsing
    def start_saving(self):
        ''' Not out data to out but save it '''
        self.saving = True
        self.save = ''

    def stop_saving(self):
        ''' Stop data saving '''
        self.saving = False
        return self.save
    
    def end_paragraph(self):
        '''
        Finalise paragraph
        '''
        if not self.data.strip():
            try:
                p = self.nstack[0].index('p')
                if self.out[-1] == '<p>' or not self.out[-1]:
                    if self.params['skip-empty-lines']:
                        self.out.pop()
                    else:
                        self.out[-1] = "<empty-line/>"
                    self.nstack[0]=self.nstack[0][:p]
                    self.nstack[1]=self.nstack[1][:p]
                else:
                    self.mark_end_tag('p')
            except ValueError:
                pass

        else:
            if 'p' not in self.nstack[0]:
                self.nstack[0][0:0]='p'
                self.nstack[1][0:0]=[None]
                self.out.append('<p>')
            self.mark_end_tag('p')
            
    def mark_start_tag(self, tag, attrs=None):
        ''' Remember open tag and put it to output '''
        try:
            flag = _TAGS[tag]
        except:
            flag = 0
        if tag in self.nstack[0]:
            self.mark_end_tag(tag)
        self.nstack[0].append(tag)
        self.nstack[1].append(attrs)
        if flag & _TAG_INP:
            self.data += self.tag_repr(tag, attrs)
        else:
            self.out.append(self.tag_repr(tag, attrs))
            
    def mark_end_tag(self, tag):
        '''
        Close corresponding tags. If tag is not last tag was outed,
        close all previously opened tags.
        I.e. <strong><em>text</strong> -> <strong><em>text</em></strong>
        '''
        if tag not in self.nstack[0]:
            return
            
        while self.nstack[0]:
            v = self.nstack[0].pop()
            a = self.nstack[1].pop()
            try:
                flag = _TAGS[v]
            except:
                flag = 0
            if flag & _TAG_INP:
                et=self.tag_repr(v,a)
                if self.data.rstrip().endswith(et):
                    self.data=self.data.rstrip()[:-len(et)]
                    if v=='a':
                        try:
                            self.ids[a[0][1]][1]-=1
                        except:
                            pass
                else:
                    self.data += "</%s>" % v
            else:
                self.process_data()
                if self.out[-1]=="<%s>" % v:
                    self.msg("!!!!\n")
                    self.out.pop()
                else:
                    self.out.append("</%s>" % v)
            if tag == v:
                break

    def process_data(self):
        '''
        Handle accomulated data when close paragraph.
        '''
        if not self.data.strip():
            return
        if not self.nofill:
            self.data=_CH_FLOW+self.data.strip()
            self.out.append(self.data)
        else:
            self.data = self.process_pre(self.data)
            self.data = self.detect_headers(self.data)
            try:
                if self.data[0]=='</p>' and self.out[-1]=='<p>':
                    self.out.pop()
                    self.data = self.data[1:]
                    msg("WoW! I must be impossible!!!")
            except IndexError:
                pass
            self.out.extend(self.data)
        self.data = ''
        
    # --- Parsed data processing methods
    def pre_process(self, data):
        '''
        Processing data before parsing.
        Return data converted to unicode. If conversion is impossible, return None.
        If encoding not set, try detect encoding with module recoding from pETR project.
        '''
        encoding = self.params['encoding-from']
        if not encoding:
            try:
                data=unicode(data,'utf8')
                encoding = None         # No encoding more needed
            except UnicodeError:
                try:
                    import recoding     # try import local version recoding
                    encoding = recoding.GetRecoder().detect(data[:2000])
                except ImportError:
                    try:
                        import petr.recoding as recoding # try import pETR's modyle
                        encoding = recoding.GetRecoder().detect(data[:2000])
                    except ImportError:
                        encoding = None
                if not encoding:
                    encoding = "Windows-1251"
                    self.msg("Recoding module not found. Use default encoding")
        try:
            if encoding:
                data=unicode(data,encoding)
                self.params['encoding-from'] = encoding
        except:
            data = None
            self.msg("Encoding %s is not valid\n" % encoding)
        if data:
            data=data.replace(u'\x0e',u'<h6>').replace(u'\x0f',u'</h6>')
            for i in u'\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x10\x11'\
                    '\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f':
                data = data.replace(i,u' ')

        return data

    def post_process(self):
        '''
        Last processing method
        '''
        id = ''
        for i in range(len(self.out)):
            if not self.out[i]:
                pass                    # skip empty lines (can apper below, where ...out[i+1]='')
            elif self.out[i][0] != '<':
                id, p = self.process_paragraph(self.out[i], id)
                if p:
                    if id:
                        self.out[i-1] = '<%s id="%s">' % (self.out[i-1][1:-1],id)
                        id = ''
                    self.out[i] = p
                else:
                    self.out[i-1]=self.out[i]=self.out[i+1]='' # remove empty paragraph
            elif id:
                try:
                    if _TAGS[self.out[i][1:-1]] & _TAG_ID:
                        self.out[i] = '<%s id="%s">' % (self.out[i][1:-1],id)
                        id = ''
                except KeyError:
                    pass
        self.out='\n'.join(self.out). \
             replace(_CH_REPL_AMP, '&amp;'). \
             replace(_CH_REPL_LT,'&lt;').    \
             replace(_CH_REPL_GT,'&gt;').    \
             replace('...',_CH_DOTS).        \
             strip()
        if self.params['convert-hyphen']:
            self.out=self.out.replace("- ",_CH_TIRE+" ").replace(" -"," "+_CH_TIRE)

        # delete links withself.out anchors
        for i in [x for x in self.ids.keys() if not self.ids[x][0] and self.ids[x][1]>=0]:
            self.out=re.sub("%s(.*?)%s" % (self.tag_repr('a',[('xlink:href','#'+i)]),'</a>') ,r'\1',self.out)
        sect=self.out.find('<section')
        if 0 < sect < len(self.out)/3 and self.params['detect-annot']:
            self.descr['annot'] = ' '.join(self.out[:sect].rstrip().rstrip('</section>').split())
            self.out=self.out[sect:]
        else:
            if self.out.startswith('</section>'):
                self.out=self.out[len('</section>'):]
            else:
                self.out='<section>'+self.out
        self.out+='</section>'
        self.out=_RE_EL.sub(r'\1',self.out)

    def detect_headers(self, data):
        '''
        Find headers in plain text.
        '''
        if not self.params['detect-headers']:
            return [data]
        res = []
        pstart = i = 0
        header = ['</p>',
                  '</section>',
                  '<section>',
                  '<title>',
                  '<p>',
                  '',                   # place for title (5)
                  '</p>',
                  '</title>',
                  '<p>'
                  ]
        while i < len(data)-1:
            empty0 = not data[i]
            try:
                empty1 = not data[i+1]
                empty2 = not data[i+2]
                empty3 = not data[i+3]
            except IndexError:
                empty1 = empty2 = empty3 = False
            if empty0 and empty1 and not empty2 and empty3:
                res.append(data[pstart:i])
                header[5]=_CH_FLOW + data[i+1].strip()
                res.extend(header)
                i+=2
                pstart = i+2
            else:
                istitle = (
                    empty0 and 
                    not empty1 and 
                    empty2 and 
                    (
                        empty3 or
                        data[i+1].startswith(' '*8) or
                        data[i+1].isupper() or
                        (
                            data[i+1].lstrip()[0] not in _DIAL_START and
                            data[i+1][-1] not in _SENTENCE_FIN
                        ) or
                        data[i+1].lstrip()[0] in _HEAD_CHARS  or
                        self.is_roman_number(data[i+1])

                    )
                )
                istitle = istitle or \
                          not empty1 and \
                          self.header_re and \
                          self.header_re.match(data[i+1])
                if istitle:
                    res.append(data[pstart:i])
                    header[5]=_CH_FLOW + data[i+1].strip()
                    res.extend(header)
                    i+=1
                    while i < len(data)-1 and not data[i+1]:
                        i+=1
                    pstart = i+1
            i+=1
        if pstart < len(data):
            res.append(data[pstart:])
        return res
    
    def detect_epigraphs(self):
        '''
        Detect epigraphs (in plain text)
        '''
        if not self.params['detect-epigraphs']:
            return
        sect_found = 0
        i = 0
        while i < len(self.out):
            if type(self.out[i]) != ListType:
                if self.out[i] == '<section>':
                    sect_found = 1
                elif self.out[i] == '<title>':
                    sect_found = sect_found and 2 or 0
                elif self.out[i] == '</title>':
                    sect_found = sect_found and 1 or 0
                elif self.out[i][0] != '<':
                    sect_found = sect_found!=1 and 2 or 0
            else:
                if sect_found == 1:
                    res = []
                    raw = self.out[i]
                    lraw = len(raw)
                    j=0
                    eplines = 0
                    epfound = 0
                    while j < len(raw):
                        while j < lraw and not raw[j]: j+=1 #  skip empty lines
                        eep = -1
                        # search empty line
                        for k in range(j,j+60):
                            if k >= lraw or not raw[k]:
                                eep = k
                                break
                        if eep == j:
                            break
                        if eep >= 0:
                            eplines = 0
                            for k in range(j,eep):
                                rawk = raw[k].lstrip()
                                if ' '*10 in raw[k] or len(rawk) < 60:
                                    eplines +=1
                                if len(rawk) > 60:
                                    eplines -= 5
                                if rawk and (
                                    rawk[0] in _DIAL_START or
                                    rawk[0].isdigit() and
                                    len(rawk)>2 and
                                    rawk[1] in _DIAL_START2
                                    ):
                                    eplines -= 1
                            if (float(eplines)/(eep-j)>0.8):
                                epfound += 1
                                author = eep-j > 1
                                res.extend(['<epigraph>','<p>',raw[j:eep-author]])
                                if author and self.clean_str(raw[eep-1]).lstrip()[0].isupper():
                                    res.extend(['</p>','<text-author>',_CH_FLOW + self.clean_str(raw[eep-1]).lstrip(),'</text-author>'])
                                else:
                                    if author: res[-1].append(raw[eep-1])
                                    res.append('</p>')
                                res.append('</epigraph>')
                                j=eep
                            else:
                                eep = -1
                        if eep < 0:
                            break
                        j+=1
                    if epfound:
                        istart=i
                        iend=i+1
                        if i and self.out[i-1] == '<p>':
                            istart-=1
                        if j < len(raw)-1:
                            res.extend(['<p>',raw[j:]])
                        elif i < len(self.out)-1 and self.out[i+1] == '</p>':
                            iend+=1
                        self.out[istart:iend] = res
                        i = istart + len(res)-1
                sect_found = 0
            i += 1

    def detect_verses(self):
        '''
        Detect verses in plain text
        '''
        if not self.params['detect-verses']:
            return
        i=0
        while i < len(self.out):
            if type(self.out[i]) == ListType:
                res=[]
                raw=[self.clean_str(x).rstrip() for x in self.out[i]]
                lraw=len(raw)
                pfound = jstart = j = 0
                while j < lraw-3:
                    if raw[j] and len(raw[j]) < 60 and \
                       raw[j+1] and len(raw[j+1]) < 80 and \
                       raw[j+2] and len(raw[j+2]) < 80 and \
                       raw[j+3] and len(raw[j+3]) < 80:
                        fl = len(raw[j])
                        k = j
                        while k < lraw:
                            if raw[k].strip() and (
                                abs(len(raw[k])-fl) > 15 or \
                                raw[k].lstrip()[0] in _DIAL_START
                                ):
                                break
                            k += 1
                        if k - j > 3:
                            pfound += 1
                            if jstart:
                                res.append('<p>')
                            if jstart != j:
                                res.extend([self.out[i][jstart:j],'</p>'])
                            res.extend(['<poem>','<stanza>'])
                            for l in range(j,k):
                                if raw[l]:
                                    res.extend(['<v>',raw[l].lstrip(),'</v>'])
                                elif l < k-1 and res[-1] != '<stanza>':
                                    res.extend(['</stanza>','<stanza>'])
                            res.extend(['</stanza>','</poem>'])
                            j=k-1
                            jstart = k
                    j+=1
                if pfound:
                    if jstart < lraw-1:
                        res.extend(['<p>',self.out[i][jstart:]])
                    istart = i
                    iend = i+1
                    try:
                        if res[0] == '<poem>' and self.out[i-1] == '<p>':
                            istart -= 1
                    except:
                        pass
                    try:
                        if res[-1] == '</poem>' and self.out[i+1] == '</p>': 
                            iend += 1
                    except:
                        pass
                    self.out[istart:iend]=res
            i+=1
            
    def detect_paragraphs(self):
        '''
        Detect paragraphs in plain text
        '''
        i=0
        while i < len(self.out):
            if type(self.out[i]) == ListType:
                res = []
                raw = self.out[i]
                j = 0
                pfound = 0
                while j < len(raw) and not raw[j]: j+=1
                jstart = j
                while j < len(raw):
                    if not raw[j]:
                        try:
                            while not raw[j]: j+=1
                        except IndexError:
                            break
                        if not self.params['skip-empty-lines']:
                            res.append('<empty-line/>')
                        jstart=j
                        continue
                    elif self.asline or \
                             not self.params['detect-paragraphs'] or \
                             j >= len(raw)-1 or \
                             not raw[j+1].lstrip() or \
                             (raw[j+1].lstrip()[0] in _DIAL_START or \
                              raw[j+1].startswith('  ')
                              ) and raw[j][-1] in _SENTENCE_FIN:
                        pfound += 1
                        res.extend(['<p>',_CH_FLOW + '\n'.join(raw[jstart:j+1]),'</p>'])
                        jstart = j+1
                    j+=1
                if pfound > 0:
                    self.out[i:i+1]=res[1:-1]
                    i+=len(res)-2
                else:
                    self.out[i]='\n'.join(raw).lstrip()
            i+=1
            
    def detect_italic(self, text, arg):
        signs='_.,!?:'
        istart=-1
        res=''
        while True:
            istart = text.find('_')
            if istart >= 0:
                iend = sys.maxint
                for i in signs:
                    try:
                        iend=min(iend, text.index(i, istart+1))
                    except:
                        pass
                if iend == sys.maxint:
                    iend=0
                text=text[:istart]+ \
                      '<emphasis>'+ \
                      text[istart+1:iend or None]+ \
                      '</emphasis>'+ \
                      (iend and text[iend+(text[iend]=='_'):] or '')
            else:
                break
        return text

    def detect_notes(self, text, arg):
        while True:
            snote = text.find(arg[0])
            enote = text.find(arg[1])
            if snote <0 or enote <= snote:
                break
            self.notes.append((self.nextid, text[snote+1:enote]))
            text=(text[:snote] +
                  '<a xlink:href="FictionBookId%s" type="note">' % self.nextid +
                  "note %s" % self.nextid+"</a>" +
                  text[enote+1:]
                  )
            self.nextid += 1
        return text

    def process_pre(self, data):
        '''
        Process preformatted data (data between <pre> and </pre> tag or plain text file)
        Determine text format.
        '''
        data = [x.rstrip() for x in data.splitlines()]
        if type(self.asline) == TupleType:
            count,G80,L80 = self.asline
            for i in data:
                if len(i) > 80:
                    G80+=1
                else:
                    L80+=1
                count+=1
                if count > 2000:
                    self.asline = G80 > L80
                    break
            if type(self.asline) == TupleType:
                self.asline=(count, G80, L80)
        return data
    
    def process_paragraph(self, paragraph, id):
        '''
        Process paragraph. Find id, normalize quotes.
        '''
        paragraph=paragraph.strip()
        startp = paragraph.find('<id ')
        while startp >= 0:
            endp=paragraph.index('>',startp+4) # if '>' will not be found exception  will raised, because use index
            found_id = paragraph[startp+4:endp]
            if not id:
                id = found_id
            else:
                self.ids[found_id][0]=0
            paragraph=paragraph[:startp]+paragraph[endp+1:]
            startp = paragraph.find('<id ')
        # id here is paragraph id, if found
        if not paragraph:
            return [id,'']
        # strip leading spaces if paragraph starth with tag
        if paragraph[0]=='<':
            endp=paragraph.index('>')
            paragraph=paragraph[:endp+1]+paragraph[endp+1:].lstrip()
        if self.params['convert-quotes']:
            # process quotes
            paragraph = _RE_LQUOTES.sub(_CH_LEFT_Q, paragraph)
            paragraph = _RE_RQUOTES.sub(_CH_RIGHT_Q, paragraph)
            paragraph = _RE_LQUOTES2.sub(_CH_LEFT_Q, paragraph)
            paragraph = _RE_RQUOTES2.sub(_CH_RIGHT_Q, paragraph)
        if self.params['detect-notes']:
            paragraph = self.process_nontags(paragraph, self.detect_notes, "[]")
            paragraph = self.process_nontags(paragraph, self.detect_notes, "{}")
        if self.params['detect-italic']:
            paragraph = self.process_nontags(paragraph, self.detect_italic, None)
        paragraph = ' '.join(paragraph.split()) # Remove extra whitespaces
        
        return [id, paragraph]

    def process_nontags(self, text, func, arg):
        ss=0
        res = ''
        w = ''
        while 0 <= ss < len(text):
            try:
                i = text.index('<',ss)
                w=text[ss:i]
                ss = i
            except:
                w=text[ss:]
                ss = -1
            if w.strip():
                # process text between tagtext if any.
                res += func(w, arg)
            else:
                res += ' '
            if ss >= 0:
                i = text.index('>',ss)
                res+=text[ss:i+1]
                ss=i+1
        return res
    
    # --- Make out document methods
    def make_description(self):
        author = self.descr.has_key('author') and self.descr['author'] or ''
        title = self.descr.has_key('title') and self.descr['title'] or ''
        if not author and '.' in title :
            point = title.index('.')
            author = title[:point].strip()
            title = title[point+1:].strip()
        author = author.split()
        first_name = author and author[0] or ''
        middle_name = len(author) > 2 and author[1] or ''
        last_name = len(author) > 2 and author[2] or (len(author) > 1 and author[1] or '')
        retv='<description><title-info><genre></genre><author><first-name>%s' \
              '</first-name><middle-name>%s' \
              '</middle-name><last-name>%s</last-name></author>'\
              '<book-title>%s</book-title>' % (first_name, middle_name, last_name, title)
        if self.descr.has_key('annot'):
            retv+='<annotation>%s</annotation>' % self.descr['annot']
        retv+='</title-info><document-info><author><nickname></nickname></author>'\
               '<date value="%s">%s</date>'\
               '<id>%s</id>'\
               '<version>1.0</version>'\
               '<program-used>h2fb ver. %s</program-used>' \
               '</document-info></description>' % \
               (time.strftime('%Y-%m-%d'),
                unicode(time.strftime('%d %B %Y, %H:%M'), self.params['sys-encoding']),
                oct(int(time.time())),
                version)
        return retv
    
    def make_notes(self):
        if not self.notes:
            return ''
        retv=['<section id="FictionBookId%s"><title><p>note %s</p></title>%s</section>' %
              (x,x,y) for x,y in self.notes]
        return '<body name="notes"><title><p>Notes</p></title>'+''.join(retv)+'</body>'
       
    def make_bins(self):
        if not self.bins:
            return ''
        return ''.join(['<binary content-type="image/jpeg" id="%s">%s</binary>' % \
                        (x.encode(self.params['encoding-to'],'xmlcharrefreplace'),y) for x,y in self.bins])
            
            

    # --- Auxiliary  methods
    def tag_repr(self, tag, attrs, single=False):
        ''' Start tag representation '''
        closer=single and '/' or ''
        if attrs:
            return "<%s %s%s>" % (tag, ' '.join(['%s="%s"' % x for x in attrs if x[1] is not None]),closer)
        else:
            return "<%s%s>" % (tag, closer)
    
    def clean_str(self, intext):
        ''' Remove simple tags from line. '''
        return _RE_TAG.sub('',intext)
    
    def is_roman_number(self, instr):
        '''
        Detect - is instr is roman number
        '''
        instr = self.clean_str(instr).strip()
        if len(instr)>8:
            return False
        return bool(_RE_ROMAN.match(instr))
    
    def msg(self, msg, level=0):
        if self.informer and self.params['verbose'] > level:
            self.informer(msg)
        
    def make_id(self, id):
        '''
        Make properly link id
        '''
        # FIX: make id later
        return id

    def print_out(self, data=None):
        if data is None:
            data = self.out
        for i in data:
            if type(i) == ListType:
                print '['
                for j in i:
                    print j.encode('koi8-r','replace')
                print ']'
            else:
                print i.encode('koi8-r','replace')

    def convert_image(self, filename):
        if not self.params['convert-images']:
            f=open(filename)
            data = f.read()
            f.close()
        else:
            data = convert2png(filename)
        if data:
            data=base64.encodestring(data)
        return data

def usage():
    print '''
HTML to FictionBook converter, ver. %s
Usage: h2fb.py [options]
where options is:
    -i, --input-file         Input file name(stdin)
    -o, --output-file        Output file name(stdout)
    -f, --encoding-from      Source encoding(autodetect)
    -t, --encoding-to        Result encoding(Windows-1251)
    -h, --help               This help
    -r,  --header-re         Regular expression for headers detection('')
    --not-convert-quotes     Not convert quotes
    --not-convert-hyphen     Not convert hyphen
    --skip-images            Skip messages
    --skip-ext-links         Skip external links
    --allow-empty-lines      Allow generate tags <empty-line/>
    --not-detect-italic      Not detect italc
    --not-detect-headers     Not detect sections headers
    --not-detect-epigraphs   Not detect epigraphs
    --not-detect-paragraphs  Not detect paragraphs
    --not-detect-annot       Not detect annotation
    --not-detect-verses      Not detect verses
    --not-detect-notes       Not detect notes
''' % version

def convert_to_fb(opts):
    import locale, getopt
    locale.setlocale(locale.LC_ALL, '')
    try:
        sys_encoding = locale.nl_langinfo(locale.CODESET)
    except AttributeError:
        sys_encoding = "Windows-1251"
        
    out_file=sys.stdout
    params={
        'file-name'         : '',       # File name
        'data'              : '',       # Data for processing
        'encoding-from'     : '',       # Source data encoding
        'encoding-to'       : 'Windows-1251',       # Result data encoding
        'convert-quotes'    : 1,        # Convert "" to << >>
        'convert-hyphen'    : 1,        # Convert - to ndash
        'header-re'         : '',       # regexp for detecting section headers
        'skip-images'       : 0,        # Ignore images (not include it to result)
        'skip-ext-links'    : 0,        # Ignore external links
        'skip-empty-lines'  : 1,        # Not generate <empty-line/> tags
        'detect-italic'     : 1,        # Detect italc (_italic text here_)
        'detect-headers'    : 1,        # Detect sections headers
        'detect-epigraphs'  : 1,        # Detect epigraphs
        'detect-paragraphs' : 1,        # Detect paragraphs
        'detect-annot'      : 1,        # Detect annotation
        'detect-verses'     : 1,        # Detect verses
        'detect-notes'      : 1,        # Detect notes ([note here] or {note here})
        'verbose'           : 1,        # Verbose level
        'convert-images'    : 1,        # Convert images to png or no.
        }

    params['sys-encoding'] = sys_encoding
    params['informer'] = sys.stderr.write
    try:
        opts, args = getopt.getopt(opts,
                                   "i:o:f:t:hv:r:",
                                   ['input-file=',
                                    'output-file=',
                                    'encoding-from=',
                                    'encoding-to=',
                                    'help',
                                    'verbose=',
                                    'not-convert-quotes',
                                    'header-re=',
                                    'skip-images',
                                    'skip-ext-links',
                                    'allow-empty-lines',
                                    'not-detect-italic',
                                    'not-detect-headers',
                                    'not-detect-epigraphs',
                                    'not-detect-paragraphs',
                                    'not-detect-annot',
                                    'not-detect-verses',
                                    'not-detect-notes',
                                    'not-convert-images',
                                    'not-convert-hyphen',
                                    ]
                                   )
    except getopt.GetoptError:
        usage()
        return
    for opt, val in opts:
        if opt in ('-i','--input-file'):
            params['file-name']=val
        elif opt in ('-o','--output-file'):
            try:
                out_file=file(val,'w')
            except:
                pass
        elif opt in ('-f','--encoding-from'):
            params['encoding-from']=val
        elif opt in ('-t','--encoding-to'):
            params['encoding-to']=val
        elif opt in ('-h','--help'):
            usage()
            return
        elif opt in ('--not-convert-quotes',):
            params['convert-quotes']=0
        elif opt in ('-r', '--header-re'):
            params['header-re']=unicode(val, sys_encoding)
        elif opt in ('--skip-images',):
            params['skip-images']=1
        elif opt in ('--skip-ext-links',):
            params['skip-ext-links']=1
        elif opt in ('--allow-empty-lines',):
            params['skip-empty-lines']=0
        elif opt in ('--not-detect-italic',):
            params['detect-italic']=0
        elif opt in ('--not-detect-headers',):
            params['detect-headers']=0
        elif opt in ('--not-detect-epigraphs',):
            params['detect-epigraphs']=0
        elif opt in ('--not-detect-paragraphs',):
            params['detect-paragraphs']=0
        elif opt in ('--not-detect-annot',):
            params['detext-annot']=0
        elif opt in ('--not-detect-verses',):
            params['detect-verses']=0
        elif opt in ('--not-detect-notes',):
            params['detect-notes']=0
        elif opt in ('--not-convert-images',):
            params['convert-images']=0
        elif opt in ('--not-convert-hyphen',):
            params['convert-hyphen']=0
        elif opt in ('-v','--verbose',):
            params['verbose']=int(val)
    data=MyHTMLParser().process(params)
    out_file.write(data)
    out_file.close()

if __name__=='__main__':
    if sys.version_info[0] < 2 or sys.version_info[1] < 3:
        sys.stderr.write('Python 2.3 or newer it is necessary for start of the program.\n')
    else:
        convert_to_fb(sys.argv[1:])


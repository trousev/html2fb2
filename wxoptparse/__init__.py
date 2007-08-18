#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import optparse
from optparse import OptionParser
from elementtree import ElementTree

import wx, wx.lib.intctrl
import textwrap
import os,sys,re

class SecondWindow(wx.Frame):
    """ Not used at the moment.
    The idea is to have a graphical window where the output is sent """
    
    def __init__(self):
        self.orig = sys.stdout
        title = "wxOptParser"
        wx.Frame.__init__(self, 
            None, 
            wx.ID_ANY, 
            title, 
            size = (900,600),
            style = wx.DEFAULT_FRAME_STYLE)
        self.panel = wx.Panel(self, -1)
        
        aVBox = wx.BoxSizer(wx.VERTICAL)
        aVBox.Add(wx.StaticText(self.panel, -1, "Output:"), 0, flag=wx.LEFT | wx.TOP, border = 5)
        self.ctrlTextOutput = wx.TextCtrl(self.panel, -1, '', size=(600, 50))
        aVBox.Add(self.ctrlTextOutput, 0, flag=wx.ALL, border = 5)
        self.panel.SetSizer(aVBox)
        self.panel.Fit()
        self.Fit()
        
    def write(self, info):
        self.orig.write(info)
        
        
class wxOptParser(optparse.OptionParser):
    def _retAppFrame(self, args=None, values=None):
        """ This is required for testing """
        
        rargs = self._get_args(args)
        if values is None:
            values = self.get_default_values()

        self.rargs = rargs
        self.largs = largs = []
        self.values = values
        self.commandLineLst = [] # My little addition
        
        try:
            stop = self._process_args(largs, rargs, values)
        except (BadOptionError, OptionValueError), err:
            self.error(err.msg)

        args = largs + rargs
        (self.options, self.args) = self.check_values(values, args)

        app = wx.PySimpleApp()
        # Skip the first arg, it's the name of the python program
        frame = MainWindow(self, self.option_list, self.options, self.args[1:])

        app.MainLoop()
        
        return app, frame
        
    def parse_args(self, args=None, values=None):
        app, frame = self._retAppFrame(args, values)
        if hasattr(self, '_wxOptParseCallback'):
            # This gives you a chance to change/test some stuff when the dialog is up
            self._wxOptParseCallback(self, app, frame)

        del frame
        del app
        return (self.options, self.args)
        

def get_file_types(option):
    ## ideally this would have been done by the calling script, this would need new type addition
    ## See http://docs.python.org/lib/optparse-adding-new-types.html
    def extract_list_items(in_str):
        """Simple routine to extract items enclosed in parens, seperated by pipe.
        For example, (1|2|3). slightly different to CHOICE version used in optionparse
        """
        ## will never contain ':' and '|' is not allowed either, not is ','
        # may NOT contain '(' or ')'
        # allow white space? Yes so find markers
        start_marker=in_str.find('(')+1
        end_marker=in_str.find(')')
        if start_marker == -1 or end_marker == -1:
            result=None
        else:
            result=tuple(in_str[start_marker:end_marker].split('|'))
        return result
    file_specification=option.getHelp().lstrip()
    result = extract_list_items(file_specification)
    return result

class MainWindow(wx.Frame):
    """ We simply derive a new class of Frame. """
    
    def __init__(self, parent, options, parsed_options, parsed_args):
        self.et = None
        self.parsed_options = parsed_options
        self.parent = parent # wxOptParser
        self.progname = sys.argv[0]
        self.bPipe = True
        
        self.options = options
        self.ctrlOptions = []
        id = -1
        
        title = "wxOptParse"
        
        wx.Frame.__init__(self, 
            None,
            wx.ID_ANY,
            title,
            size = (900,600),
            style = wx.DEFAULT_FRAME_STYLE)
            
        self.panel = wx.ScrolledWindow(self, -1, (0, 0), style=wx.TAB_TRAVERSAL)
        
        self.loadSavedInfo()
        
        aVBox = wx.BoxSizer(wx.VERTICAL)
        
        text = wx.StaticText(self.panel, -1, self.progname, style = wx.ALIGN_CENTRE)
        font = wx.Font(18, family = wx.SWISS, style = wx.NORMAL, weight = wx.NORMAL)
        text.SetFont(font)
        text.SetSize(text.GetBestSize())
        aVBox.Add(text, flag=wx.ALL, border = 5)

        for myOption in IterOptions(self):
            strHelp = myOption.getHelp()
                
            if myOption.toSkip():
                pass # skip these
            elif myOption.isChoice():
                choices = [''] + list(myOption.getChoices())
                cbox = wx.ComboBox(self.panel, -1, choices = choices, style = wx.CB_READONLY | wx.CB_DROPDOWN)
                self._addCtrl(aVBox, cbox, myOption, wx.EVT_COMBOBOX, self.OnComboChanged, strHelp)
            elif myOption.isBoolean():
                listHelp = textwrap.wrap(strHelp)
                checkb = wx.CheckBox(self.panel, -1, listHelp[0], size=(600, 20))
                self._addCtrl(aVBox, checkb, myOption, wx.EVT_CHECKBOX, self.OnCheckClicked)
                if len(listHelp) > 1:
                    aVBox.Add(wx.StaticText(self.panel, -1, '\n'.join(listHelp[1:])), flag = wx.LEFT, border = 20)
            elif myOption.getType() == 'int':
                min = wx.lib.intctrl.IntCtrl(self.panel, size=( 50, -1 ) )
                min.SetNoneAllowed(True)
                min.SetValue(None)
                self._addCtrl(aVBox, min, myOption, wx.lib.intctrl.EVT_INT, self.OnIntChanged, strHelp)
            elif myOption.getType() == 'float':
                textctrl = wx.TextCtrl(self.panel, -1, size=(50, -1))
                self._addCtrl(aVBox, textctrl, myOption, wx.EVT_TEXT, self.OnTextChange, strHelp)
            elif self._guessFile(myOption):
                self._addFileBox(aVBox, myOption)
            elif self._guessPath(myOption):
                self._addPathBox(aVBox, myOption)
            else:
                textctrl = wx.TextCtrl(self.panel, -1, size=(-1, -1))
                self._addCtrl(aVBox, textctrl, myOption, wx.EVT_TEXT, self.OnTextChange, strHelp)

        self.ctrlExtraArgs = wx.TextCtrl(self.panel, -1, '', size=(-1,-1))
        aVBox.Add(wx.StaticText(self.panel, -1, "Additional arguments:"), 0, flag=wx.LEFT | wx.TOP, border = 5)
        aVBox.Add(self.ctrlExtraArgs, 0, flag=wx.ALL | wx.EXPAND, border = 5)
        
        if parsed_args != None and len(parsed_args) > 0:
            self.ctrlExtraArgs.SetValue(' '.join(parsed_args))
        else:
            if self.et:
                item = self.et.find('extra')
                if item != None:
                    strValue = item.attrib['lastval']
                    if strValue != None and strValue != 'None':
                        self.ctrlExtraArgs.SetValue(strValue)
            
        self.ctrlExtraArgs.Bind(wx.EVT_TEXT, self.OnTextChange)
        
        # Read-only for now, but would be nice to make read-write and allow 
        # users to put values there as well.
        #self.ctrlParams = wx.TextCtrl(self.panel, -1, '', size=(-1,-1))
        self.ctrlParams = wx.TextCtrl(self.panel, -1, '', size=(-1,-1), style=wx.TE_READONLY)
        aVBox.Add(wx.StaticText(self.panel, -1, "Params:"), 0, flag=wx.LEFT | wx.TOP, border = 5)
        aVBox.Add(self.ctrlParams, 0, flag=wx.ALL | wx.EXPAND, border = 5)
        
        self.ctrlGo = wx.Button(self.panel, wx.ID_OK, "Go")
        self.ctrlGo.SetDefault()
        aVBox.Add(self.ctrlGo, flag = wx.ALL, border = 5)
        self.ctrlGo.Bind(wx.EVT_BUTTON, self.OnGo)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.buildParams()

        self.panel.SetSizer(aVBox)
        self.panel.Fit()
        
        w, h = self.panel.GetSize()
        maxW = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_X)
        maxH = wx.SystemSettings_GetMetric(wx.SYS_SCREEN_Y)
        self.panel.SetScrollbars(20, 20, w/20, h/20)
        if w <= maxW and h <= maxH:
            self.Fit()        
        self.Show(True)

    def _guessFile(self, option):
        strSearch = option.getHelp()
        if not strSearch:
            return False
        return 'file' in strSearch.lower()
    
    def _guessPath(self, option):
        strSearch = option.getHelp()
        if not strSearch:
            return False
        return 'path' in strSearch.lower() or 'folder' in strSearch.lower()
    
    def _addFileBox(self, aVBox, option):
        ahBox = wx.BoxSizer(wx.HORIZONTAL)
        avBox = wx.BoxSizer(wx.VERTICAL)
        
        textctrl = wx.TextCtrl(self.panel, -1, size=(-1, -1))
        self._addCtrl(avBox, textctrl, option, wx.EVT_TEXT, self.OnTextChange, option.getHelp())
        
        ahBox.Add(avBox)
        button = wx.Button(self.panel, -1, '...', size=(30, -1))
        ahBox.Add(button, 0, flag = wx.BOTTOM | wx.ALIGN_BOTTOM, border = 4)
        
        #button.Bind(wx.EVT_BUTTON, self.generate_OnClickFile())
        #button.Bind(wx.EVT_BUTTON, self.generate_OnClickFile(('*.jpg','*.png','*.py')))
        file_type_list=get_file_types(option)
        button.Bind(wx.EVT_BUTTON, self.generate_OnClickFile(file_type_list))
        
        aVBox.Add(ahBox, 0, flag = wx.LEFT | wx.TOP, border = 0)

    def _addPathBox(self, aVBox, option):
        ahBox = wx.BoxSizer(wx.HORIZONTAL)
        avBox = wx.BoxSizer(wx.VERTICAL)
        
        textctrl = wx.TextCtrl(self.panel, -1, size=(-1, -1))
        self._addCtrl(avBox, textctrl, option, wx.EVT_TEXT, self.OnTextChange, option.getHelp())
        
        ahBox.Add(avBox)
        button = wx.Button(self.panel, -1, '...', size=(30, -1))
        ahBox.Add(button, 0, flag = wx.BOTTOM | wx.ALIGN_BOTTOM, border = 4)
        button.Bind(wx.EVT_BUTTON, self.OnClickFolder)
        
        aVBox.Add(ahBox, 0, flag = wx.LEFT | wx.TOP, border = 0)
        
    def _addCtrl(self, aVBox, ctrl, option, eventId, function, text = None):
        if text:
            aVBox.Add(wx.StaticText(self.panel, -1, textwrap.fill(text), size=(600, -1)), 0, flag=wx.LEFT | wx.TOP, border = 5)
        
        strDefault = option.getDefault()
            
        if strDefault != None:
            if isinstance(ctrl, wx.lib.intctrl.IntCtrl):
                try:
                    ctrl.SetValue(int(strDefault))
                except:
                    ctrl.SetValue(None)
            elif isinstance(ctrl, wx.CheckBox):
                if strDefault == 'True' or strDefault == True:
                    strDefault = True
                elif strDefault == 'False' or strDefault == False:
                    strDefault = False
                else:
                    strDefault = None
                if strDefault == None:
                    ctrl.SetValue(False)
                elif option.getAction() == 'store_false':
                    ctrl.SetValue(not strDefault)
                else:
                    ctrl.SetValue(strDefault)
            elif option.isChoice():
                if str(strDefault) in option.getChoices():
                    ctrl.SetValue(str(strDefault))
            else:
                ctrl.SetValue(str(strDefault))
        
        aVBox.Add(ctrl, 0, flag = wx.EXPAND | wx.ALL, border = 5)
        self.ctrlOptions.append((ctrl, option.option))
        ctrl.Bind(eventId, function)

    def OnGo(self, evnt):
        self.params =  self._buildParams()
        values = self.parent.get_default_values()
        self.saveInfo()
        
        self.parent.rargs = self.params[:]
        self.parent.largs = largs = []
        self.parent.values = values

        try:
            stop = self.parent._process_args(largs, self.parent.rargs, values)
        except (optparse.BadOptionError, optparse.OptionValueError), err:
            print err

        args = largs + self.parent.rargs
        (self.parent.options, self.parent.args) = self.parent.check_values(values, args)

        #print "Args:", self.params
        self.Unbind(wx.EVT_CLOSE)
        self.ctrlGo.Unbind(wx.EVT_BUTTON)
        self.ctrlExtraArgs.Unbind(wx.EVT_TEXT)
        self.Destroy()
        
    def OnTextChange(self, event):
        self.buildParams()

    def generate_OnClickFile(self, wildcard_options=None):
        if wildcard_options is None:
            #wildcard_options='All files (*.*)|*.*|Compiled python files (*.pyc)|*.pyc'
            wildcard_options='All files (*.*)|*.*'
        else:
            # assume a tuple or list of extensions
            temp_str_list=[]
            for x in wildcard_options:
                temp_str_list.append('(%s)' % x)
                temp_str_list.append(x)
            ## TODO Always add 'All files (*.*)|*.*' to end?
            wildcard_options='|'.join(temp_str_list)
        
        # note no self reference
        def wildcardOnClickFile(event):
            ctrl = event.GetEventObject()
            dlg = wx.FileDialog(
                self, message="Choose a file", defaultDir=os.getcwd(), 
                defaultFile="", wildcard=wildcard_options, style=wx.OPEN | wx.CHANGE_DIR
                )

            # Show the dialog and retrieve the user response. If it is the OK response, 
            # process the data.
            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
        
                ctrl = self.prevTextCtrl(event)
                ctrl.SetValue(' '.join(paths))

            # Destroy the dialog. Don't do this until you are done with it!
            # BAD things can happen otherwise!
            dlg.Destroy()
        return wildcardOnClickFile

    def OnClickFolder(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)

        # If the user selects OK, then we process the dialog's data.
        # This is done by getting the path data from the dialog - BEFORE
        # we destroy it. 
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = self.prevTextCtrl(event)
            ctrl.SetValue(dlg.GetPath())
            
        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()

    def prevTextCtrl(self, event):
        ctrl = event.GetEventObject()
        ctrlParent = ctrl.GetParent()
        windows = ctrlParent.GetChildren()
        ctrlPrev = windows[0]
        for win in windows:
            if win == ctrl:
                break
            if isinstance(win, wx.TextCtrl):
                winPrev = win
        return winPrev
        
    def OnCheckClicked(self, event):
        self.buildParams()

    def OnComboChanged(self, event):
        self.buildParams()
        
    def OnIntChanged(self, event):
        self.buildParams()
        
    def buildParams(self):
        self.parent.commandLineLst = self._buildParams(useQuotes = True)[:]
        self.ctrlParams.SetValue(' '.join(self.parent.commandLineLst))

    def _buildParams(self, useQuotes = False):
        strTextList = []
        for myOption in IterOptions(self):
            
            strValue = myOption.getValue()
            if strValue == 'None':
                strValue = ''
                
            if myOption.isChoice():
                if strValue != None and len(strValue) > 0:
                    strTextList.append(myOption.getOptString())
                    if useQuotes and (' ' in strValue or '*' in strValue or '?' in strValue):
                        strValue = '"%s"' % (strValue)
                    
                    strTextList.append(strValue)
            elif myOption.isBoolean():
                if myOption.getBooleanStringValue() == "True":
                    strTextList.append(myOption.getOptString()) # FIX to check, why opt_string()?
            else:
                if myOption.getType() == 'int':
                    strValue = str(strValue)
                elif myOption.getType() == 'float':
                    try:
                        strValue = str(float(strValue))
                    except ValueError:
                        strValue = ''
                    
                if len(strValue) > 0:
                    strTextList.append(myOption.getOptString())
                    if useQuotes and (' ' in strValue or '*' in strValue or '?' in strValue):
                        strValue = '"%s"' % (strValue)
                    
                    strTextList.append(strValue)

        extraArgsValue = self.ctrlExtraArgs.GetValue()
        if extraArgsValue:
            extraArgs = [x.strip() for x in extraArgsValue.split(' ') 
                if len(x.strip()) > 0]
            
            if len(extraArgs) > 0:
                strTextList += extraArgs
        
        return strTextList

    def loadSavedInfo(self):
        strFilename = self.getXmlFilename()
        if strFilename == None:
            return
        
        if not os.path.isfile(strFilename):
            return 

        # print "Loading up %s" % (strFilename)
        self.et = ElementTree.parse(strFilename)
        
    def saveInfo(self):
        strFilename = self.getXmlFilename()
        if strFilename == None:
            return
        
        # print "Saving to arguments to: %s" % ( strFilename)
        if self.et:
            """ There is no elementree the first time """
            self.updateElementTree()
            self.et.write(strFilename, encoding="iso-8859-1")
            return
        
        of = file(strFilename, "w")
        of.write('<wxOptParse app="%s">\n' % (self.progname))
        for myOption in IterOptions(self):
            of.write('  <option name="%s"' % (myOption.getName()))
            strValue = myOption.getValue()
            
            if myOption.isChoice() or myOption.isNumber():
                of.write(' lastval="%s">\n' % (strValue,))
            elif myOption.isBoolean():
                of.write(' lastval="%s">\n' % (myOption.getBooleanStringValue(),))
            else:
                of.write(' lastval="%s">\n' % (strValue,))
            
            of.write('  </option>\n')

        of.write('  <extra lastval="%s">\n' % (str(self.ctrlExtraArgs.GetValue())))
        of.write('  </extra>\n')

        of.write('</wxOptParse>\n')
        
        of.close()

    def updateElementTree(self):
        """ Go through the elementtree and make sure that everything matches 
        the controls.
        
        The element must already be in the elementtree
        """
        for ctrl, option in self.ctrlOptions:
            strName = option.dest
            if option.action == 'store_true' or option.action == 'store_false':
                if (option.action == 'store_true' and ctrl.IsChecked() == True) or \
                    (option.action == 'store_false' and ctrl.IsChecked() == False):
                    strLastVal = 'True'
                elif ctrl.GetValue() != None:
                    strLastVal = 'False'
                else:
                    strLastVal = 'None'
            else:
                strLastVal = str(ctrl.GetValue())
            
            self.updateElement(strName, strLastVal)
        self.updateExtraArg()
        
    def updateElement(self, strName, strLastVal):
        for item in self.et.findall('//option'):
            if item.attrib['name'] == strName:
                #print "%s = '%s'" % (strName, strLastVal)
                if strLastVal == optparse.NO_DEFAULT:
                    strLastVal = None
                previous = item.attrib['lastval'][:]
                item.attrib['lastval'] = str(strLastVal)
                self.AppendRecent(item, strLastVal, previous)
                break

    def updateExtraArg(self):
        """ Update the "extra" arg which is handled a little differently
        """
        item = self.et.find('//extra')
        if item != None:
            previous = item.attrib['lastval'][:]
            value = self.ctrlExtraArgs.GetValue()
            if value == None:
                value = 'None'
            item.attrib['lastval'] = value
            self.AppendRecent(item, item.attrib['lastval'], previous)
            
    def AppendRecent(self, node, curVal, lastVal):
        if str(curVal) == str(lastVal):
            return
        
        node.text = '\n    '
        
        for event in node.findall('recent'):
            if event.attrib['value'] == curVal:
                node.remove(event)
                break
        
        newNode = ElementTree.Element('recent')
        newNode.attrib['value'] = lastVal
        newNode.tail = '\n    '
        node.insert(0, newNode)

    def getXmlFilename(self):
        strFilename = _WxOptParseGetXmlFromFilename(self.progname)
        if strFilename == self.progname:
            # Whatever we do, don't overwrite the program
            return None

        return strFilename
        
    def OnClose(self, event):
        self.Destroy()
        sys.exit(-1)


class IterOptions:
    def __init__(self, parent):
        self.parent = parent
        
        if len(self.parent.ctrlOptions) > 0:
            self.list = self.parent.ctrlOptions
        else:
            self.list = self.parent.options
        
        self.nIndex = 0
        
    def __iter__(self):
        return self
        
    def next(self):
        if self.nIndex < len(self.list):
            self.nIndex += 1
            return MyOption(self.list[self.nIndex - 1], self.parent.et, 
                self.parent.parsed_options)
        raise StopIteration

class MyOption:
    """ Option class handles elementtree and optparse.options
    
    Create a class so that all the times we have to iterate over the options 
    we have a consistent set of rules about what type of object we are 
    looking at, for example .
    """
    def __init__(self, listItem, et, parsed_options):
        self.et = et
        self.parsed_options = parsed_options
        if isinstance(listItem, tuple):
            self.ctrl, self.option = listItem
        else:
            self.ctrl = None
            self.option = listItem
        
    def getCtrl(self):
        return self.ctrl
    
    def getType(self):
        return self.option.type
    
    def getValue(self):
        strValue = self.ctrl.GetValue()
        if strValue == None  or str(strValue) == str(optparse.NO_DEFAULT):
            strValue = 'None'
            
        return strValue
        
    def getName(self):
        return self.option.dest
        
    def isChoice(self):
        return self.option.choices != None

    def getChoices(self):
        return self.option.choices
        
    def isNumber(self):
        return self.option.type == 'int' or self.option.type == 'float'
    
    def isBoolean(self):
        return self.option.action == 'store_true' or self.option.action == 'store_false'

    def getBooleanStringValue(self):
        if (self.option.action == "store_true" and self.getValue() == True) or \
            (self.option.action == "store_false" and self.getValue() == False):
            return "True"
        elif self.getValue() != 'None':
            return "False"
        return "None"

    def getOptString(self):
        try:
            return self.option.get_opt_string()
        except:
            # This should work with older versions of optparse
            if self.option._long_opts:
                return self.option._long_opts[0]
            else:
                return self.option._short_opts[0]

    def getAction(self):
        return self.option.action
        
    def getHelp(self):
        strHelp = self.option.help
        
        if not strHelp and self.option._long_opts:
            strHelp = self.option._long_opts[0]
        if not strHelp and self.option._short_opts:
            strHelp = self.option._short_opts[0]

        return strHelp
        
    def toSkip(self):
        return self.option.action == 'help' or self.option.action == 'version'

    def getDefault(self):
        strDefault = self.option.default
        
        if hasattr(self.parsed_options, self.option.dest):
            strDefault = getattr(self.parsed_options, self.option.dest)
            if strDefault != None:
                return strDefault
        
        if self.findLastVal(self.option.dest) != None:
            strDefault = self.findLastVal(self.option.dest)
        
        if str(strDefault) == str(optparse.NO_DEFAULT):
            strDefault = None
            
        return strDefault

    def findLastVal(self, strName):
        return self.findItemAttrib(strName, 'lastval')
        
    def findItemAttrib(self, strName, strAttrib):
        item = self.findItem(strName)
        if item != None and strAttrib in item.attrib:
            return item.attrib[strAttrib]
        return None

    def findItem(self, strName):
        if self.et == None:
            return None
            
        for item in self.et.findall('//option'):
            if item.attrib['name'] == strName:
                return item

        return None

    def __str__(self):
        return "%s:%s" % (self.getName(), self.getDefault())

def _WxOptParseGetXmlFromFilename(strFilename):
    strFilename = re.sub(r'\..{1,4}$', '.args', strFilename)
    strDirName = os.path.dirname(strFilename)
    strBaseName = os.path.basename(strFilename)
    # Add the dot to hide in in Linux
    strFilename = os.path.join(strDirName, '.' + strBaseName)
    strFilename = os.path.normpath(strFilename)
    
    return strFilename


g_orginalOptionParser = optparse.OptionParser
optparse.OptionParser = wxOptParser
OptionParser = wxOptParser

def handleCommandLine():
    import sys
    
    if len(sys.argv) > 1 and len(sys.argv[1]) > 0:
        strFilename = sys.argv[1]
    else:
        print "usage: wxoptparse.py <programtorun>"
        #~ strFilename = "tests/mytest.py"
        #~ strFilename = "tests/noDefaultsTest.py"
        #strFilename = "tests/grepTest.py"
        sys.exit(-1)
        
    strDir = os.path.dirname(strFilename)
    if len(strDir) > 0:
        sys.path.append(os.path.abspath(strDir))
    sys.path.append('.') 
    globals()['__name__'] = '__main__'
    
    sys.argv[0] = os.path.basename(strFilename) # Let's cheat
    if sys.argv[0] == strFilename and len(strDir) > 0:
        sys.argv[0] = sys.argv[0][len(strDir):]
    
    strModuleName = sys.argv[0][:]
    if strModuleName.endswith('.py'):
        strModuleName = strModuleName[:-3]
    
    module = __import__(strModuleName)
    module.__dict__.update(globals())
    execfile(strFilename, module.__dict__)

if __name__ == "__main__":
    handleCommandLine()

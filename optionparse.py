# From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/278844
# Simple optparse wrapper that removes even more boiler plate that 
# command line arg passing introduces
#
# clach04
#
# This is modified from the original code snippet
#   *   adds GUI support via http://wxoptparse.berlios.de/
#       if no arguments present AND wxoptparse available
#   *   adds INTeger type enforcement, other types to be added as needed.
#   *   added support for only one (long) param, i.e. no need for "-p" and "--param"
#   *   Updated Usage detection regex to hand "Usage" and "usage"
#   *   added FLOAT type support
#   *   added CHOICE type support, uses (1|2) to indicate choices
#   *   added DEFAULT support

"""\
:Author: M. Simionato
:Date: April 2004
:Title: A much simplified interface to optparse.

You should use optionparse in your scripts as follows.
First, write a module level docstring containing something like this
(this is just an example):

'''usage: %prog files [options]
   -d, --delete: delete all files
   -e, --erase = ERASE: erase the given file'''
   
Then write a main program of this kind:

# sketch of a script to delete files
if __name__=='__main__':
    import optionparse
    option,args=optionparse.parse(__doc__)
    if not args and not option: optionparse.exit()
    elif option.delete: print "Delete all files"
    elif option.erase: print "Delete the given file"

Notice that ``optionparse`` parses the docstring by looking at the
characters ",", ":", "=", "\\n", so be careful in using them. If
the docstring is not correctly formatted you will get a SyntaxError
or worse, the script will not work as expected.
"""

import re, sys

from optparse import OptionParser as regular_OptionParser

try:
    #raise ImportError
    # from http://wxoptparse.berlios.de/
    from wxoptparse import wxOptParser as gui_OptionParser
    have_wxoptparse = True
except ImportError:
    have_wxoptparse = False



USAGE = re.compile(r'(?s)\s*[Uu]sage: (.*?)(\n[ \t]*\n|$)')

# Without the __nonzero__ update code below will fail to show usage in caller:
#
#   if not opt and not args:
#       optionparse.exit()
#
import optparse
def nonzero(self): # will become the nonzero method of optparse.Values       
    "True if options were given"
    for v in self.__dict__.itervalues():
        if v is not None: return True
    return False

optparse.Values.__nonzero__ = nonzero # dynamically fix optparse.Values

class ParsingError(Exception): pass

optionstring=""

class Usage(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        #return `self.value`
        # could return expr()
        return self.value
    """
    def __init__(self, msg):
        self.msg = msg
    """

def exit(msg=""):
    # exit with error message (note only works if stdout is working, e.g. NOT Windows .pyw or py2exe)
    # TODO add code to py2exe to display error text params from SystemExit
    raise SystemExit(msg or optionstring.replace("%prog",sys.argv[0]))

def exit_exception(msg=""):
    raise Usage(msg or optionstring.replace("%prog",sys.argv[0]))

def extract_list_items(in_str):
    """Simple routine to extract items enclosed in parens, seperated by pipe.
    For example, (1|2|3).
    """
    ## will never contain ':' and '|' is not allowed either, not is ','
    # may contain '(' or ')'
    # allow white space? Yes so find markers
    start_marker=in_str.find('(')+1
    end_marker=in_str.rfind(')')
    if start_marker == -1 or end_marker == -1:
        result=None
    else:
        result=tuple(in_str[start_marker:end_marker].split('|'))
    return result



def parse(docstring, arglist=None, exit_on_usage_error=True):
    global optionstring
    global exit
    OptionParser = regular_OptionParser
    if exit_on_usage_error == False:
        exit = exit_exception
    #print 'optionparse: arglist', arglist
    if arglist == [] and have_wxoptparse:
        # empty argument list passed into this function, so lets use a GUI
        OptionParser = gui_OptionParser
        # if arglist is None (i.e. ommitted), then still treat this like a Non-GUI script
    optionstring = docstring
    match = USAGE.search(optionstring)
    if not match: raise ParsingError("Cannot find the option string")
    optlines = match.group(1).splitlines()
    try:
        #p = optparse.OptionParser(optlines[0])
        #p = OptionParser(optlines[0])
        p = OptionParser(optionstring.replace("%prog",sys.argv[0])) ## print full usage information on bad flags
        for line in optlines[1:]:
            param_names=[]
            param_options={}
            opt, help=line.split(':')[:2]
            try:
                short,long=opt.split(',')[:2]
            except ValueError, info:
                # only 1 param specified. assume it was the long type (TODO add check!)
                short=None
                long=opt
            long_datatype="string"
            long_datatype=None
            if '=' in opt:
                # information will follow parameter
                action='store'
                long_split_list = long.split('=')
                long=long_split_list[0]
                #
                # Start of data type enforcement code
                # integers keyword in doc is INT,
                #   e.g.:   -b, --background_colour=INT: Number from (0 to n) of the colour to use as background colour.
                # floating point keyword in doc is FLOAT
                # choice list keyword in doc is CHOICE, with pipe seperated list enclosed in parens
                #   e.g.:   -c, --mychoice=CHOICE(one|two|three): choice of 3 things
                #
                long_datatype=long_split_list[1].lower()
                long_datatype_list=long_datatype.split()
                long_datatype=long_datatype_list[0]
                if long_datatype.startswith('choice'):
                    param_options['choices']=extract_list_items(long_datatype)
                if long_datatype not in ['int', 'choice', 'float']: #, 'filename' if using wxoptparse add new type?
                    # Unknown type, probably just some descriptive text about param
                    long_datatype=None #"string"
                
                # Start of DEFAULT code
                # default is either DEFAULT defaultvalue or DEFAULT=defaultvalue 
                #   e.g.:   -m, --main_colour=INT DEFAULT 99: Main colour number
                #   e.g.:   -t, --transparen_colour=INT DEFAULT=99: Transparent colour number
                #
                try:
                    default_marker=long_datatype_list[1]
                    if default_marker=='default':
                        try:
                            default_text=long_datatype_list[2]
                        except IndexError, info:
                            # could be in next list item, if not raise an error
                            default_text=long_split_list[2]
                        param_options['default']=default_text
                except IndexError, info:
                    # no default marker
                    pass
                
            else:
                # Simple on/off flag
                action='store_true'
            if short:
                param_names.append(short.strip())
                param_names.append(long.strip())
            else:
                param_names.append(long.strip())
            param_options['action']=action
            param_options['type']=long_datatype
            param_options['help']=help.strip()
            p.add_option(*param_names, **param_options )
    except (IndexError,ValueError):
        print IndexError,ValueError ## DEBUG
        raise ## DEBUG
        raise ParsingError("Cannot parse the option string correctly")
    return p.parse_args(arglist)


'''
# Example script
################ cut here and create a new script ################ 
"""An example script invoking optionparse, my wrapper around optparse.

  usage: %prog [options] args
  -f, --filename=FILENAME: name of file to use
  -b, --background_colour=INT: Background colour number
  -m, --main_colour=INT DEFAULT 99: Main colour number
  -t, --transparen_colour=INT DEFAULT=99: Transparent colour number
  -l, --latitude=FLOAT: co-ordinate with dot (NOTE wxoptparse has a bug with letting non float data into field it does the right thing by NOT setting the param but does not show error/beep (as it does for INT) on screen)
  -p, --positional: print positional arguments
  -1, --option1=OPTION1: print option1
  -2, --option2=ANY OLD TEXT: print option2
  -c, --mychoice=CHOICE(one|two|three): choice of 3 things
  -o, --out-filename=FILENAME(*.jpg|*.png): FILENAME=(*.jpg|*.png) name of file to use
"""

## NOTE, doc string does not use: ',', ':', and filename/choice do not use '(',')', '|' in text description

## Caution! be careful not to optimize out (e.g. with py2exe) the docstrings
## i.e. set optimize=1 at most, e.g.:

#~ options = {
#~  'py2exe': { 
#~      "optimize": 1,  ## 1 and NOT 2 because I use the __doc__ string as the usage string. 2 optimises out the doc strings
#~      }
#~  }


import sys

import optionparse

#opt, args = optionparse.parse(__doc__)
argv=None
if argv is None:
    argv = sys.argv
opt, args = optionparse.parse(__doc__, argv[1:])

if not opt and not args:
    optionparse.exit()
if opt.background_colour:
    print 'opt.background_colour', opt.background_colour
if opt.positional:
    print 'args', args
if opt.option1:
    print 'opt.option1', opt.option1
if opt.option2:
    print 'opt.option2', opt.option2

print "opt, args ", opt, args
print 'end'

opt_dict={}
for temp_param in dir(opt):
    if not temp_param.startswith('_') and not callable(getattr(opt, temp_param)):
        opt_dict[temp_param] = getattr(opt, temp_param)
    
print "opt_dict['background_colour']", opt_dict['background_colour']
print "opt_dict['option1']", opt_dict['option1']
################ cut here end ################ 
'''
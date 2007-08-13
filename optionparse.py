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
                action='store'
                #long=long.split('=')[0]
                long_split_list = long.split('=')
                long=long_split_list[0]
                #
                # Start of data type enforcement code
                # integers only at this stage, keyword in doc is INT,
                # e.g.:   -b, --background_colour=INT: Number from (0 to n) of the colour to use as background colour.
                #
                long_datatype=long_split_list[1].lower()
                if long_datatype != 'int':
                    long_datatype="string"
                    long_datatype=None
            else:
                action='store_true'
            if short:
                p.add_option(short.strip(),long.strip(),action = action, type=long_datatype, help = help.strip())
            else:
                p.add_option(long.strip(),action = action, type=long_datatype, help = help.strip())
    except (IndexError,ValueError):
        print IndexError,ValueError ## DEBUG
        raise ## DEBUG
        raise ParsingError("Cannot parse the option string correctly")
    return p.parse_args(arglist)

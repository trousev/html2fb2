# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
"""wrapper around ConvertLIT http://www.convertlit.com/
this is simple  a wrapper around clit.exe NOT a library wrapper

Uses python 2.4 subprocess module http://docs.python.org/lib/module-subprocess.html
"""

import os
import re

import subprocess

class ConvertLITError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def del_dir(path):
    if not os.path.exists(path):
        return
    for file in os.listdir(path):
        file_or_dir = os.path.join(path,file)
        if os.path.isdir(file_or_dir) and not os.path.islink(file_or_dir):
            del_dir(file_or_dir) #it's a directory reucursive call to function again
        else:
            #os.remove(file_or_dir) #it's a file, delete it
            try:
                os.remove(file_or_dir) #it's a file, delete it
            except OSError, info:
                #probably failed because it is not a normal file or permissions problem
                if info.errno != 2:
                    print OSError, info.errno, info, dir(info)
                    raise
                    ## FIXME change perms....
                    os.remove(file_or_dir) #it's a file, delete it
                else:
                    pass
    os.removedirs(path) #delete the directory here

def safe_mkdir(newdir):
    result_dir = os.path.abspath(newdir)
    try:
        os.makedirs(result_dir)
    except OSError, info:
        if info.errno == 17 and os.path.isdir(result_dir):
            pass
        else:
            raise

def find_files_with_extension(directory_name, file_extension_list):
    # FIXME only does single dir (does not recurse)
    local_file_extension_list = [file_extension.lower() for file_extension in file_extension_list] 
    #file_extension = file_extension.lower()
    content = os.listdir(directory_name)
    temp_list = []
    for temp_file in content:
        for file_extension in local_file_extension_list:
            if temp_file.lower().endswith(file_extension):
                full_path = os.path.join(directory_name, temp_file)
                temp_list.append((os.path.getsize(full_path ), full_path ))
                break
    return  temp_list

def find_main_lit_file(directory_name):
    directory_name = os.path.abspath(directory_name)
    
    ### Dumb Brute Force find index.html (or derivatives)
    ## want case insensitive (recursive) glob....
    ##index_filename = os.path.join(directory_name, '.html
    ##os.path.exists()
    main_filename = None
    content = os.listdir(directory_name)
    for x in content:
        if x.lower() == 'index.html' or x.lower() == 'index.htm':
            main_filename = os.path.join(directory_name, x)
            break
    
    if main_filename is None:
        # Find largest html file
        file_list = find_files_with_extension(directory_name, ['.htm', '.html'] )
        ## get the filename of the largest size file
        file_list.sort()
        main_filename = file_list[-1][1] ## get the filename of the last  entry
    return main_filename
    


def ExtractLIT(in_filename, out_dirname=None, clit_exe=None):
    """Extract files from .lit file and return best guess main html file
    TODO should it return directory too, i.e. make out_dirname optional and default it if not specified?"""
    in_filename = os.path.abspath(in_filename)
    if out_dirname is None:
        out_dirname=in_filename+'_DIR'
    if clit_exe is None:
        clit_exe=CLIT_EXE
    if not os.path.exists(clit_exe):
        raise ConvertLITError('Missing ConvertLIT exe %r, download latest version from http://www.convertlit.com'% clit_exe)

    out_dirname = os.path.abspath(out_dirname)
    out_dirname = os.path.join(out_dirname, '') # add trailing slash to out_dirname  to prevent clit from crashing...

    #print 'ExtractLIT: in_filename', repr(in_filename )
    #print 'ExtractLIT: out_dirname', repr(out_dirname)

    del_dir(out_dirname)
    #safe_mkdir(out_dirname) ###  not needed for Windows, is needed for Linux??
    ## what about ConvertLIT stdio and stderr...?
    retcode = subprocess.call([clit_exe, in_filename, out_dirname])
    #print 'ExtractLIT: retcode', retcode

    if retcode != 0:
        raise ConvertLITError('subprocess call failed! retcode=%d'% retcode)

    return find_main_lit_file(out_dirname)


#####################
# Simple key words not tag based :-(
bad_values = """
<![if>
</![if>
<![endif]>
</![endif]>
<o:p>
</o:p>
<st1>
</st1:place>
</st1:placename>
</st1:placetype>
</st1:address>
</st1:street>
</st1:city>
</st1:state>
</st1:country-region>
"""

## TODO FIXME add:
"""
<st1*> -- i.e. wildcarded
"""
## DONE in aggresive experimental replace below


bad_values_list = []
for x in bad_values.split('\n'):
    if x != '':
        bad_values_list.append(x)

def clean_lit_str(in_str):
    """Clean up "bad" html that is present in various .lit xml files
    """
    return_str = in_str
    # clean values found in http://www.idpf.org/ / http://openebook.org files
    for x in bad_values_list:
        return_str = return_str.replace(x, '')
    return return_str

###################

def find_tags(in_str):
    # Good known tags....
    ## TODO: consider grabbing a list from w3,
    ##       e.g. http://www.w3.org/TR/html401/index/elements.html
    ignore_tags = [
'body',
'head',
'meta',
'html',
'style',
'title',
'body',
'br',
'sub',
'sup',
'h1',
'h2',
'h3',
'h4',
'h5',
'h6',
'h7', # ???
'b',
'i',
'a',
'p',
'span',
'div',
]

    findtags_re = r"""(?P<tag><.*?>)"""
    findtags_reobj = re.compile(findtags_re,  re.IGNORECASE| re.DOTALL)

    #findtagname_re = r"""</?(?P<tag_name>.*?)>"""
    #findtagname_re = r"""</?(?P<tag_name>\w+).*>"""
    findtagname_re = r"""</?(?P<tag_name>\S*).*>"""
    findtagname_reobj = re.compile(findtagname_re,  re.IGNORECASE| re.DOTALL)

    """
    for x in findtags_reobj.findall(in_str):
        print x
    print '-'*65
    """
    tag_counts = {}
    for x in findtags_reobj.finditer(in_str):
        temp_html_tag = x.group('tag')
        #print temp_html_tag
        """
        if not temp_html_tag.startswith('<?xml version="1.0"') and not temp_html_tag.startswith('<!DOCTYPE'):
            #print temp_html_tag,
            #print findtagname_reobj.search(temp_html_tag).group('tag_name')
            temp_tagname = findtagname_reobj.search(temp_html_tag).group('tag_name')
        else:
            temp_tagname=temp_html_tag
        if temp_tagname not in ignore_tags:
            tag_counts[temp_tagname] = tag_counts.setdefault(temp_tagname, 0) + 1
        """
        if temp_html_tag.startswith('<?xml version="1.0"') or temp_html_tag.startswith('<!DOCTYPE'):
            temp_tagname=temp_html_tag
        else:
            temp_tagname = findtagname_reobj.search(temp_html_tag).group('tag_name')
            if temp_tagname not in ignore_tags:
                tag_counts[temp_tagname] = tag_counts.setdefault(temp_tagname, 0) + 1
    return tag_counts

def tag_count_sort(tag_counts):
    sorted_tag_counts = []
    for x in tag_counts:
        sorted_tag_counts.append((tag_counts[x], x))
    sorted_tag_counts.sort()
    return sorted_tag_counts

def remove_unknown_tags(in_str, remove_tag_list):
    """Clean up "bad" html b removing uunknown tags
    """
    return_str = in_str
    done_tags = []
    for tag_count, tag_name in remove_tag_list:
        ## do a pass for tags with colons in them (remove after and including colon and use that to replace with instead)
        if ':' in tag_name:
            tag_name = tag_name[:tag_name.find(':')]
            if tag_name in done_tags:
                continue
            done_tags.append(tag_name)
        #temp_re = """</?%s.*?>""" % re.escape(tag_name)  #FIXME if tag_name = 'o' then tags such as "open" etc. are matched!! or 'su' (or 's') would match 'sub' and 'sup'
        temp_re = r"""</?%s(?!\w)[:\s]?.*?>""" % re.escape(tag_name)
        #print temp_re
        temp_compile_obj = re.compile(temp_re,  re.IGNORECASE| re.DOTALL)
        return_str = temp_compile_obj.sub('', return_str)
    return return_str

def experimental_clean_lit_str(html_str):
    """Agressive, find tags that we don't recognise and remove them.
    WARNING! Could remove good tags if "good tag" list is incomplete (which it is)
    """
    tag_count = find_tags(html_str)
    sorted_tag_counts = tag_count_sort(tag_count)
    
    #from pprint import pprint
    #pprint(sorted_tag_counts)
    
    clean_html = remove_unknown_tags(html_str, sorted_tag_counts)
    return clean_html

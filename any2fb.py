# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

"""
Any to FictionBook2 converter.
Primarily a HTML to FictionBook2 converter, supports; .html, .rtf, .lit, and .txt

Usage: %prog [options] args
    -i, --input-file=FILENAME: (*.html|*.htm|*.html|*.rtf|*.zip|*.lit|*.*) REQUIRED Input file name
    -o, --output-file=FILENAME: (*.fb2|*.*) Output file name, if left blank creates name based on input filename
    -f, --encoding-from=ENCODING_NAME:  Source encoding, autodetect if omitted.
    -t, --encoding-to=ENCODING_NAME DEFAULT=us-ascii:    Encoding to use in final fb2 book.
    --convert_span_to=CHOICE(em|strong|remove) DEFAULT=em: What to convert html <span> tags to
    --convert-quotes:     Convert quotes, i.e. convert "" to << >>
    --convert-hyphen:     Convert hyphens, i.e. - to ndash
    --skip-images:        Skip images, i.e. if specified do NOT include images.
    --convert-images:     Always convert images to PNG
    --no_centered_to_headers: (RTF input only) Do not convert centered text into (html)headers/(FB)titles. By default RTF centered text is converted into headers/titles
    --no_zip_output:    Do not create compressed ebook. By default output files are put in a zip file (to save space)
    --convertlit=FILENAME: (*.exe|*.*) (LIT input only) Filename for ConvertLIT executable (OPTIONAL, only needed for converting .LIT format, see www.convertlit.com)
    --no_clean_temp_lit: (LIT input only) Do not remove/delete intermediate exploded .lit files
    --aggressive_lit_html_clean: (LIT input only) Aggressive HTML clean for .lit source files (WARNING may loose proper tags!)
"""

import cgitb
#cgitb.enable(format="text") 

import sys

import optionparse
#import weboptionparse as optionparse
import h2fb
try:
    #raise ImportError
    import compressedfile
except ImportError:
    compressedfile=None


def main(argv=None):
    if argv is None:
        argv = sys.argv

    opt, args = optionparse.parse(__doc__, argv[1:])

    params = h2fb.default_params.copy()
    
    # Process command line options only used by this module
    rtf_centered_to_headers = opt.no_centered_to_headers != True
    del opt.no_centered_to_headers
    no_zip_output = opt.no_zip_output == True
    del opt.no_zip_output
    convertlit_path = opt.convertlit
    del opt.convertlit
    lit_clean_temp_dir = opt.no_clean_temp_lit != True
    del opt.no_clean_temp_lit
    aggressive_lit_html_clean = opt.aggressive_lit_html_clean == True
    del opt.aggressive_lit_html_clean
    
    # Convert out command line options into something h2fb can handle
    
    # convert underscores to hypens,
    # e.g. "option_something" in to "option-something" (which h2fb expects)
    opt_dict={}
    for temp_param in dir(opt):
        temp_value = getattr(opt, temp_param)
        if not temp_param.startswith('_') and not callable(temp_value):
            temp_key = temp_param.replace('_', '-') ## horrible hack! as "-" were turned into '_' in the argument processor
            if isinstance(temp_value, unicode):
                temp_value=str(temp_value)
            opt_dict[temp_key] = temp_value
    
    in_filename = opt_dict['input-file']
    del opt_dict['input-file']
    out_filename = opt_dict['output-file']
    del opt_dict['output-file']
    if not out_filename:
        out_filename = in_filename + '_' + opt_dict['encoding-to'] + '.fb2' ## dumb but quick

    # Handle .lit files
    isLIT=False
    ## FIXME clean up temp directory at end!!
    if in_filename.lower().endswith('.lit'):
        isLIT=True
    if isLIT:
        from litfuncs import ExtractLIT, clean_lit_str, del_dir, experimental_clean_lit_str
        
        lit_clean_html = clean_lit_str
        if aggressive_lit_html_clean:
            lit_clean_html = experimental_clean_lit_str
        ##FIXME get temp dir return... and use it later for clean up
        temp_lit_directory = out_filename + '__temp_lit_DIR'
        temp_html_filename = ExtractLIT(in_filename, temp_lit_directory, clit_exe=convertlit_path)
        print 'temp_html_filename', temp_html_filename
        in_filename = temp_html_filename
        # FIXME should be able to dectect this (in h2b??)
        #params['encoding-from'] = 'UTF-8'


    params['file-name'] = in_filename
    # Simply overwrite dictionary
    for temp_param in opt_dict:
        params[temp_param] = opt_dict[temp_param]
    
    params['detect-verses'] = 0 ## DEBUG, workaround for bug in detect-verses code (line length??), detect-verses makes NO sense for html input files, only makes sense for raw text files (h2fb can handle plain text files)
    params['skip-empty-lines'] = 0
    
    print 'Input file:', in_filename 
    print 'Output file:', out_filename

    if compressedfile is None:
        myfile_open = open
    else:
        myfile_open = compressedfile.open_zipfile
    if compressedfile is None or no_zip_output:
        myfile_open_for_write = open
    else:
        myfile_open_for_write = compressedfile.open_zipfile

    # start actually processing the file now
    
    in_file = myfile_open(in_filename, 'rb')
    out_file = myfile_open_for_write(out_filename, 'w')
    
    input_text = in_file.read()
    if isLIT:
        # .lit (html) input stream clean up
        input_text = lit_clean_html(input_text)
    #### DEBUG
    #~ print '-'*65
    #~ print repr(input_text[:24])
    #~ print '-'*65
    #~ print '='*65
    #~ input_text = unicode(input_text,'utf8')
    #~ print '*'*65
    #### DEBUG
    if input_text.startswith('{\\rtf'):
        # Looks like we have RTF data not html!
        import rtf.Rtf2Html
        #### START temp rtf workaround until Rtf2Html suports e?dash and optional hyphen
        # RTF input stream clean up
        ## See bug http://sourceforge.net/tracker/index.php?func=detail&aid=1811128&group_id=103452&atid=634851
        ## older rtf spec http://latex2rtf.sourceforge.net/RTF-Spec-1.0.txt
        
        # Newline removal ends up without any empty paragraphs (i.e. empty-line tags in FB2)
        # Fits in with what the input RTF file looks like so I think this is the RIGHT thing to do until RTF lib is fixed.
        # Also fixes missing bold tags in _some_ cases....
        input_text = input_text.replace('\r\n','') # remove newlines...
        input_text = input_text.replace('\n','') # remove newlines...
        ## TODO remove MAC newlines.....??
        for x in ['\emdash', '\\endash']:
            input_text = input_text.replace(x+' ','-')
            input_text = input_text.replace(x,'-')
        input_text = input_text.replace('\\-\n','') # remove, could replace...
        input_text = input_text.replace('\\-\r\n','') # remove, could replace...
        input_text = input_text.replace('\\-','') # remove, could replace...
        #### END temp rtf workaround until Rtf2Html suports e?dash and optional hyphen
        input_text = rtf.Rtf2Html.getHtml(input_text)
        ## TODO add Centered (or bold) tags as headers?
        if rtf_centered_to_headers:
            ## FIXME use beautiful soup (http://www.crummy.com/software/BeautifulSoup/) to find, '<div align='center'>' and convert to H2
            input_text = input_text.replace("<div align='center'>",'<h2>')
            input_text = input_text.replace('</div>','</h2>')
            
    ## TODO add beautiful soup (http://www.crummy.com/software/BeautifulSoup/) clean html before convert support? Possibly put that into h2fb? may help with bad nested bold tags (see unittest, test_nested_emphasis_italic_lesssimple)
    ## TODO add PDF support??
    ## TODO add Table Of Contents generation - if using a decent reader like Haalireader this is not needed.
    ## TODO zip'd support of html archives that contain images
    ## BUGFIX filenames in zip's - needed to ensure internal href's are translated correctly, especially for ./thisfile.html#link_name style href's
    
    params['data'] = input_text
    in_file.close()
    data=h2fb.MyHTMLParser().process(params)
    out_file.write(data)
    out_file.close()
    
    if isLIT:
        # .lit temp file clean up
        if lit_clean_temp_dir:
            del_dir(temp_lit_directory)

    return 0


if __name__ == "__main__":
    sys.exit(main())



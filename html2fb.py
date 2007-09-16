# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

"""
HTML to FictionBook2 converter.
NOTE Options/defaults are different to h2fb.

Usage: %prog [options] args
    -i, --input-file=FILENAME: (*.html|*.htm|*.html|*.rtf|*.zip|*.*) Input file name
    -o, --output-file=FILENAME: (*.fb2|*.*) Output file name, if left blank creates name based on input filename
    -f, --encoding-from=ENCODING_NAME:  Source encoding, autodetect if omitted.
    -t, --encoding-to=ENCODING_NAME DEFAULT=us-ascii:    Encoding to use in final fb2 book.
    --convert_span_to=CHOICE(em|strong|remove) DEFAULT=em: What to convert html <span> tags to
    --convert-quotes:     Convert quotes, i.e. convert "" to << >>
    --convert-hyphen:     Convert hyphens, i.e. - to ndash
    --skip-images:        Skip images, i.e. if specified do NOT include images.
    --convert-images:     Always convert images to PNG
"""


import sys

import optionparse
import h2fb
try:
    #raise ImportError
    import compressedfile
    myfile_open = compressedfile.open_zipfile
except ImportError:
    myfile_open = open




def main(argv=None):
    if argv is None:
        argv = sys.argv

    opt, args = optionparse.parse(__doc__, argv[1:])

    params = h2fb.default_params.copy()
    
    
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
    
    params['file-name'] = in_filename
    # Simply overwrite dictionary
    for temp_param in opt_dict:
        params[temp_param] = opt_dict[temp_param]
    
    params['detect-verses'] = 0 ## DEBUG, workaround for bug in detect-verses code (line length??), detect-verses makes NO sense for html input files, only makes sense for raw text files (h2fb can handle plain text files)
    params['skip-empty-lines'] = 0
    
    print 'Input file:', in_filename 
    print 'Output file:', out_filename

    # start actually processing the file now
    
    in_file = myfile_open(in_filename, 'rb')
    out_file = myfile_open(out_filename, 'w')
    
    input_text = in_file.read()
    if input_text.startswith('{\\rtf'):
        # Looks like we have RTF data not html!
        import rtf.Rtf2Html
        input_text = rtf.Rtf2Html.getHtml(input_text)
    
    params['data'] = input_text
    in_file.close()
    data=h2fb.MyHTMLParser().process(params)
    out_file.write(data)
    out_file.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())



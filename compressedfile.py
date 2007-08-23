"""Module to offer simple compressed file support by assuming the file 
in interest is contained in a zip file. Allows reading to a file,
or writing to a file (but not both and not appending).

Right now this module deals with real files on disk (it uses im memory
for performance for the intermediate files so there are no temporary
on-disk files). It does not support file objects as input. This is
next on the TODO list.

TODO consider support of different compress and archive formats:
    .Z
    .gz
    .tar
    .tgz
    tar.gz
    tar.z


    import gzip
    text_file_object = open(text_filename + '.gz', 'wb')
    gzip_fileptr = gzip.GzipFile(os.path.basename(text_filename), fileobj=text_file_object)
    return gzip_fileptr

"""

try:
    #raise ImportError
    import cStringIO as StringIO
except ImportError:
    import StringIO

import os
import time
import zipfile



def ro_open_zipfile(file_name, read_mode=None, extension_of_interest=None):
    """Read only open of either a text file or a zip file and returns regular file object
    if opening a zip file, opens the first file that ends with: extension_of_interest
    e.g. extension_of_interest='.txt'
    e.g. extension_of_interest='.rtf'
    
    if file is a zip file the contents are read in binary mode (under Windows)
    
    file_name is used pretty much as-is so recommend using ASCII filenames and not latin1, Unicode (utf16) or bytes containing utf-8
    
    TODO consider allowing extension_of_interest to be either a 
    single string or a list/tuple/etc. of strings, 
    e.g. ['*.html', '*.htm']"""
    
    if read_mode is None:
        read_mode='rb'
    if not read_mode.startswith('r'):
        raise(NotImplementedError, 'only support reading files')
    
    file_ptr = None
    if not file_name.lower().endswith('.zip'):
        # assume this is a raw file
        try:
            file_ptr = open(file_name, read_mode)
        except IOError, info:
            if info.errno == 2:
                # [Errno 2] No such file or directory
                file_name = file_name + '.zip' # ignoring upper case,
    
    if file_ptr is None:
        # this is a zip file
        zipfile_ptr = zipfile.ZipFile(file_name, 'r') # 'r' is binary for ZipFile
        
        textfile_name=None
        if extension_of_interest is None:
            # find the first file in the zip file and use that
            textfile_name=zipfile_ptr.namelist()[0]
        else:
            f_ext = extension_of_interest.lower()
            # find first f_ext file
            for name in zipfile_ptr.namelist():
                if name.lower().endswith(f_ext):
                    textfile_name = name
                    break
        file_ptr = StringIO.StringIO(zipfile_ptr.read(textfile_name))
    return file_ptr


class ZipFileWrapper:
    def __init__(self, zipfileptr, zipinfo):
        self._zipfileptr = zipfileptr
        self._zipinfo = zipinfo
        self._fileptr = StringIO.StringIO()
    
    def __getattr__(self, attr):
        if self.__dict__.has_key(attr):
            return self.__dict__[attr]
        else:
            return getattr(self._fileptr, attr)
            
    def close(self, *args, **kwargs):
        self._zipfileptr.writestr(self._zipinfo, self._fileptr.getvalue())
        self._zipfileptr.close()
        self._fileptr.close()
        ## TODO disallow more writes/closes....



def wo_open_zipfile(file_name, write_mode=None):
    """Write only open of zip file where the returned file handle is
    to the file inside and returns regular file object that can be written to
    
    file_name is used pretty much as-is so recommend using ASCII filenames and not latin1, Unicode (utf16) or bytes containing utf-8"""
    
    if write_mode is None:
        write_mode='wb'
    if not write_mode.startswith('w'):
        raise(NotImplementedError, 'only support writting new files')
    
    if not file_name.lower().endswith('.zip'):
        zipfile_name = file_name + '.zip'
        newfile_name_inzip = os.path.basename(file_name)
    else:
        zipfile_name = file_name
        newfile_name_inzip = os.path.splitext(os.path.basename(file_name))[0]
    
    now = time.localtime(time.time())[:6]
    myzipfile = zipfile.ZipFile(zipfile_name, "w")  # 'w' is binary for ZipFile
    info = zipfile.ZipInfo(newfile_name_inzip)
    info.date_time = now
    info.compress_type = zipfile.ZIP_DEFLATED
    return ZipFileWrapper(myzipfile, info)

def open_zipfile(name, mode=None):
    """Emulate stdlib open but using compressed files for input and output.
    Can open uncompressed files for reading as well as compressed.
    Opening files for write ALWAYS creates compressed files.
    
    Does not handle optional buffering argument"""
    if mode is None:
        mode='rb'
    if mode.startswith('r'):
        return ro_open_zipfile(name, mode)
    elif mode.startswith('w'):
        return wo_open_zipfile(name, mode)
    else:
        raise(NotImplementedError, 'unsupported file open mode')


if __name__ == '__main__':
    zipfile_name = "D:\\dloads\\usenet\\Pan\\onppc\\Foster,Alan Dean -11 Running From The Deity_txt.zip"
    #tempfile = ro_open_zipfile(zipfile_name, 'r')
    tempfile = ro_open_zipfile(zipfile_name, 'r', '.txt')
    
    bytes_to_read=10    
    data = tempfile.read(bytes_to_read)
    print len(data), repr(data)
    print len(data), data
    tempfile.close()

    zipfile_name = "D:\\tmp\Deity.txt.zip"
    zipfile_name = "D:\\tmp\Deity.txt"
    tempfile = wo_open_zipfile(zipfile_name)
    tempfile.write('hello world.')
    tempfile.write('goodbye world')
    tempfile.close()
    #tempfile.close() ## bad! we closed this already :-)
    #tempfile.write("I'm zipped!")  ## bad! we closed this already :-)

    tempfile=open_zipfile(zipfile_name, 'w')
    tempfile.write("I'm zipped!")
    tempfile.close()

    tempfile=open_zipfile(zipfile_name)
    print tempfile.read()
    tempfile.close()


# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import re
import unittest

import h2fb


## TODO need a way to ignore autho VERION in for when it changes
## need to test <empty-line/>, and add support for it in to h2fb!

in_filename = 'in_memory.html'
test_params = h2fb.default_params.copy()
test_params['file-name'] = in_filename
test_params['verbose'] = 0
test_params['convert-images'] = 0


def word_list_from_markup(in_str):
    compile_obj = re.compile(r"""(?is)<.*?>""")
    return_list = compile_obj.subn('', in_str)[0].replace('<', ' <').replace('>', '> ').split()
    ## debug
    #temp_str = compile_obj.subn('', in_str)[0]
    #return_list = temp_str .replace('<', ' <').replace('>', '> ').split()
    return return_list

def extract_body_from_markup(in_str):
    compile_obj = re.compile(r"""<body>(?P<bodycontents>.*)</body>""",  re.IGNORECASE| re.DOTALL)
    match_obj = compile_obj.search(in_str)
    bodycontents = match_obj.group('bodycontents')
    return bodycontents
    
class TestH2FB(unittest.TestCase):
    def assertTextContentEqual(self, str1, str2):
        """simple/dumb remove markup and compare 2 strings ignoring whitespace
        """
        str1_list=word_list_from_markup(str1)
        str2_list=word_list_from_markup(str2)
        #compile_obj = re.compile(r"""(?is)<.*?>""")
        #compile_obj = re.compile(r"""<.*>""")
        #compile_obj = re.compile(r"""<.*?>""")
        #str2_list=compile_obj.subn('', str2)[0].replace('<', ' <').replace('>', '> ').split()
        self.assertEqual(str1_list, str2_list)
    #def setUp(self):

    def test_blank_lines_br_only(self):
        """test_blank_lines_br_only: check if <empty-line/> is ever used
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        local_test_params['skip-empty-lines'] = 0
        in_data = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Strict//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
</head>
<body>
line number one.<br>
line number two.<br>
line number three.<br>
<br>
line number four, blank line above.<br>
</body>
</html>

'''
        expected_result = """
<body><section><p>
line number one.
</p>
<p>
line number two.
</p>
<p>
line number three.
</p>
<empty-line/>
<p>
line number four, blank line above.
</p></section></body>
        """
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        self.assertTrue('<empty-line' in data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))
        self.assertTextContentEqual(expected_result, extract_body_from_markup(data))
        
    def test_blank_lines_with_p(self):
        """test_blank_lines_with_p: check if <empty-line/> is ever used
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        local_test_params['skip-empty-lines'] = 0
        in_data = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Strict//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
</head>
<body>
<p>paragraph number one.</p>
<p>paragraph number two.</p>
<p>paragraph number three.</p>
<p>paragraph number three.</p>
<br>
<p>paragraph number four, blank line above.</p>
</body>
</html>

'''
        expected_result = """
<body><section><p>
paragraph number one.
</p>
<p>
paragraph number two.
</p>
<p>
paragraph number three.
</p>
<p>
paragraph number three.
</p>
<empty-line/>
<p>
paragraph number four, blank line above.
</p></section></body>
        """
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        self.assertTrue('<empty-line' in data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))
        self.assertTextContentEqual(expected_result, extract_body_from_markup(data))

    def test_incorrect_loss_of_data(self):
        """test_incorrect_loss_of_data: Regression test. Odd bug where detect-verses (in html input) loses data!
        NOTE I'm beginning to wonder if the detect-? code is for text files ONLY?
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        in_data = '''<h1>
  detect verse bug
</h1>

<p>
this line nneeds to be seventy two characters long so here is some data
this line s only fifty eight chars linemlkjjkhkjhkhjhkjhk
where as this line is seventy characters long, in comparison to above
START of a  72 length line, this is a 71 length line, is a 72 lengthEND
START of a  71 length line, this is a 71 length line, is a 71 lengthEND
This 40 charac length line will vanish!
</p>
<p>
The cat sat on the mat chewing on someones head
</p>

'''
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        #self.assert_('This 40 charac length line will vanish!' in data)
        self.assertTrue('This 40 charac length line will vanish!' in data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))

    def test_incorrect_loss_of_data_text(self):
        """test_incorrect_loss_of_data_text: Regression test. Odd bug where detect-verses (in html input) loses data!
        NOTE I'm beginning to wonder if the detect-? code is for text files ONLY?
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        in_data = '''
  detect verse bug


this line nneeds to be seventy two characters long so here is some data
this line s only fifty eight chars linemlkjjkhkjhkhjhkjhk
where as this line is seventy characters long, in comparison to above
START of a  72 length line, this is a 71 length line, is a 72 lengthEND
START of a  71 length line, this is a 71 length line, is a 71 lengthEND
This 40 charac length line will vanish!

The cat sat on the mat chewing on someones head

'''
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        #self.assert_('This 40 charac length line will vanish!' in data)
        self.assertTrue('This 40 charac length line will vanish!' in data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))

    def test_incorrect_loss_of_data_no_detect(self):
        """test_incorrect_loss_of_data_no_detect: Regression test. Odd bug where detect-verses (in html input) loses data!
        NOTE I'm beginning to wonder if the detect-? code is for text files ONLY?
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 0
        in_data = '''<h1>
  detect verse bug
</h1>

<p>
this line nneeds to be seventy two characters long so here is some data
this line s only fifty eight chars linemlkjjkhkjhkhjhkjhk
where as this line is seventy characters long, in comparison to above
START of a  72 length line, this is a 71 length line, is a 72 lengthEND
START of a  71 length line, this is a 71 length line, is a 71 lengthEND
This 40 charac length line will vanish!
</p>
<p>
The cat sat on the mat chewing on someones head
</p>

'''
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        #self.assert_('This 40 charac length line will vanish!' in data)
        self.assertTrue('This 40 charac length line will vanish!' in data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))


if __name__ == '__main__':
    unittest.main()

# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import string
import re
import unittest

import h2fb


## TODO add test for <p> inside <a> tages as hrefs/xlinks do NOT seem to work

in_filename = 'in_memory.html'
test_params = h2fb.default_params.copy()
test_params['file-name'] = in_filename
test_params['verbose'] = 0
test_params['convert-images'] = 0
test_params['encoding-to'] = 'us-ascii'
test_params['convert-span-to'] = 'em' # not sure if this should be global set or on per test basis...

#print 'test_params', test_params

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

##################
def dumb_html_diff(html_str1, html_str2):
    ## TODO consider changing white space handling- right now this is the original version
    def html2list(x, b=0):
        ## html2list from http://www.aaronsw.com/2002/diff/
        mode = 'char'
        cur = ''
        out = []
        for c in x:
            if mode == 'tag':
                if c == '>': 
                    if b: cur += ']'
                    else: cur += c
                    out.append(cur); cur = ''; mode = 'char'
                else: cur += c
            elif mode == 'char':
                if c == '<': 
                    out.append(cur)
                    if b: cur = '['
                    else: cur = c
                    mode = 'tag'
                elif c in string.whitespace: out.append(cur+c); cur = ''
                else: cur += c
        out.append(cur)
        return filter(lambda x: x is not '', out)

    def remove_duplicate_white_space(in_list):
        temp_list = []
        last_was_white_space=False
        for x in in_list:
            if x.isspace():
                if last_was_white_space:
                    continue
                else:
                    temp_list.append(x)
                    last_was_white_space=True
            else:
                temp_list.append(x)
                last_was_white_space=False
        return temp_list

    def remove_all_white_space(in_list):
        """This is so simple, should really use filter() for performance"""
        temp_list = []
        for x in in_list:
            if x.isspace():
                continue
            else:
                temp_list.append(x)
        return temp_list
    
    l1 = html2list(html_str1)
    l2 = html2list(html_str2)

    l1 = remove_all_white_space(l1)
    l2 = remove_all_white_space(l2)
        
    return l1 == l2

#########################################################

class TestH2FBUtil(unittest.TestCase):
    
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

    def assertMLContentEqual(self, str1, str2):
        """simple/dumb compare 2 strings containing ML (xml or html)
        does not handle complx cases such as "<some_tab />"
        """
        dummy_var = dumb_html_diff(str1, str2)
        self.assertEqual(dummy_var, True)

class TestH2FB(TestH2FBUtil):

    def test_span_replacement(self):
        """test_span_replacement: check if <span> tags are highlighted
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
I'm <span>not</span> happy about this <span class="bold">arrangment</span><br>
</body>
</html>

'''
        expected_result = """
<body><section><p>
I'm <emphasis>not</emphasis> happy about this <emphasis>arrangment</emphasis>
</p>
</section></body>
"""
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))
        self.assertTextContentEqual(expected_result, extract_body_from_markup(data))
        
    def test_escaped_data_1(self):
        """test_escaped_data_1: check if &#...... works
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        local_test_params['skip-empty-lines'] = 0
        in_data = '''<html>
    <body>
 
        <p>&#8220;Quoted.&#8221; Fred&#8217;s car.</p>
 
    </body>
</html>
'''
        in_data = '''<html>
    <body>
    
        <h2>decimal escape 1 (under (255)</h2>
        <p>
        extravagant d&#233;cor (hex 0x00e9)
        </p>
        
        <h2>named escape</h2>
        <p>&ldquo;Quoted.&rdquo; Fred&rsquo;s car.</p>
        
        <h2>decimal escape 2 (over 255)</h2>
        <p>&#8220;Quoted.&#8221; Fred&#8217;s car.</p>
 
    </body>
</html>
'''

        expected_result = """<body><section>
<title>
<p>
decimal escape 1 (under (255)
</p>
</title>
<empty-line/>
<p>
extravagant d&#233;cor (hex 0x00e9)
</p>
</section>
<section>
<title>
<p>
named escape
</p>
</title>
<empty-line/>
<p>
&#8220;Quoted.&#8221; Fred&#8217;s car.
</p>
</section>
<section>
<title>
<p>
decimal escape 2 (over 255)
</p>
</title>
<empty-line/>
<p>
&#8220;Quoted.&#8221; Fred&#8217;s car.
</p></section></body>
        """
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        self.assertTextContentEqual(expected_result, extract_body_from_markup(data))
        
        
    def test_escaped_data_2(self):
        """test_escaped_data_2: check if &#x...... works, currently FAILS :-(
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        local_test_params['skip-empty-lines'] = 0
        in_data = '''<html>
    <body>
    
         <h2>hex escape</h2>
         
        <p>
        extravagant d&#x00e9;cor
        </p>
        
        <p>&#x201c;Quoted.&#x201d; Fred&#x2019;s car.</p>
 
 <h2>information</h2>
 <br>
 <br>
 LEFT DOUBLE QUOTATION MARK
 decimal: &#8220;
 http://www.eki.ee/letter/chardata.cgi?ucode=201c
 
 
 RIGHT DOUBLE QUOTATION MARK
 decimal: &#8221;
 http://www.eki.ee/letter/chardata.cgi?ucode=201d

RIGHT SINGLE QUOTATION MARK
decimal: &#8217;
http://www.eki.ee/letter/chardata.cgi?ucode=2019

 
    </body>
</html>
'''

        expected_result = """not written yet as h2fb does not yet support hex escaped literals
        """
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
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
        
    def test_nested_emphasis_bold_simple(self):
        """test_nested_emphasis: check if <b><b>this is bold</b></b> is handled (i.e. reduced into one tag)
        TODO <b><b>this is bold</b> as is this</b>
        """
        local_test_params = test_params.copy()
        in_data = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Strict//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
</head>
<body>
<p>
<b><b>this is bold</b></b>
</p>
</body>
</html>

'''
        expected_result = """
<section><p>
<strong>this is bold</strong>
</p></section>        
        """
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        #print '-'*65
        #print extract_body_from_markup(data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))
        self.assertMLContentEqual(expected_result, extract_body_from_markup(data))

    def test_nested_emphasis_italic_simple(self):
        """test_nested_emphasis: check if <i><i>this is italic</i></i> is handled (i.e. reduced into one tag)
        TODO <i><i>this is italic</i> as is this</i>
        """
        local_test_params = test_params.copy()
        in_data = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Strict//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
</head>
<body>
<p>
<i><i>this is italic</i></i>
</p>
</body>
</html>

'''
        expected_result = """
<section><p>
<emphasis>this is italic</emphasis>
</p></section>        
        """
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        #print '-'*65
        #print extract_body_from_markup(data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))
        self.assertMLContentEqual(expected_result, extract_body_from_markup(data))

    def test_nested_emphasis_italic_lesssimple(self):
        """test_nested_emphasis: check if <i><i>this is italic</i> as is this</i> is handled (i.e. reduced into one tag)
        """
        local_test_params = test_params.copy()
        in_data = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Strict//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
</head>
<body>
<p>two italic nested tags
<i><i>this is italic</i> as is this</i>
</p>
</body>
</html>

'''
        expected_result = """
<section><p>
two italic nested tags
<emphasis>this is italic as is this</emphasis>
</p></section>        
        """ ## matches webbrowser behaviour of Firefox and IE
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        #print '-'*65
        #print extract_body_from_markup(data)
        self.assertTextContentEqual(in_data, extract_body_from_markup(data))
        self.assertMLContentEqual(expected_result, extract_body_from_markup(data))

        
    def test_avoid_duplicate_tags(self):
        """test_avoid_duplicate_tags: check handle embedded <p> inside <a>...</a>
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        local_test_params['skip-empty-lines'] = 0
        in_data = '''<html>
    <body>
        <a href="#someref1">
        <p>One line of text</p>
        </a>

        <a href="#someref2">
        <p>Another line of text</p>
        </a>
    </body>
</html>
'''
        expected_result = """<body><section><p>
One line of text
</p>
<p>
Another line of text
</p></section></body>
        """
        local_test_params['data'] = in_data
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
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

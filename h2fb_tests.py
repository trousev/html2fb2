# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import re
import unittest

import h2fb

in_filename = 'in_memory.html'
test_params = h2fb.default_params.copy()
test_params['file-name'] = in_filename
test_params['verbose'] = 0
test_params['convert-images'] = 0


class TestH2FB(unittest.TestCase):
    def assertTextContentEqual(self, str1, str2):
        """simple/dumb remove markup and compare 2 strings ignoring whitespace
        """
        compile_obj = re.compile(r"""<.*>""")
        str1_list=compile_obj.subn('', str1)[0].replace('<', ' <').replace('>', '> ').split()
        str2_list=compile_obj.subn('', str2)[0].replace('<', ' <').replace('>', '> ').split()
        self.assertEqual(str1_list, str2_list)
    #def setUp(self):

    def test_incorrect_loss_of_data(self):
        """Regression test. Odd bug where detect-verses (in html input) loses data!
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
        self.assertTextContentEqual(in_data, data)

    def test_incorrect_loss_of_data_no_detect(self):
        """Regression test. Odd bug where detect-verses (in html input) loses data!
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
        self.assertTextContentEqual(in_data, data)


if __name__ == '__main__':
    unittest.main()

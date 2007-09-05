# -*- coding: ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import sys
import unittest

import h2fb

in_filename = 'in_memory.html'
test_params = h2fb.default_params.copy()
test_params['file-name'] = in_filename
test_params['verbose'] = 0


class TestH2FB(unittest.TestCase):
    #def setUp(self):

    def test_incorrect_loss_of_data(self):
        """Regression test. Odd bug where detect-verses (in html input) loses data!
        NOTE I'm beginning to wonder if the detect-? code is for text files ONLY?
        """
        local_test_params = test_params.copy()
        local_test_params['detect-verses'] = 1
        local_test_params['data'] = '''<h1>
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
        data=h2fb.MyHTMLParser().process(local_test_params)
        #print data
        #self.assert_('This 40 charac length line will vanish!' in data)
        self.assertTrue('This 40 charac length line will vanish!' in data)


if __name__ == '__main__':
    unittest.main()

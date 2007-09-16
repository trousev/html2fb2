# -*- coding: latin-1 -*-
""" pyrtflib is a library to parse RTF. It is provided with two
examples that translate from RTF to raw text and to HTML.
Copyright (C) 2005 Loïc Fejoz

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

usage:

import rtf
rawString = rtf.getTxt(rtfString)
htmlString = rtf.getHtml(rtfString)
"""

import Rtf2Html
import Rtf2Txt

# get Html from a string that contain Rtf """
getHtml = Rtf2Html.getHtml


# get the Text from a string that contain Rtf """
getTxt = Rtf2Txt.getTxt

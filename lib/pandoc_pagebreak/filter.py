#!/usr/bin/env python
from pandocfilters import toJSONFilter, RawBlock
import re

"""
Pandoc filter to replace `<!-- break -->` with page break divs.

This is overkill - you can achieve the same thing purely in markdown
and css. However, using comments for page breaks makes them less
intrusive (e.g. they're not shown in github markdown renders.)
"""

def page_break(k,v,fmt,meta):
    if k == 'RawBlock':
        fmt, s = v
        if fmt == "html" and re.search("<!--\s*break\s*-->", s, re.IGNORECASE):
            return RawBlock('html', '</section><section style="page-break-before:always;">')

if __name__ == "__main__":
    toJSONFilter(page_break)

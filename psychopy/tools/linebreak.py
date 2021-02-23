#!/usr/bin/env python
# coding: utf-8

"""
Split string in accordance with UAX#14 Unicode line breaking.

Code is based on uniseg 0.7.1 (https://pypi.org/project/uniseg/)
"""


import sys
import os
import re
from unicodedata import east_asian_width
from psychopy.tools.linebreak_class import linebreak_class

__all__ = [
    'get_breakable_points',
    'break_units',
]

if sys.version_info >= (3, 0):
    from builtins import ord as _ord, chr as _chr
else:
    from __builtin__ import ord as _ord, unichr as _chr

if sys.maxunicode < 0x10000:
    # narrow unicode build
    rx_codepoints = re.compile(r'[\ud800-\udbff][\udc00-\udfff]|.', re.DOTALL)
    
    def code_point(s, index=0):
        
        L = rx_codepoints.findall(s)
        return L[index]
    
    def code_points(s):
        
        return rx_codepoints.findall(s)

else:
    # wide unicode build
    def code_point(s, index=0):
        return s[index or 0]
    
    def code_points(s):
        return list(s)

BK = 'BK'   # Mandatory Break
CR = 'CR'   # Carriage Return
LF = 'LF'   # Line Feed
CM = 'CM'   # Combining Mark
NL = 'NL'   # Next Line
SG = 'SG'   # Surrogate
WJ = 'WJ'   # Word Joiner
ZW = 'ZW'   # Zero Width Space
GL = 'GL'   # Non-breaking ("Glue")
SP = 'SP'   # Space
B2 = 'B2'   # Break Opportunity Before and After
BA = 'BA'   # Break After
BB = 'BB'   # Break Before
HY = 'HY'   # Hyphen
CB = 'CB'   # Contingent Break Opportunity
CL = 'CL'   # Close Punctuation
CP = 'CP'   # Close Parenthesis
EX = 'EX'   # Exclamation/Interrogation
IN = 'IN'   # Inseparable
NS = 'NS'   # Nonstarter
OP = 'OP'   # Open Punctuation
QU = 'QU'   # Quotation
IS = 'IS'   # Infix Numeric Separator
NU = 'NU'   # Numeric
PO = 'PO'   # Postfix Numeric
PR = 'PR'   # Prefix Numeric
SY = 'SY'   # Symbols Allowing Break After
AI = 'AI'   # Ambiguous (Alphabetic or Ideographic)
AL = 'AL'   # Alphabetic
CJ = 'CJ'   # Conditional Japanese Starter
H2 = 'H2'   # Hangul LV Syllable
H3 = 'H3'   # Hangul LVT Syllable
HL = 'HL'   # Hebrew Letter
ID = 'ID'   # Ideographic
JL = 'JL'   # Hangul L Jamo
JV = 'JV'   # Hangul V Jamo
JT = 'JT'   # Hangul T Jamo
RI = 'RI'   # Regional Indicator
SA = 'SA'   # Complex Context Dependent (South East Asian)
XX = 'XX'   # Unknown

"""
import sqlite3

dbpath = os.path.join(os.path.dirname(__file__), 'linebreaking_classes.sqlite3')
if not os.path.exists(dbpath):
    raise FileNotFoundError('{} is not found.'.format(dbpath))

_conn = sqlite3.connect(dbpath)

def _line_break(u):
    
    cur = _conn.cursor()
    cur.execute('select value from LineBreak where cp = ?', (ord(u),))
    for value, in cur:
        return str(value)
    return 'Other'

def line_break(c, index=0):
    return _line_break(code_point(c, index))
"""

def line_break(c, index=0):
    
    code = ord(code_point(c, index))
    if code in linebreak_class:
        return linebreak_class[code]
    return 'Other'

def break_units(s, breakables):
    i = 0
    for j, bk in enumerate(breakables):
        if bk:
            if j:
                yield s[i:j]
            i = j
    if s:
        yield s[i:]

def _preprocess_boundaries(s):
    prev_prop = None
    i = 0
    for c in code_points(s):
        prop = line_break(c)
        if prop in (BK, CR, LF, SP, NL, ZW):
            yield (i, prop)
            prev_prop = None
        elif prop == CM:
            if prev_prop is None:
                yield (i, prop)
                prev_prop = prop
        else:
            yield (i, prop)
            prev_prop = prop
        i += len(c)

def get_breakable_points(s, legacy=False):
    if not s:
        return
    
    primitive_boundaries = list(_preprocess_boundaries(s))
    prev_prev_lb = None
    prev_lb = None
    for i, (pos, lb) in enumerate(primitive_boundaries):
        next_pos, __ = (primitive_boundaries[i+1]
                        if i<len(primitive_boundaries)-1 else (len(s), None))
        
        if legacy:
            if lb == AL:
                cp = unichr(ord(s, pos))
                lb = ID if east_asian_width(cp) == 'A' else AL
            elif lb == AI:
                lb = ID
        else:
            if lb == AI:
                lb = AL
        
        if lb == CJ:
            lb = NS

        if lb in (CM, XX, SA):
            lb = AL
        # LB4
        if pos == 0:
            do_break = False
        elif prev_lb == BK:
            do_break = True
        # LB5
        elif prev_lb in (CR, LF, NL):
            do_break = not (prev_lb == CR and lb == LF)
        # LB6
        elif lb in (BK, CR, LF, NL):
            do_break = False
        # LB7
        elif lb in (SP, ZW):
            do_break = False
        # LB8
        elif ((prev_prev_lb == ZW and prev_lb == SP) or (prev_lb == ZW)):
            do_break = True
        # LB11
        elif lb == WJ or prev_lb == WJ:
            do_break = False
        # LB12
        elif prev_lb == GL:
            do_break = False
        # LB12a
        elif prev_lb not in (SP, BA, HY) and lb == GL:
            do_break = False
        # LB13
        elif lb in (CL, CP, EX, IS, SY):
            do_break = False
        # LB14
        elif (prev_prev_lb == OP and prev_lb == SP) or prev_lb == OP:
            do_break = False
        # LB15
        elif ((prev_prev_lb == QU and prev_lb == SP and lb == OP)
              or (prev_lb == QU and lb == OP)):
            do_break = False
        # LB16
        elif ((prev_prev_lb in (CL, CP) and prev_lb == SP and lb == NS)
              or (prev_lb in (CL, CP) and lb == NS)):
            do_break = False
        # LB17
        elif ((prev_prev_lb == B2 and prev_lb == SP and lb == B2)
              or (prev_lb == B2 and lb == B2)):
            do_break = False
        # LB18
        elif prev_lb == SP:
            do_break = True
        # LB19
        elif lb == QU or prev_lb == QU:
            do_break = False
        # LB20
        elif lb == CB or prev_lb == CB:
            do_break = True
        # LB21
        elif lb in (BA, HY, NS) or prev_lb == BB:
            do_break = False
        # LB22
        elif prev_lb in (AL, HL, ID, IN, NU) and lb == IN:
            do_break = False
        # LB23
        elif ((prev_lb == ID and lb == PO)
              or (prev_lb in (AL, HL) and lb == NU)
              or (prev_lb == NU and lb in (AL, HL))):
            do_break = False
        # LB24
        elif ((prev_lb == PR and lb == ID)
              or (prev_lb == PR and lb in (AL, HL))
              or (prev_lb == PO and lb in (AL, HL))):
            do_break = False
        # LB25
        elif ((prev_lb == CL and lb == PO)
              or (prev_lb == CP and lb == PO)
              or (prev_lb == CL and lb == PR)
              or (prev_lb == CP and lb == PR)
              or (prev_lb == NU and lb == PO)
              or (prev_lb == NU and lb == PR)
              or (prev_lb == PO and lb == OP)
              or (prev_lb == PO and lb == NU)
              or (prev_lb == PR and lb == OP)
              or (prev_lb == PR and lb == NU)
              or (prev_lb == HY and lb == NU)
              or (prev_lb == IS and lb == NU)
              or (prev_lb == NU and lb == NU)
              or (prev_lb == SY and lb == NU)):
            do_break = False
        # LB26
        elif ((prev_lb == JL and lb in (JL, JV, H2, H3))
              or (prev_lb in (JV, H2) and lb in (JV, JT))
              or (prev_lb in (JT, H3) and lb == JT)):
            do_break = False
        # LB27
        elif ((prev_lb in (JL, JV, JT, H2, H3) and lb in (IN, PO))
              or (prev_lb == PR and lb in (JL, JV, JT, H2, H3))):
            do_break = False
        # LB28
        elif prev_lb in (AL, HL) and lb in (AL, HL):
            do_break = False
        # LB29
        elif prev_lb == IS and lb in (AL, HL):
            do_break = False
        # LB30
        elif ((prev_lb in (AL, HL, NU) and lb == OP)
              or (prev_lb == CP and lb in (AL, HL, NU))):
            do_break = False
        # LB30a
        elif prev_lb == lb == RI:
            do_break = False
        else:
            do_break = True
        for j in range(next_pos-pos):
            yield int(j==0 and do_break)
        prev_prev_lb = prev_lb
        prev_lb = lb



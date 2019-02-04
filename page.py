#!/usr/bin/env python

import sys, os
import numpy as np

from util import subcode_bcd, mrag, page
from printer import Printer, do_print

class Page(object):
    rows = np.array([0, 27, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    def __init__(self, a):
        
        self.array = a.reshape((26,42))
        #do_print(self.array[0])
        ((self.m,self.r),e) = mrag(self.array[0][:2])
        (self.p,e) = page(self.array[0][2:4])
        (self.s,self.c),self.e = subcode_bcd(self.array[0][4:10])

        # remove parity
        self.array[2:,2:] &= 0x7f

        # check if row n-1 is double height
        self.no_double_on_prev = ((self.array[1:-1,2:]) != 0x0d).all(axis=1)
        # row 1 can't contain double but might due to not being printable
        self.no_double_on_prev[0] = True

        # calculate a target threshold for each line
        # based on the number of non-blank characters

        # first count non-blanks
        self.threshold = ((self.array[2:,2:] != ord(' ')).sum(axis=1))

        # if non-blanks <= 5, don't require a match (set threshold to 0)
        # also ignore rows following a double height row
        self.threshold *= ((self.threshold > 5) & (self.no_double_on_prev))

        # some proportion of non-blanks must match in the rest of the lines
        self.threshold /= 2

        # sum required threshold for each line to get total threshold
        self.threshold_sum = self.threshold.sum() * 1.5

        try:
            self.ds = int("%x" % self.s, 10)
        except ValueError:
            self.ds = 1000
        rows = np.array([mrag(self.array[n][:2])[0][1] for n in range(26)])
        self.goodrows = (rows == Page.rows)

    def hamming(self, other):
        # compute the similarity/difference between two subpages
        # if similar enough to squash them into a single subpage, return true
        # note: no point checking rows 0 and 1. they will always match for 
        # all subpages.

        h = ((self.array[2:] != ord(' ')) & (self.array[2:] == other.array[2:])).sum(axis=1)
        return ((h >= self.threshold)).all() and h.sum() >= self.threshold_sum
        #return h.sum() < 200

    def to_html(self, anchor):
        body = []

        p = Printer(self.array[0][10:])
        p.anchor = anchor
        line = '   <span class="pgnum">P%d%02x</span> ' % (self.m,self.p) + p.string_html()
        body.append(line)

        i = 2
        for i in range(2,26):
          if self.no_double_on_prev[i-2]:
            p = Printer(self.array[i][2:])
            if i == 25 and self.rows[1] == 27:
                p.set_fasttext(self.array[1], self.m)
            body.append(p.string_html())
            # skip a line if this packet contained double height chars

        head = '<div class="subpage" id="%d">' % self.s

        return head + "".join(body) + '</div>'

    def to_str(self):
        return "".join([chr(x) for x in self.array.reshape((42*26))])
    
    def to_binary(self):
        return "".join(['{0:08b}'.format(x) for x in self.array.reshape((42*26))])

    def to_base64url(self):
        #print self.array.shape
        # Chop the MRAG off from the data
        noMrag = self.array[0:26,2:]
        noMrag[0, :8] = 32
        visible = np.delete(noMrag, 1, 0)
        #print visible.shape
        #print "".join('{0:08b}'.format(63)[1:])
        #binary += ('{0:08b}'.format(x)[1:] for x in self.array[2:26][2:])
        binary = "".join('{0:08b}'.format(x)[1:] for x in visible.reshape(1000))
        binary += "00"
        
        #print "binary Length:%d\n" % len(binary)
        encoded = "<a href='https://teletextarchaeologist.org/editor/#0:"
        # Loop 5-bit segments
        for n in range(len(binary) / 6):
            # Get substring
            segment = binary[n*6:(n*6)+6]
            index = int(segment, 2)
            encoded += "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"[index]
        encoded += "' target='_blank'>" + "%d%02x" % (self.m, self.p) + "</a>\n"
        return encoded

    def to_c64teletext(self):
        # Chop the MRAG off from the data
        noMrag = self.array[0:26,2:]
        visible = np.delete(noMrag, 1, 0)
        noheader = np.delete(visible, 0, 0)
        
        c64Out = "".join([chr(x) for x in noheader.reshape((40*24))])
        c64Out = c64Out.join('0x00')
        
        return c64Out

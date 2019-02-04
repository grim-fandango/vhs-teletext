#!/usr/bin/env python

import sys, os
import numpy as np

from util import subcode_bcd, mrag, page, bitwise_mode
from printer import Printer, do_print
from page import Page
from fragment import fragments

class Squasher(object):
    def __init__(self, filename):
        data = file(filename, 'rb')
        self.pages = []
        self.page_count = 0
        print filename,
        done = False
        while not done:
            p = data.read(42*26)
            if len(p) < (42*26):
                done = True
            else:
                p = Page(np.fromstring(p, dtype=np.uint8))
                for flist in fragments:
                    tmp = [(f.test(p),n,f) for n,f in enumerate(flist)]
                    ans = max(tmp)
                    if ans[0] > 0:
                        ans[2].fix(p)
                self.pages.append(p)
                self.page_count += 1
        print "%5d" % self.page_count,

        self.subcodes = self.guess_subcodes()
        self.subcode_count = len(self.subcodes)

        self.m = self.pages[0].m
        self.p = self.pages[0].p


        for i in range(3):
         unique_pages = self.hamming()
         squashed_pages = []
         for pl in unique_pages:
             page = Page(self.squash(pl))
             squashed_pages += [page]*len(pl)
         self.pages = squashed_pages

        unique_pages = self.hamming()
        squashed_pages = []
        for pl in unique_pages:
          if len(pl) > 1 or len(unique_pages) == 1:
            squashed_pages += [Page(self.squash(pl))]
            
        if nosquash == 'nosquash' or (nosquash == 'nosquash777' and self.m == 7 and self.p == 0x77): 
            squashed_pages = self.pages
           
        # sort it
        sorttmp = [(p.s, p) for p in squashed_pages]
        sorttmp.sort()
        squashed_pages = [p[1] for p in sorttmp]
        self.squashed_pages = squashed_pages

        print "%3d" % self.subcode_count, "%3d" % len(squashed_pages), "%3d" % len(unique_pages)

    def guess_subcodes(self):
        subpages = [x.ds for x in self.pages if x.ds < 0x100]
        us = set(subpages)
        sc = [(s,subpages.count(s)) for s in us]
        sc.sort()

        if len(sc) < 2:
          return sc
        else:
          if sc[0][0] == 0 and sc[0][1] > (len(subpages)*0.8):
            good = [0]
          else:
            good = []
            bad = []
            for n in range(len(sc)):
                if sc[n][0] == n+1:
                    good.append(sc[n][0])
                else:
                    bad.append(sc[n][0])

        return good

    def hamming(self):
        unique_pages = []
        unique_pages.append([self.pages[0]])

        for p in self.pages[1:]:
            matched = False
            for op in unique_pages:
                if p.hamming(op[0]):
                    op.append(p)
                    matched = True
                    break
            if not matched:
                unique_pages.append([p])

        sorttmp = [(len(u),u) for u in unique_pages]
        sorttmp.sort(reverse=True)
        unique_pages = [x[1] for x in sorttmp]

        #if len(unique_pages) > self.subcode_count:
        #    unique_pages = unique_pages[:self.subcode_count]
        self.print_this = (len(unique_pages) != self.subcode_count)

        return unique_pages

    def squash(self, pages):
        return bitwise_mode([x.array for x in pages])

    def to_str(self):
        return "".join([p.to_str() for p in self.squashed_pages])

    def to_html(self):
        header = """<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Page %d%02x</title><link rel="stylesheet" type="text/css" href="teletext.css" /></head>
<body><pre>""" % (self.m, self.p)
        body = "".join([p.to_html("#%d" % n) for n,p in enumerate(self.squashed_pages)])
        footer = "</body>"
        
        htmlOut.write("<a href='%d%02x.html'>%d%02x</a><br />\n"  % (self.m, self.p, self.m, self.p))

        return header+body+footer

    def to_binary(self):
        return "".join([p.to_str() for n,p in enumerate(self.squashed_pages)])
        
    def to_base64url(self):
        # Convert page to contiguous binary string
        #binary = "".join([p.to_binary() for p in enumerate(self.squashed_pages)])

        url = "".join([p.to_base64url() for n,p in enumerate(self.squashed_pages)])
        
        #print "\n%s\n" % (url)
            
        return url
        
    def to_c64teletext(self):
        out = "".join([p.to_c64teletext() for p in self.squashed_pages])
        return out

def main_work_subdirs(gl):
    for root, dirs, files in os.walk(gl['pwd']):
        dirs.sort()
        if root == gl['pwd']:
            for d2i in dirs:
                print(d2i)

if __name__=='__main__':
    indir = sys.argv[1] + '/pages'
    outdir = sys.argv[1] + '/html'
    try:
      nosquash = sys.argv[2]
    except IndexError:
      nosquash = ''    
    try:
      bindir = sys.argv[1] + '/binaries'
    except IndexError:
      bindir=''


    outpath = os.path.join('.', outdir)
    binpath = os.path.join('.', bindir)

    if not os.path.isdir(outpath):
        os.makedirs(outpath)
    if not os.path.isdir(binpath):
        os.makedirs(binpath)

    base64Out = file(os.path.join(outpath, "index.html"), 'w')
    base64Out.write("<!DOCTYPE html><html><head><meta http-equiv='Content-Type' content='text/html;charset=utf-8' /><script type='text/javascript' src='https://teletextarchaeologist.org/editor/teletext-editor.js'></script><script type='text/javascript'>        function init_frames() {            // Create a new editor:\n          var editor = new Editor();            // Make it the active editor so it receives keypresses:\n          active_editor = editor;            // Initialise the editor, placing it in the canvas with HTML\n            // ID 'frame'.\n          editor.init_frame('frame');            // Set the user page entry offset\n            editor._viewer_setuserpageoffset(3);            // Set the time display offset and format\n            editor._viewer_settimeformat(32, 'h:m/s');            // Load all pages from this html page\n            editor._viewer_loadpages();        }        </script>        <title>teletext-editor</title>        <style type='text/css'>a:link{color: white} a:visited{color: white}        body {             background-color: #111;        }        canvas {            /* The canvas should have no padding */            background-color: #000;            z-index: 1;            border: 10px solid black;            border-radius: 5px;                        /* Centre the canvas on the page */	            position:relative;          margin: auto;            position: absolute;          left:0;          right: 0;          top: 0;          bottom: 0;        }        </style>        </head>        <body onload='init_frames();'>        <canvas id='frame'></canvas>        <div style='display: none;'>")
    
    htmlOut = file(os.path.join(outpath, "index.htm"), 'w')
    htmlOut.write("<!DOCTYPE html><html><head><meta http-equiv='Content-Type' content='text/html;charset=utf-8'></head><body><div style='font-family: Helvetica, Arial, sans-serif; text-align: left;'><h1>Service, Date</h1>")

    
    for root, dirs, files in os.walk(indir):
        dirs.sort()
        files.sort()
        for f in files:
            s = Squasher(os.path.join('.', root, f))
            m = s.m
            if m == 0:
                m = 8
            outfile = "%d%02x.html" % (m, s.p)
            of = file(os.path.join(outpath, outfile), 'wb')
            of.write(s.to_html())
            if bindir != '':
                binoutfile = "%d%02x.bin" % (m, s.p)
                binfile = file(os.path.join(binpath, binoutfile), 'wb')
                binfile.write(s.to_binary())
                
                #c64file = file(os.path.join(binpath, "%d%02x-01.prg" % (m, s.p)), 'wb')
                #c64file.write(s.to_c64teletext())
            #print "\n%s\n" % (s.to_base64url())   
            base64Out.write("\n%s\n<br />" % (s.to_base64url()))
    
    htmlOut.write("</div></body></html>")
    htmlOut.close()
    
    base64Out.write("</div><div style='color: white; font-family: Helvetica, Arial, sans-serif; text-align: center; font-size: 80%;'><h1>Teletext Viewer - [Service] [Date]</h1><p>Teletext data is recovered from videotape by <a href='https://twitter.com/grim_fandango'>Jason Robertson (@grim_fandango)</a>, using Alistair Buxton's <a href='https://github.com/ali1234/vhs-teletext'>VHS-Teletext</a> with additional functionality by Jason Robertson. <br/><br/>Viewer is Simon Rawles' <a href='https://github.com/rawles/teletext-editor'>Teletext Editor</a> tailored for viewing by <a href='https://twitter.com/adamdawes575'>Adam Dawes (@adamdawes575)</a><p>Usage: type the page number you want using the number keys.  Use cursor keys left/right to move through the sub-pages; use cursor keys up/down to move to the next available page.</p></div></body></html>")
    base64Out.close()
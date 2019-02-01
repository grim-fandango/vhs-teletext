import re

from teletext.misc.all import All

class PrinterANSI(object):

    def __init__(self, tt, colour=True, codepage=0):
        self.tt = tt&0x7f
        self.fg = 7
        self.bg = 0
        self.mosaic = False
        self.solid = True
        self.double = True if 0x0d in tt else False
        self.flash = False
        self.conceal = False
        self.boxed = False
        self.flinkopen = False
        # ignored for now
        self.codepage = codepage

        # anchor for header links so we can bookmark a subpage
        self.anchor = ""

        self.colour = colour


    def ttchar(self, c):
        if self.mosaic and (c < ord('@') or c > ord('_')):
            return chr(c+0xee00) if self.solid else chr(c+0xede0)
        else:
            if c == ord('#'):
                return chr(0xa3) # pound sign
            elif c == ord('_'):
                return chr(ord('#'))
            elif c == ord('`'):
                return chr(0x2014) # em dash
            elif c == ord('~'):
                return chr(0xf7) # division symbol
            elif c == 0x7f:
                return chr(0xe65f) # rectangle
            else:
                return chr(c)


    def setstyle(self, fg=None, bg=None):
        if self.colour:
            return '\033[3%dm\033[4%dm' % ((fg or self.fg), (bg or self.bg))
        else:
            return ''


    def transform(self, c):
        h = c&0xf0
        l = c&0x0f
        if h == 0x0:
            if l < 8:
                self.fg = l
                self.conceal = False
                self.mosaic = False
                ret = ' '+self.setstyle()
            elif l == 0x8: # flashing
                self.flash = True
                ret = ' '+self.setstyle()
            elif l == 0x9: # steady
                self.flash = False
                ret = ' '+self.setstyle()
            elif l == 0xa: # flashing
                self.boxed = True
                ret = ' '+self.setstyle()
            elif l == 0xb: # steady
                self.boxed = False
                ret = ' '+self.setstyle()
            else:
                ret = ' '
                #print hex(int(c&0xff))
        elif h == 0x10:
            if l < 8:
                self.fg = l
                self.conceal = False
                self.mosaic = True
                self.solid = True
                ret = ' '+self.setstyle()
            elif l == 0x8: # conceal
                self.conceal = True
                ret = ' '+self.setstyle()
            elif l == 0x9:
                self.solid = True
                ret = ' '
            elif l == 0xa:
                self.solid = False
                ret = ' '
            elif l == 0xc:
                self.bg = 0
                ret = self.setstyle()+' '
            elif l == 0xd:
                self.bg = self.fg
                ret = self.setstyle()+' '
            else:
                ret = ' '
                #print hex(int(c&0xff))
        else:
            ret = self.ttchar(c)

        return ret


    def __str__(self):
        head = self.setstyle(fg=7, bg=0)
        body = "".join([self.transform(x) for x in self.tt])
        return head+body+('\033[0m' if self.colour else '')



class PrinterHTML(PrinterANSI):

    def __init__(self, tt, codepage=0, pages_set=All):
        PrinterANSI.__init__(self, tt, colour=False, codepage=codepage)
        self.fastext = False
        self.pages_set = pages_set

    def ttchar(self, c):
        if self.mosaic:
            return PrinterANSI.ttchar(self, c)
        elif c == ord('<'):
            return '&lt;'
        elif c == ord('>'):
            return '&gt;'
        else:
            return PrinterANSI.ttchar(self, c)


    def htmlspanstyle(self, fg=None, bg=None):
        return '<span class="f%d b%d%s%s%s%s">' % ((fg or self.fg), (bg or self.bg), 
                      (" dh" if self.double else ""), (" fl" if self.flash else ""),
                      (" cn" if self.conceal else ""), (" bx" if self.boxed else " nx"))


    def setstyle(self, fg=None, bg=None):
        link = ''
        linkclose = ''
        if self.fastext:
            if self.flinkopen:
                linkclose = '</a>'
                self.flinkopen = False
            if self.fg in [1,2,3,6] and self.links[[1,2,3,6].index(self.fg)] in self.pages_set:
                link = '<a href="%s.html">' % self.links[[1,2,3,6].index(self.fg)]
                self.flinkopen = True

        return linkclose+'</span>'+self.htmlspanstyle()+link


    def linkify(self, html):
        e = '([^0-9])([0-9]{3})([^0-9]|$)'
        def repl(match):
            if match.group(2) in self.pages_set:
                return '%s<a href="%s.html%s">%s</a>%s' % (match.group(1), match.group(2), self.anchor, match.group(2), match.group(3))
            else:
                return '%s%s%s' % (match.group(1), match.group(2), match.group(3))
        p = re.compile(e)
        return p.sub(repl, html)


    def __str__(self):
        head = self.htmlspanstyle(fg=7, bg=0)
        body = "".join([self.transform(x) for x in self.tt])
        foot = '</span>'
        if self.fastext:
            if self.flinkopen:
                foot += '</a>'
        else:
            body = self.linkify(body)
        return head+body+foot+'\n'


def html():
    import sys
    import os

    from .pipeline import reader, make_service
    from .spellcheck import spellcheck

    def sciter(packet_iter):
        for packet in packet_iter:
            spellcheck(packet)
            yield packet

    service = make_service(sciter(reader(open(sys.argv[1]))))

    pages_set = service.pages_set()

    for magazineno, magazine in service.magazines.iteritems():
        for pageno, page in magazine.pages.iteritems():

            outfile = open(os.path.join(sys.argv[2], '%d%02X.html' % (magazineno, pageno)), 'w')

            outfile.write("""<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Page %d%02X</title>
    <link rel="stylesheet" type="text/css" href="teletext.css" title="Default Style"/>
    <link rel="alternative stylesheet" type="text/css" href="teletext-noscanlines.css" title="No Scanlines"/>
    <script type="text/javascript" src="cssswitch.js"></script>
    </head>
    <body onload="set_style_from_cookie()"><pre>""" % (magazineno, pageno))

            for subpageno, subpage in page.subpages.iteritems():
                outfile.write(
                    subpage.to_html(magazineno, pageno, subpageno, magazine.header(magazineno, subpage), pages_set))

            outfile.write("</pre></body>")

            outfile.close()

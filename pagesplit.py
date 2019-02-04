#!/usr/bin/env python

import sys, os
import numpy as np

from util import mrag, page
from finders import *
from printer import do_print

import config
import finders

import colorama
colorama.init()

import shutil

def do_raw(filename):
    
    try:
        filereader = open(filename, 'rb')
        f = filereader.read()
        filereader.close()

    except:
        return (0, 0, '')
    
    f1count = 0
    f2count = 0
    data = ''
    for l in range(len(f) / 42):
        print 'Line: %d\r' % l,
        sys.stdout.flush()
        offset = 42*l
        line = f[offset:offset+42]
        
        if line != "\xff"*42:
            data = data + line
            
            if l > 15:
                f2count += 1
            else:
                f1count += 1

    return (f1count, f2count, data)

class PageWriter(object):
    def __init__(self, outdir):
        self.outdir = outdir
        self.count = 1
        self.bad = 0

    def write_page(self, ps):
        if ps[0].me or ps[0].pe:
            self.bad += 1
        else:
            m = str(ps[0].m)
            p = '%02x' % ps[0].p
            path = os.path.join('.', self.outdir, m)
            if not os.path.isdir(path):
                os.makedirs(path)
            f = os.path.join(path, p)
            #print "Page Path: %s" % f
            of = file(f, 'ab')
            for p in ps:
                of.write(p.tt)
            of.close()
            if self.count % 50 == 0:
                print f, '- ',
                print do_print(np.fromstring(ps[0].tt, dtype=np.uint8)), "%4.1f" % (100.0*self.count/(self.count+self.bad))
            self.count += 1



class PacketHolder(object):

    sequence = 0

    def __init__(self, tt):

        self.sequence = PacketHolder.sequence
        PacketHolder.sequence += 1

        (self.m,self.r),e = mrag(np.fromstring(tt[:2], dtype=np.uint8))
        match = False
        F = finders.test(finders.all_headers, tt)
        if F:
            self.r = 0
            F.check_page_info()
            self.me = False #F.me
            self.pe = False #F.pe
            self.p = F.p
            match = True
                
        if not match and self.r == 0:
            self.r = -1
            self.m = -1
        self.tt = tt
        self.used = False



class NullHandler(object):
    def __init__(self):
        self.highest_packet = 100000000

    def add_packet(self, p):
        pass



class MagHandler(object):
    packet_order = [0, 27, 1, 2, 3, 4, 5, 6, 7, 8, 9, 
                    10, 11, 12, 13, 14, 15, 16, 17, 
                    18, 19, 20, 21, 22, 23, 24]
    pol = len(packet_order)

    def __init__(self, m, pagewriter):
        self.m = m
        self.packets = []
        self.seen_header = False
        self.pagewriter = pagewriter

    def good_page(self):
        self.pagewriter.write_page(self.packets)
        self.packets = []

    def bad_page(self):
        #print "\nBad Page %d" % (self.m)
        self.pagewriter.bad += 1
        self.packets = []

    def check_page1(self):
        if len(self.packets) >= MagHandler.pol:
            self.packets = self.packets[:MagHandler.pol]
            rows = [p.r for p in self.packets]
            c = [a1 == b1 for a1,b1 in zip(rows,MagHandler.packet_order)].count(True)
            if c >= (MagHandler.pol - 2): # flawless subpage
                self.good_page()
                return
                
        self.bad_page()

    def fill_missing(self):
        rows = [p.r for p in self.packets]
        ans = []
        for n in MagHandler.packet_order:
            try:
                ans.append(self.packets[rows.index(n)])
            except ValueError:
                ans.append(PacketHolder("\x00"*42))
        self.packets = ans

    def check_page(self):
        self.packets[0].good = True
        highgood = 0
        badcount = 0
        for n in range(1, len(self.packets)-1):
            a = (self.packets[n].ro - self.packets[n-1].ro)
            b = (self.packets[n+1].ro - self.packets[n].ro)
            c = (self.packets[n].r == MagHandler.packet_order[-1])
            if badcount < 20 and self.packets[n].ro > highgood and (c or a == 1 or b == 1 or (a > 0 and b > 0)):
                self.packets[n].good = True
                highgood = self.packets[n].ro
            else:
                self.packets[n].good = False
                badcount += 1
        self.packets[-1].good = self.packets[-1].ro > highgood
        
        self.packets = [p for p in self.packets if p.good]
        #A value of 0.25 below will pick up pages with only four packets
        if len(self.packets) > (MagHandler.pol*0.25):
            self.fill_missing()
            self.good_page()
        else:
            self.bad_page()

    def add_packet(self, p):
        if p.r == 0:
            if self.seen_header:
                self.check_page()
            else:
                self.bad_page()
            self.seen_header = True
        p.ro = MagHandler.packet_order.index(p.r)
        self.packets.append(p)



if __name__=='__main__':

    # Usage: pagesplit.py FolderOrFile [t42 file number to start from]

    packet_list = []
    
    if os.path.isdir(sys.argv[1]):
        t42path = sys.argv[1] + '\\t42'
        parentPath = sys.argv[1]
    else:
        t42path = os.path.abspath(os.path.join(sys.argv[1], os.pardir))
        parentPath = t42path
    
    w = PageWriter(parentPath +  '\\pages')
    
    mags = [MagHandler(n, w) if n in config.magazines else NullHandler() for n in range(8)]   
    
    of = file(os.path.join(parentPath, "PacketOrder.txt"), 'w')
    try:
        shutil.rmtree(parentPath + '/pages/')
    except:
        print "Unable to delete 'pages' folder\n"

        
    sys.stderr.write('parentpath = %s\n' % parentPath)
        
    if len(sys.argv) > 2:
        startT42 = int(sys.argv[2])
    else:
        startT42 = 0
    
    if os.path.isdir(sys.argv[1]):
        for i in range(startT42,100000):
        #for i in range(23000,23010):
            (a,b,f) = do_raw(t42path + '\\' + ('%08d.t42' % i))
            sys.stderr.write(t42path + '\\' + ('%08d.t42\t%d\t%d\n' % (i, a, b)))
            if b != -1:
        
                #try:
                for n in range(0,len(f)/42):
                    tt = f[n*42:(n*42)+42]
                    
                    if len(tt) == 42:
                        p = PacketHolder(tt)
                        if p.r in MagHandler.packet_order:
                            mags[p.m].add_packet(p)
                            
                            of.write("File: %s Magazine: %s Packet: %s\n" % (('%08d.t42' % i), p.m, p.r))
                            
            else:
                break
    else:
        (a,b,f) = do_raw(sys.argv[1])
        sys.stderr.write('%s\t%d\t%d\n' % (sys.argv[1], a, b))
        if b != -1:
            sys.stderr.write('b != -1')
            #try:
            for n in range(0,len(f)/42):
                tt = f[n*42:(n*42)+42]
                
                if len(tt) == 42:
                    p = PacketHolder(tt)
                    if p.r in MagHandler.packet_order:
                        mags[p.m].add_packet(p)
                        
                        of.write("File: %s Magazine: %s Packet: %s\n" % (sys.argv[1], p.m, p.r))
        
    of.close()



    #while(True):
    #    tt = sys.stdin.read(42)
    #    if len(tt) < 42:
    #        exit(0)
    
    #    p = PacketHolder(tt)
    #    if p.r in MagHandler.packet_order:
    #        mags[p.m].add_packet(p)


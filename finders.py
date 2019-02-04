#!/usr/bin/env python

# * Copyright 2011 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

import sys
import numpy as np

from util import *

class Finder(object):
    def __init__(self, match1, match2, name="", row=-1):
        self.match1 = np.fromstring(match1, dtype = np.uint8)
        self.match2 = np.fromstring(match2, dtype = np.uint8)
        self.passrank = (5+self.calculaterank(self.match1))*0.5
        try:
            self.pagepos = match2.index('m')
        except ValueError:
            self.pagepos = -1
        self.row = row
        self.possible_bytes = []
        self.name = name

        for n in range(42):
            c = self.match2[n]
            if c == ord('e'):
                self.possible_bytes.append(set([makeparity(self.match1[n])]))
            elif c == ord('u'):
                self.possible_bytes.append(upperbytes)
            elif c == ord('l'):
                self.possible_bytes.append(lowerbytes)
            elif c == ord('h'):
                self.possible_bytes.append(hexbytes)
            elif c == ord('m'):
                self.possible_bytes.append(set(numberbytes[1:9]))
            elif c >= ord('0') and c <= ord('9'):
                self.possible_bytes.append(set(numberbytes[:1+c-ord('0')]))
            elif c == ord('D'):
                self.possible_bytes.append(day1bytes)
            elif c == ord('A'):
                self.possible_bytes.append(day2bytes)
            elif c == ord('Y'):
                self.possible_bytes.append(day3bytes)
            elif c == ord('M'):
                self.possible_bytes.append(month1bytes)
            elif c == ord('O'):
                self.possible_bytes.append(month2bytes)
            elif c == ord('N'):
                self.possible_bytes.append(month3bytes)
            elif c == ord('H'):
                self.possible_bytes.append(hammbytes)
            elif c == ord('d'):
                self.possible_bytes.append(dcbytes)
            elif c == ord('p'):
                self.possible_bytes.append(paritybytes)
            else:
                self.possible_bytes.append(allbytes)

    def findexact(self, visual):
        return ((self.match2 == ord('e')) & 
                (visual == self.match1)).sum()

    def findupper(self, visual):
        return ((self.match2 == ord('u')) & 
                (visual >= ord('A')) &
                (visual <= ord('Z'))).sum()

    def findlower(self, visual):
        return ((self.match2 == ord('l')) & 
                (visual >= ord('a')) &
                (visual <= ord('z'))).sum()

    def findnumber(self, visual):
        return ((self.match2 >= ord('0')) & 
                (self.match2 <= ord('9')) &
                (visual >= ord('0')) &
                (visual <= self.match2)).sum()

    def findmag(self, visual):
        return ((self.match2 == ord('m')) & 
                (visual >= ord('1')) &
                (visual <= ord('8'))).sum()

    def findhex(self, visual):
        return ((self.match2 == ord('h')) & 
                (((visual >= ord('0')) & (visual <= ord('9'))) |
                 ((visual >= ord('A')) & (visual <= ord('F'))) |
                 ((visual >= ord('a')) & (visual <= ord('f'))))).sum()

    def calculaterank(self, visual):
        rank = 0
        rank += self.findexact(visual)
        rank += self.findupper(visual)*0.1
        rank += self.findlower(visual)*0.1
        rank += self.findnumber(visual)*0.2
        rank += self.findmag(visual)*0.2
        rank += self.findhex(visual)*0.1
        return rank

    def find(self, packet):
        rank = 0
        self.packet = packet # np.fromstring(packet, dtype=np.uint8)
        (self.m,self.r),self.me = mrag(self.packet[:2])
        if self.r == self.row:
            rank += 5
        rank += self.calculaterank(self.packet&0x7f)
        return rank/self.passrank if (rank > self.passrank) else 0

    def fixup(self):
        self.packet[0:2] = makemrag(self.m, self.row)
        for n in range(0, 42):
            if self.match2[n] == ord('e'):
                self.packet[n] = makeparity(self.match1[n])
        return "".join([chr(x) for x in self.packet])

    def check_page_info(self):
        self.p,self.pe = page(self.packet[2:4])
        try:
            hpage = [int(chr(self.packet[n+self.pagepos]&0x7f), 16) for n in range(3)]
            self.hm = hpage[0]
            self.hp = (hpage[1]<<4)|hpage[2]
            self.me = (self.hm != self.m) and self.me
            self.pe = (self.hp != self.p) and self.pe
        except ValueError:
            self.hm = -1
            self.hp = -1
            self.me = True
            self.pe = True

        #if self.me or self.pe:
        #    print("P%1d%02x " % (self.m,self.p)),
        #    print("P%1d%02x " % (self.hm,self.hp))

ARD = Finder("          653 ARDtext dd 14.10.14 19:37:49",
             "HHHHHHHHHHmhhpeeeeeeepppp39e19e99p29e59e59",
             name="ARDtext Packet 0", row=0)

BBC = Finder("          CEEFAX 217  Wed 25 Dec \x0318:29/53",
                "HHHHHHHHHHeeeeeeemhheeDAYep9eMONee"+"29e59e59", 
                name="BBC Packet 0", row=0)

Central = Finder("          Central  217 Wed 25 Dec 18:29:53",
                 "HHHHHHHHHHeeeeeeeeemhheDAYe39eMONp29e59e59", 
                 name="Central Packet 0", row=0)

FiveText = Finder("          \x06   5 text   \x07255 02 May\x031835:21",
                  "HHHHHHHHHHe"+"eeeeeeeeeeeee"+"mhhe39eMONe"+"2959e59", 
                  name="5 Text Packet 0", row=0)

TeletextLtd = Finder("          \x04\x1d\x03Teletext\x07 \x1c100 May05\x0318:29:53",
                     "HHHHHHHHHHe"+"e"+"e"+"eeeeeeeee"+"ee"+"mhheMONp9e"+"29e59e59", 
                     name="Teletext Ltd Packet 0", row=0)

FourTel = Finder("          4-Tel 307 Sun 26 May\x03C4\x0718:29:53",
                 "HHHHHHHHHHeeeeeemhheDAYep9eMONe"+"eee"+"29e59e59", 
                  name="4Tel Packet 0", row=0)

Oracle =  Finder("          ORACLE 297 Sun26 May\x03ITV 1829:53",
                 "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                   name="ORACLE Packet 0", row=0)

OracleCEN = Finder("          ORACLE 297 Sun26 May\x03CEN 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE Central Packet 0", row=0)

OracleYTV = Finder("          ORACLE 297 Sun26 May\x03YTV 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE Yorkshire Packet 0", row=0)

OracleTest = Finder("                 644                      ",
                    "HHHHHHHHHHeeeeeeemhheeeeeeeeeeeeeeeeeeeeee",
                  name="ORACLE Test Page Packet 0", row=0)
		              
Televox = Finder("          TELEVOX 000101  **       2022:02",
                 "HHHHHHHHHHeeeeeeee999999ppppppppppp2959e59", 
                  name="ORACLE Televox Packet 0", row=0)

OracleC4 = Finder("          ORACLE 297 Sun26 May\x03C4  1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE C4 Packet 0", row=0)

Oracle1976 = Finder("          ORACLE 297 Sun26May ITV 18.29/53",
                    "HHHHHHHHHHeeeeeeemhheDAY39MONeeeee29e59e59", 
                  name="ORACLE 1976 Packet 0", row=0)

OraclePre1976 = Finder("          ORACLE p176 Wed 18 Feb  20.44/13",
					   "HHHHHHHHHHeeeeeeepmhheDAYe39eMONee29e59e59", 
					name="ORACLE Pre-1976 Packet 0", row=0)
					
TeletextFailure = Finder("          TELETEXT SYSTEM FAILURE **:**:**",
					     "HHHHHHHHHHeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 
					name="Teletext System Failure Packet 0", row=0)		

DBI = Finder("              DBI/CH3 - DBILN1     2243:32",
		     "HHHHHHHHHHeeeeeeeeeeeeeeeeeeeeeeeee2959e59", 
			name="DBI/CH3 Packet 0", row=0)
                        
DBIStatus = Finder("              DBI STATUS PAGE      2243:43",
			       "HHHHHHHHHHppppeeeeeeeeeeeeeeepppppp2959e59", 
			       name="DBI Status Packet 0", row=0)			
					
TeletextSubtitles = Finder("               ITV SUBTITLES              ",
			               "HHHHHHHHHHeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 
			       name="Teletext Subtitles Packet 0", row=0)				
					
BBCnew = Finder("          CEEFAX 1 217 Wed 25 Dec\x0318:29/53",
                "HHHHHHHHHHeeeeeee2emhheDAYe39eMONe"+"29e59e59", 
             name="BBC Packet 0", row=0)

Generic     = Finder("          100 MEDICINA            18:29:53",
                     "HHHHHHHHHHpppppppppppppppppppppppppppppppp", 
                     name="Generic", row=0)

SkyTextEarly     = Finder("          \x06Skytext \x07100 Mon 12 Jan\x032320:53",
                     "HHHHHHHHHHeeeeeeeeeemhheDAYe39eMONe2959e59", 
                     name="SkyText", row=0)
                     
OracleLON = Finder("          ORACLE 297 Sun26 May\x03LON 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE London Packet 0", row=0)
                  
SkyText     = Finder("          \x06SKYTEXT \x07100 Mon 12 Jan\x032320:53",
                     "HHHHHHHHHHeeeeeeeeeemhheDAYep9eMONe2959e59", 
                     name="SkyText", row=0)
                     
TeletextOn3 = Finder("          Teletext on 3 525 May16\x0319:03:33",
                     "HHHHHHHHHHeeeeeeeeeeeeeemhheMON39"+"e29:59:59", 
                     name="TeletextOn3", row=0)
                     
TeletextOn4 = Finder("          Teletext on 4 525 May16\x0319:03:33",
                     "HHHHHHHHHHeeeeeeeeeeeeeemhheMON39"+"e29:59:59", 
                     name="TeletextOn4", row=0)
                     
OracleGRA = Finder("          ORACLE 297 Sun26 May\x03GRA 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE Granada Packet 0", row=0)

OracleTTT = Finder("          ORACLE 297 Sun26 May\x03TTT 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE Tyne Tees Packet 0", row=0) 

OracleHTV = Finder("          ORACLE 297 Sun26 May\x03HTV 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE HTV Packet 0", row=0)    

OracleITN = Finder("          ORACLE 297 Sun26 May ITN 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE ITN Packet 0", row=0)        

OracleGreenClock = Finder("          ORACLE 297 Sun26 May ITV 1829:53",
                          "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE ITV Green Clock Packet 0", row=0)  

OracleWhite = Finder("          ORACLE 297 Sun26 May\x07ITV 1829:53",
                     "HHHHHHHHHHeeeeeeemhheDAYp9eMON"+"peeep2959e59", 
                  name="ORACLE ITV White Channel ID and Clock", row=0) 
                  
OracleWhiteIDGreenClock = Finder("          ORACLE 297 Sun26 May\x07ITV\x021829:53",
                                 "HHHHHHHHHHeeeeeeemhheDAYp9eMON"+"peee"+"e2959e59", 
                  name="ORACLE ITV White Channel ID and Green Clock", row=0) 

Anglia =  Finder("          Anglia   217 Wed 25 Dec 18:29:53",
                 "HHHHHHHHHHeeeeeeeeemhheDAYe39eMONp29e59e59", 
                 name="Anglia Packet 0", row=0)       

PleaseReferToPage100 =  Finder("          PLEASE REFER TO PAGE 100 1829:53",
                               "HHHHHHHHHHeeeeeeeeeeeeeeeeeeeeeeeee2959e59", 
                                name="PleaseReferToPage100 Packet 0", row=0)  
                                
PleaseReferToPage400 =  Finder("          PLEASE REFER TO PAGE 400 1829:53",
                               "HHHHHHHHHHeeeeeeeeeeeeeeeeeeeeeeeee2959e59", 
                                name="PleaseReferToPage400", row=0) 

PleaseSelectPage100 =  Finder("           PLEASE SELECT PAGE 100  1829:53",
                              "HHHHHHHHHHeeeeeeeeeeeeeeeeeeeeeeeee2959e59", 
                                name="PleaseSelectPage100", row=0)                                 
                                
TurnToPage100 =  Finder("             TURN TO PAGE 700      1335:43",
                              "HHHHHHHHHHpppeeeeeeeeeeeeeeeepppppp2959e59", 
                                name="TurnToPage100", row=0)   

PageSelectedIsOnC4 =  Finder("           PAGE SELECTED IS ON C4  1903:46",
                             "HHHHHHHHHHpeeeeeeeeeeeeeeeeeeeeeepp2959e59", 
                                name="PageSelectedIsOnC4", row=0)                                   
                                
AirCallTeletext = Finder("             AIR CALL TELETEXT     1337:17",
                         "HHHHHHHHHHpppeeeeeeeeeeeeeeeeeppppp2959e59", 
                  name="Air Call Teletext", row=0)

OracleCH4 = Finder("          ORACLE 297 Sun26 May\x03CH4 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE CH4 Packet 0", row=0)         

OracleTVS = Finder("          ORACLE 297 Sun26 May TVS 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE TVS Packet 0", row=0)  
                  
OracleANG = Finder("          ORACLE 297 Sun26 May ANG 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE Anglia", row=0) 
                  
OracleHTV = Finder("          ORACLE 297 Sun26 May HTV 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE HTV", row=0)                   
                  
AirCallTeletext = Finder("             AIR CALL TELETEXT     1337:17",
                         "HHHHHHHHHHpppeeeeeeeeeeeeeeeeeppppp2959e59", 
                  name="Air Call Teletext", row=0) 

OracleOffAir = Finder("          ORACLE P000  DATE\x14\x1d\x03ITV \x07\x1cTIME  ",
                      "HHHHHHHHHHeeeeeeeeeeeeeeeee"+"ee"+"e"+"eeee"+"ee"+"eeeeee", 
                  name="ORACLE off air", row=0) 

DBIInternational = Finder("          \x01   DBI/CH4 M BCAST2  \x09\x07 2102:40",
                          "HHHHHHHHHHe"+"ppeeeeepppeppppppppppe"+"e"+"e2959e59", 
                  name="DBI International", row=0)                   

Westcountry = Finder("          \x04\x1D\x07westcountry 659 Mon 5\x1c0003.49",
                     "HHHHHHHHHHe"+"e"+"e"+"eeeeeeeeeeeemhheDAYp9e"+"2959e59", 
                  name="Westcountry", row=0)   

MTVText = Finder("          104\x03MTVText  \x03Sun 9 Apr\x0317:32:48",
                 "HHHHHHHHHHmhhe"+"eeeeeeeeee"+"DAYp9eMONe"+"29e59e59", 
                  name="MTVText", row=0)   

ORACLEDateTime = Finder("                     Sat29 Sep     1903:10",
                        "HHHHHHHHHHeeeeeeeeeeeDAYp9eMONeeeee2959e59", 
                  name="ORACLE Date and Time", row=0)

Supertext = Finder("          Supertext100 Sun  6 Aug 14:07/57",
                   "HHHHHHHHHHeeeeeeeeepppeDAYep9eMONp29e59e59", 
                  name="Supertext", row=0)

Central = Finder("          Central  6FF Wed  6 Nov 20:03:21",
                 "HHHHHHHHHHeeeeeeeeemhheDAYep9eMONe29e59e59", 
                name="Central", row=0)  
                
ITVSubtitles = Finder("              ITV SUBTITLES               ",
                      "HHHHHHHHHHeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 
                name="ITV Subtitles", row=0)   
                
OracleSTV1982 = Finder("          ORACLE 297 Sun26 May STV 1829:53",
                       "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE STV 1982", row=0) 

Granada = Finder("          Granada 625 Mon  9 Oct  20:03:21",
                 "HHHHHHHHHHeeeeeeeemhheDAYep9eMONee29e59e59", 
                name="Granada", row=0)      

ITVPlusGRA = Finder("          ITV+   633 Wed 3 Nov\x03GRA 0038:55",
                    "HHHHHHHHHHeeeepppmhheDAYp9eMON"+"eeeee2959e59", 
                name="ITV+ GRA", row=0) 

OracleS4C = Finder("          ORACLE 297 Sun26 May\x03S4C 1829:53",
                  "HHHHHHHHHHeeeeeeemhheDAYp9eMONe"+"eeee2959e59", 
                  name="ORACLE S4C", row=0)
                  
Sbectel2000s = Finder("          SBECTEL 400     26 Meh  20:07:35",
                      "HHHHHHHHHHeeeeeeeemhheeeee39epppee29e59e59", 
                 name="Sbectel 2000s", row=0)  

Sbectel2005 = Finder("          SBECTEL  497    Ion 12  19:06:13",
                     "HHHHHHHHHHeeeeeeeeemhheeeepppe39ee29e59e59", 
name="Sbectel 2005", row=0) 
             
Sbectel1990s = Finder("          \x02SBECTEL\x07\x07317\x07Mon\x0725\x07Dec 1843:56",
                    "HHHHHHHHHHe"+"eeeeeeee"+"e"+"mhhe"+"DAYe"+"p9e"+"MONe2959e59", 
                 name="Sbectel 1990s", row=0) 

Sbectel1990sb = Finder("          SBECTEL  317 Mon\x0725 Dec\x0318:43.56",
                       "HHHHHHHHHHeeeeeeeeemhheDAYe"+"p9eMONe"+"29e59e59", 
                 name="Sbectel 1990s", row=0)                 

STVAncillary = Finder("          \x04\x1d\x07SCOTTEXT  \x1c600  3Sep\x0323:59:56",
                      "HHHHHHHHHHe"+"e"+"e"+"eeeeeeeeeee"+"mhhep9MONe"+"29e59e59", 
                     name="STVAncillary", row=0)

ITVPlusHTV = Finder("          ITV+   633 Wed 3 Nov\x03HTV 0038:55",
                    "HHHHHHHHHHeeeepppmhheDAYp9eMON"+"eeeee2959e59", 
                    name="ITV+ HTV", row=0) 

itv1Wales = Finder("          itv1Wales 699 Tue Feb21 18:01:51",
                   "HHHHHHHHHHeeeeeeeeeemhheDAYeMONe9e29e59e59", 
                    name="itv1 Wales", row=0) 
                    
                    
CeefaxSelect200 = Finder("          \x0dPLEASE SELECT PAGE 200 13:40/18",
                         "HHHHHHHHHHe"+"eeeeeeeeeeeeeeeeeeeeeee29e59e59", 
                    name="Ceefax Select Page 200", row=0)                     
   
OracleGPN = Finder("          ORACLE 297 Sun26 May GPN 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE Grampian", row=0) 

Channel = Finder("          \x04\x1d\x07Channel  \x1c100 Apr 12\x0318:29:53",
                 "HHHHHHHHHHe"+"e"+"e"+"eeeeeeeeee"+"mhheMONe29e"+"29e59e59", 
                     name="Channel Ancillary", row=0)                  

OracleBDR = Finder("          ORACLE 297 Sun26 May BDR 1829:53",
                   "HHHHHHHHHHeeeeeeemhheDAYp9eMONpeeep2959e59", 
                  name="ORACLE Border", row=0)  
                     
all_headers = [Generic]
#all_headers = [BBC, CeefaxSelect200] # 20/12/1979 - 11/08/1990
#all_headers = [BBCnew] # 8/3/1997 - 26/8/2006

#all_headers = [OraclePre1976]
#all_headers = [OracleWhiteIDGreenClock] # 25/07/1979 - 01/04/1981
#all_headers = [OracleWhite] # 19/01/1981 - 01/04/1981
#all_headers = [OracleITN, OracleGreenClock, PleaseReferToPage100] # 25/12/1981 - 21/07/1982
#all_headers = [OracleITN, OracleGreenClock, OracleSTV1982, PleaseReferToPage100] # 17/10/1982 - 04/02/1983
#all_headers = [OracleITN, Oracle, PleaseReferToPage100, OracleOffAir] # 02/01/1983 - 24/09/1983
#all_headers = [Oracle, PleaseSelectPage100] #22/11/1983 - 07/02/1984
#all_headers = [Oracle, OracleBDR, PageSelectedIsOnC4, PleaseSelectPage100] #11/03/1984 - 27/12/1984
#all_headers = [Oracle, OracleANG, AirCallTeletext, TurnToPage100, PageSelectedIsOnC4, Televox, PleaseSelectPage100] # 02/04/1985 - 31/12/1992

#all_headers = [TeletextLtd, Granada, DBIInternational, TeletextOn3, ITVPlus] # 03/11/1993
#all_headers = [TeletextLtd, ITVPlusHTV, DBIInternational] # 26/09/1994 - 06/11/1996
#all_headers = [TeletextLtd, Channel] # 21/02/2002

#all_headers = [OracleCH4, OracleITN, PleaseReferToPage400] # 10/04/1983
#all_headers = [OracleC4] # 07/12/1983 - 31/12/1992

#all_headers = [OracleS4C] # 07/08/1988
#all_headers = [TeletextLtd, Sbectel2000s] # 25/01/2005 - 21/05/2006
#all_headers = [TeletextLtd, Sbectel2005] # 12/01/2005
#all_headers = [TeletextLtd, Sbectel1990s] # 25/12/1995 - 11/05/1996
#all_headers = [TeletextLtd, Sbectel1990sb] # 08/11/1998 - 21/01/2000
#all_headers = [TeletextLtd, FourTel, DBIInternational] # 19/6/1995 - 20/11/1998

#all_headers = [Supertext] 
#all_headers = [TeletextOn3] # 1/6/1998 - 5/9/1998
#all_headers = [FiveText, TeletextLtd]
#all_headers = [SkyText]

# there are two types of broadcast packet. one has 8/4 PDC data and the other
# has no encoding (not even parity). the latter is almost impossible to 
# deconvolve so we try for the former to speed up the finder.
BBC_BSD = Finder("\x15\xea \x15\x15\xea\xea\xea\x5e              BBC1 CEEFAX        ",
                 "e"+"e"+"de"+"e"+"e"+"e"+"e"+"e"+"HHHHHHHHHHHHHeeee2eeeeeeeeeeeeeee", 
                 name="BBC Broadcast Service Data", row=30)

Generic_BSD = Finder(" \xea                     BBC1 CEEFAX        ",
                     "He"+"dHHHHHH             pppppppppppppppppppp", 
                     name="Generic Broadcast Service Data", row=30)

all_bsd = [BBC_BSD, Generic_BSD]

def test(finders, packet):
    a_packet = np.fromstring(packet, dtype=np.uint8)
    ans = []
    for f in finders:
        ans.append((f.find(a_packet), f))
    t = max(ans)
    return t[1] if t[0] > 0 else None

if __name__=='__main__':

    F = BBC1

    while(True):
        tt = sys.stdin.read(42)
        if len(tt) < 42:
            exit(0)
        if F.find(tt):
            print "found"

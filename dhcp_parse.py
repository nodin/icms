#!/usr/bin/python
#from odict import OrderedDict
import os

macDict={}#OrderedDict()
nspDict={}#OrderedDict()

def digi2ASCII(hexStr,base):
    rtn=''
    if hexStr.endswith('.'):
        hexStr=hexStr[:-1]
    for hex in hexStr.split('.'):
        if hex=='':
            continue
        rtn+=chr(int(hex,base))
    return rtn

def dec2ASCII(hexStr):
    return digi2ASCII(hexStr,10)

def hex2ASCII(hexStr):
    return digi2ASCII(hexStr,16)

def multiple_split(s, seps):
    res = [s]
    for sep in seps:
        s, res = res, []
        for seq in s:
            res += seq.split(sep)
    return res

def convert2DecAndPlus1(field, dopad="true"):
    value = '%d'%(ord(field) +1)
    if dopad :
        value = '%02d'%(ord(field) +1)
    return value

def pad2digit(value):
    return "%02d"%(int(value))

def filterNodename(nodename):
    return nodename.replace("-",'')

def parseNSPByCID(CID):
    """
    nokia  : <Nodename> <slot>/<port>:0.100
    siement: <Nodename with SIIP> <shelf>/<slot>:0.100
    huawei : <Nodename with HUAG> <slot>/<port>:0.100
    ECI    : <Nodename> atm <slot>/<port>:0.100
    """

    NOKIA_SHELF='1'
    SIEMENT_PORT='17'
    HUAWEI_SHELF='0'
    ECI_SHELF='1'
    nsp_items = multiple_split(CID, [' ', ':', '/'])
    #print "nsp_items:%s"%(nsp_items)
    if len(nsp_items)==5:
        #nsp=nsp_items[0]+' atm'+"_"+ ECI_SHELF+'/'+pad2digit(nsp_items[2])+'/'+pad2digit(nsp_items[3])
        nsp=filterNodename(nsp_items[0])+"_"+ ECI_SHELF+'/'+pad2digit(nsp_items[2])+'/'+pad2digit(nsp_items[3])
    elif 'SIIP' in nsp_items[0]:
        nsp=filterNodename(nsp_items[0])+"_"+nsp_items[1]+'/'+pad2digit(nsp_items[2])+'/'+ SIEMENT_PORT
    elif 'HUAG' in nsp_items[0]:
        nsp=filterNodename(nsp_items[0])+"_"+ HUAWEI_SHELF+'/'+pad2digit(nsp_items[1])+'/'+pad2digit(nsp_items[2])
    else:
        nsp=filterNodename(nsp_items[0])+"_"+ NOKIA_SHELF+'/'+pad2digit(nsp_items[1])+'/'+pad2digit(nsp_items[2])
    return nsp

def parseUTStarcomAID(AID):
    """
    UTStarcom
     RID starts with"0000079d"
     RID
     Hexadecimal conversion of <Nodename>_<shelf>/<slot>/<port>
     RID: 0000079d010100ca000000000000000000004243445554414730303701080b000064
      No CID
    """


    AID=list(hex2ASCII(AID))
    #print AID
    AID=AID[:-3]
    #print AID
    ssp=AID[-3:]
    #print "UT startcomm ssp:%s"%(ssp)
    node_name=[]
    namestr= AID[:-3][::-1]
    #print namestr
    for i in range(len(namestr)):
        byte=namestr[i]

        #if len(byte)==0:
        #    continue
        #print "char %c"%(byte)
        if ord(byte)==0:
            break
        node_name.append(byte)
    #print node_name
    node_name = node_name[::-1] #reverse string
    return ''.join(node_name)+"_"+convert2DecAndPlus1(ssp[0],False)+'/'+convert2DecAndPlus1(ssp[1])+'/'+convert2DecAndPlus1(ssp[2])

def parseNSPfromOption82(option82):
    print findMiddleString(option82,'CID: ',' ')
    try:
        CID=dec2ASCII(findMiddleString(option82,'CID: ',' '));
        print CID
        AID=findMiddleString(option82,'AID: ','')
        #UT starcom;
        if AID.startswith("0.0.7.9d"):
              return parseUTStarcomAID(AID)
        #huawei
        elif hex2ASCII(AID).find('HUAG') != -1:
            return parseNSPByCID(AID)
        else:
            return parseNSPByCID(CID)
    except:
        return None

def findMiddleString(src,left,right):
    pos_begin = src.find(left)
    if pos_begin == -1:
        return ''
    pos_end = len(src) -1
    if len(right) != 0:
        pos_end = src.find(right, pos_begin + len(left))
    if pos_end == -1:
        return ''
    return src[pos_begin+len(left):pos_end]


def convertMAC(mac):
    return mac.replace(".",":").upper()

def parseDHCPOption82(lines):
    for line in lines:
        pos = line.find('raw option-82 info')
        if pos != -1:
            #option82 = findMiddleString(line,'raw option-82 info is CID:','')
            nsp = parseNSPfromOption82(line)
            if not nsp == None:
                ip  = findMiddleString(line,'for ',' ')
                nspDict[ip]=nsp.upper()
        else:
            pos = line.find('DHCPOFFER')
            if pos != -1:
                ip  = findMiddleString(line,'on ',' to')
                mac = findMiddleString(line,'to ',' ')
                macDict[ip]=convertMAC(mac)


READ_SIZE=4096000

def readLines(option82_filename,pos_filename):
    import os

    lines=[]
    pos='0'
    option82file= None
    try:
        filesize=os.path.getsize(option82_filename)
        option82file = open(option82_filename, 'rb')
        try:
            pos= open(pos_filename,'r').read()
        except:
            open(pos_filename, 'w').write("%s"%('0'))
            print 'no pos file,take pos as 0'
            pos='0'
        if not pos:
            return lines

        if filesize <= (long(pos)):
            pos=0L
        option82file.seek(long(pos))
        buffer = option82file.read(READ_SIZE)
        option82file.close()

        if buffer:
            last_line_pos=buffer.rfind('\n')
            if last_line_pos != -1:
                newpos=long(pos) + last_line_pos
                open(pos_filename, 'w').write("%d"%(newpos))
                lines=buffer.split('\n')
    finally:
        if option82file:
            try:
                option82file.close()
            except:
                pass
    return lines

macNspDict={}#OrderedDict()

def domatch():
    for ip, nsp in nspDict.items():
        try:
            mac = macDict[ip]
            if ip != None:
                macNspDict[mac]=nspDict[ip]
        except:
            print 'no key in mac:'+ip

    nspDict.clear()
    macDict.clear()

import logging
logger = None

def initlog(log_file):
    import logging.handlers
    global logger

    logger = logging.getLogger()
    hdlr = logging.handlers.RotatingFileHandler(
              log_file, maxBytes=200000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    return [logger,hdlr]

def log(message, level=logging.INFO):
    global logger

    logger.log(level ,message )
    #hdlr.flush()
    #logger.removeHandler( hdlr)


def writeout(dhcp_name,out_dir):
    import time
    outfile_name="%sMAC2NSP_%s_%s.txt"%(out_dir,time.strftime('%Y%m%d'),dhcp_name)
    f = file(outfile_name, 'a')
    print macNspDict
    for mac, nsp in macNspDict.items():
        f.write("%s %s\n"%(mac, nsp))
        log("matched nsp: %s %s"%(mac, nsp),logging.DEBUG)
    f.close()
    macNspDict.clear()

def test():
    import unittest
    #print hex2ASCII('48.48')
    assert hex2ASCII('30.30.') == '00'
    items =multiple_split('<Nodename with HUAG> <slot>/<port>:0.100', [' ', ':', '/'])
    #print items
    assert items==['<Nodename', 'with', 'HUAG>', '<slot>', '<port>', '0.100']
    print pad2digit('9')
    assert pad2digit('9')=='09'
    assert convert2DecAndPlus1('\x12', "true")=='19'
    print convert2DecAndPlus1('\x08', "true")
    assert convert2DecAndPlus1('\x08', "true")=='09'
    assert convert2DecAndPlus1('\x08', False)=='9'

    # parseNSPByCID(CID):
    """
    nokia  : <Nodename> <slot>/<port>:0.100
    siement: <Nodename with SIIP> <shelf>/<slot>:0.100
    huawei : <Nodename with HUAG> <slot>/<port>:0.100
    ECI    : <Nodename> atm <slot>/<port>:0.100
    """
    print parseNSPByCID("NOKIA 8/20:0.100")
    print parseNSPByCID("siementSIIP 10/9:0.100")
    print parseNSPByCID("huaHUAGwei 10/9:0.100")
    print parseNSPByCID("ECI atm 10/9:0.100")
    assert parseNSPByCID("NOKIA 8/20:0.100")=='NOKIA_1/08/20'
    assert parseNSPByCID("siement-SIIP 10/9:0.100")=='siementSIIP_10/09/17'
    assert parseNSPByCID("hua-HUAG-wei 10/9:0.100")=='huaHUAGwei_0/10/09'
    assert parseNSPByCID("ECI atm 10/9:0.100")=='ECI_1/10/09'
    assert findMiddleString("bbbaaaccc",'bbb','c')=='aaa'
    print convertMAC("0d.0e.ef")
    assert convertMAC("0d.0e.ef")=='0D:0E:EF'
    nsp =parseUTStarcomAID('0.0.7.9d.1.1.f.d2.0.0.0.0.0.0.0.0.0.0.4d.4b.54.55.54.41.47.30.30.36.0.d.12.0.1.f4')
    print "UT nsp: %s"%(nsp)
    assert nsp =='MKTUTAG006_1/14/19'
    nsp =parseNSPfromOption82('Aug  8 03:14:06 QCYHNMS-DHCP01 dhcpd: Lease for 172.16.6.253 raw option-82 info is CID: 50.56.53.54.49.48.48.55  AID: 0.0.7.9d.1.1.f.d2.0.0.0.0.0.0.0.0.0.0.4d.4b.54.55.54.41.47.30.30.36.0.d.12.0.1.f4')
    assert nsp=='MKTUTAG006_1/14/19'
    nsp =parseNSPfromOption82('Aug  8 03:14:06 QCYHNMS-DHCP01 dhcpd: Lease for 172.16.6.253 raw option-82 info is CID: 50.56.53.54.49.48.48.55  AID: 0.0.7.9d.1.1.f.d2.0.0.0.0.0.0.0.0.0.0.4d.4b.54.55.54.41.47.30.30.36.0.d.12.0.1.f4')
    assert nsp=='MKTUTAG006_1/14/19'
    nsp =parseNSPfromOption82('Aug 31 00:00:18 QCYHNMS-DHCP01 dhcpd: Lease for 8.16.202.255 raw option-82 info is CID: 66.76.82.48.49.45.78.75.65.71.48.49.45.67.79.84.32.49.55.47.50.51.58.48.46.53.48.48 AID: 3.2.0.0.0.0.0.0.0.40.43.bd.7d.38.11.17.0.1.f4')
    print nsp
    assert nsp=='BLR01NKAG01COT_1/17/23'
    lines=['Aug 31 00:00:18 QCYHNMS-DHCP01 dhcpd: Lease for 8.16.248.253 is connected to interface 48/48 (add 1 to port number!), VLAN 22832 on switch 0:0:0:0:0:0',
        'Aug 31 00:00:18 QCYHNMS-DHCP01 dhcpd: Lease for 8.16.248.253 raw option-82 info is CID: 81.67.89.48.51.45.78.75.65.71.48.49.45.67.79.84.32.53.47.49.51.58.48.46.53.48.48 AID: 3.2.0.0.0.0.0.0.0.40.43.be.77.b.5.d.0.1.f4',
        'Aug 31 00:00:18 QCYHNMS-DHCP01 dhcpd: DHCPDISCOVER from 40:4a:03:b7:8e:54 via 8.16.240.1',
        'Aug 31 00:00:18 QCYHNMS-DHCP01 dhcpd: DHCPOFFER on 8.16.248.253 to 40:4a:03:b7:8e:54 via 8.16.240.'
        ]
    parseDHCPOption82(lines)
    assert macDict=={'8.16.248.253': '40:4A:03:B7:8E:54'}
    assert nspDict=={'8.16.248.253': 'QCY03NKAG01COT_1/05/13'}
    domatch()
    print macNspDict
    assert macNspDict=={'40:4A:03:B7:8E:54': 'QCY03NKAG01COT_1/05/13'}
    logger,hdlr=initlog("option82_parse_log.log")
    writeout('c:/')
    lines=readLines('D:/pldt/dhcp_opt82.log','c:/dhcp_parse_pos')
    print lines
    parseDHCPOption82(lines)
    domatch()
    print macNspDict

def parseLeaseFile(dhcp_name,out_dir):
    import os
    lease_file_path = os.path.join('/tmp','%s.leases' % dhcp_name)
    os.system('grep "agent.remote-id" -B 3 %s |grep -v "uid" |grep -v "binding" |grep -v "circuit">k.txt' % lease_file_path)
    os.system("awk -F\  '{print $3}' k.txt|awk 'NF'>k1.txt")

    f = open('k1.txt','r')
    while 1:
        mac = f.readline()
        aid = f.readline()
        if not mac:
            break
        else:
            mac=mac.replace(";\n",'')
            aid=aid.replace(";\n",'')
            try:
                nsp=parseUTStarcomAID(aid.replace(":",'.').replace(';',''))
                macNspDict[convertMAC(mac)]=nsp
            except:
                print "not UTStarcom device in lease file"
    writeout(dhcp_name,out_dir)
    #writeout("/root")

def doParse(option82_filename,pos_filename,out_dir,dhcp_name):
    doexit=None
    for count in range(20):
        for inner_count in range(20):
            lines=readLines(option82_filename,pos_filename)
            if not lines:
                doexit='true'
                break
            parseDHCPOption82(lines)
        if doexit:
            break
        import time
        time.sleep(2)

    domatch()
    writeout(dhcp_name,out_dir)

def parseDHCPFile(dhcp_name):
    DHCP_OPTION82_LOG='/var/log/dhcp_opt82.log_'+dhcp_name
    POS_FILE='/var/log/dhcp_parse_pos_' + dhcp_name
    OUT_DIR='/var/log/'
    begin_pos='0'
    if os.path.isfile(DHCP_OPTION82_LOG)==False:
        open(DHCP_OPTION82_LOG,"w")
    if os.path.isfile(POS_FILE)==False:
        pos_file = open(POS_FILE,"w")
        pos_file.write("0")
    try:
        begin_pos= open(POS_FILE).read()
    except:
        print "no pos file"
    logger,hdlr=initlog(DHCP_OPTION82_LOG)
    log("begin parse DHCP option82 from : %s at position: %s"%(DHCP_OPTION82_LOG,begin_pos))
    parseLeaseFile(dhcp_name,OUT_DIR)
    doParse(DHCP_OPTION82_LOG,POS_FILE,OUT_DIR,dhcp_name)
    log("end parse DHCP option82 file : %s at position: %s"%(DHCP_OPTION82_LOG,open(POS_FILE).read( )))



#
#DHCP_OPTION82_LOG='/var/log/dhcp_opt82.log'
#POS_FILE='/var/log/dhcp_parse_pos'
#OUT_DIR='/home/test/OPTION82/'
#logger=None
#test_mode=True
#
#if test_mode:
#    test()
#    POS_FILE='C:/dhcp_parse_pos'
#    logger,hdlr=initlog("option82_parse_log.log")
#    log("begin parse DHCP option82 from : %s at position: %s"%('',open(POS_FILE).read( )))
#    print "begin parse python file."
#    doParse('D:/pldt/dhcp_opt82.log','C:/dhcp_parse_pos','C:/')
#    log("end parse DHCP option82 file : %s at position: %s"%(DHCP_OPTION82_LOG,open(POS_FILE).read( )))
#                                                 m
#else:
#    begin_pos='0'
#    try:
#        begin_pos= open(POS_FILE).read()
#    except:
#        print "no pos file"
#
#    logger,hdlr=initlog("option82_parse_log.log")
#    log("begin parse DHCP option82 from : %s at position: %s"%(DHCP_OPTION82_LOG,begin_pos))
#    parseLeaseFile(OUT_DIR)
#    doParse(DHCP_OPTION82_LOG,POS_FILE,OUT_DIR)
#    log("end parse DHCP option82 file : %s at position: %s"%(DHCP_OPTION82_LOG,open(POS_FILE).read( )))

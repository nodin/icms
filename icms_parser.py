from logger import log
from string import maketrans

INVALID_CHAR_TABLE = maketrans('\xa0', ' ')

def parse_subscriber(line, fieldDescriptors):
    """Parse a line of ICMS file and return a list of tuples containing the fields"""
    line = line.translate(INVALID_CHAR_TABLE)
    result = []
    for name, field in fieldDescriptors:
        try:
            value = field.get_value(line)
        except:
            log.error("Invalid line found when parsing field %s: \n%s" % (name, line))
            return None
        if value == None:
                return None
        # Ignore the line if the value is empty and it is not-null
        if field.notNull and value == "" and name != "bb_" and name!= "dt_":
            log.info("The value of the field %s is empty while non-empty value is expected: \n%s" % (name, line))
            return None

        result.append( (name, value.decode('iso-8859-1', 'replace').encode('utf-8', 'replace')) )

    return result


def subscriber_to_string(subscriber):
    """Subscriber to string"""
    return '{\n' + '\n'.join([ "%s=%s" % (name, value) for name, value in subscriber]) + '\n}\n'


def trim_substr(s, start, length):
    return s[start : start + length].strip()


def is_any_true(func, it):
    """
    Iterate the elements with the given iterator, and apply the func the the elements.
    Return true the func returns true, returns false if all func call return false.
    """
    for item in it:
        if func(item): return True
    return False


def get_ssp_legacy(line, senStart, senLen):
    sen = trim_substr(line, senStart, senLen).replace(' ', '')
    if len(sen) < 11:
        return None
    #(shelf, slot, port)
    return (sen[6:7], sen[7:9], sen[9:11])


def get_ssp_ngn(line, coeStart, coeLen):
    coe = trim_substr(line, coeStart, coeLen)
    if len(coe) < 9:
        return None
    coe = coe[-9:]
    #(shelf, slot, port)
    return (coe[0:1], coe[1:3], coe[3:5])


class NormalField(object):
    """A normal field in a ICMS file"""
    def __init__(self, start, length, notNull=False):
        self.notNull = notNull
        self.start = start
        self.length = length

    def get_value(self, line):
        """Extract the value from a line of ICMS file"""
        return trim_substr(line, self.start, self.length)


class NodeAssignmentField(object):
    """Node assignment field with a slightly different implementation"""

    LEGACY_KEYWORDS = ['ECIP', 'SIIP', 'NKAG', 'NKIP']
    NGN_KEYWORDS = ['UTAG', 'HUAG']

    def __init__(self,
            pcbiStart, pcbiLen,
            scbiStart, scbiLen,
            cidStart, cidLen,
            coeStart, coeLen,
            senStart, senLen,
            notNull=True):
        self.notNull = notNull
        self.pcbiStart = pcbiStart
        self.pcbiLen = pcbiLen
        self.scbiStart = scbiStart
        self.scbiLen = scbiLen
        self.cidStart = cidStart
        self.cidLen = cidLen
        self.coeStart = coeStart
        self.coeLen = coeLen
        self.senStart = senStart
        self.senLen = senLen

    def get_value(self, line):
        format_nssp = lambda n, ssp : ssp and ("%s_%s/%s/%s" % (n, ssp[0], ssp[1], ssp[2])) or ''
        # check CID for NGN DSLAMs
        cid = trim_substr(line, self.cidStart, self.cidLen)
        if is_any_true(lambda kw : kw in cid, self.NGN_KEYWORDS):
            return format_nssp(cid, get_ssp_ngn(line, self.coeStart, self.coeLen))
        # check FMPCBI for LEGACY DSLAMs
        pcbi = trim_substr(line, self.pcbiStart, self.pcbiLen)
        if is_any_true(lambda kw : kw in pcbi, self.LEGACY_KEYWORDS):
            return format_nssp(pcbi.replace('-', ''), get_ssp_legacy(line, self.senStart, self.senLen))
        # check FMSCBI for LEGACY DSLAMs
        scbi = trim_substr(line, self.scbiStart, self.scbiLen)
        if is_any_true(lambda kw : kw in scbi, self.LEGACY_KEYWORDS):
            return format_nssp(scbi.replace('-', ''), get_ssp_legacy(line, self.senStart, self.senLen))
        return ''


class AdminDomainField(object):
    """docstring for AdminDomainField"""
    def __init__(self, f1Start, f1Len, f2Start, f2Len, notNull=True):
        self.notNull = notNull
        self.f1Start = f1Start
        self.f1Len = f1Len
        self.f2Start = f2Start
        self.f2Len = f2Len

    def get_value(self, line):
        """docstring for get_value"""
        field1 = trim_substr(line, self.f1Start, self.f1Len)
        field2 = trim_substr(line, self.f2Start, self.f2Len)
        if len(field1) >= 3:
            return '/PLDT/' + field1[0:3]
        elif len(field2) >=3:
            return '/PLDT/' + field2[0:3]
        else:
            return '/PLDT/'

class  BBField(object):
    """A BB filed in a ICMS  file"""
    def __init__(self, pos, notNull=False):
        self.notNull = notNull
        self.pos = pos
    def get_value(self, line):
        """Extract the value from a line of ICMS file"""
        resultlist = line.split('|')
        print "bb parese result list is %s" % len(resultlist)
        if len(resultlist) < 13:
            return None
        if len(resultlist) == self.pos:
            print 'service status is null'
            return ''
             
        value = resultlist[self.pos]    
        return value.strip()
        

class BBNodeAssignField(object):
    def __init__(self, pos, notNull=False):
        self.notNull = notNull
        self.pos = pos
    def get_value(self,line):
        resultlist = line.split('|')
        if len(resultlist) < 13:
            return None
        resultlist = line.split('|')
        value = resultlist[5]+'_' + resultlist[6] +'/'+resultlist[7]+'/'+resultlist[8] 
        print value
        return value

class BBDomainPathField(object):
    def __init__(self, pos, notNull=False):
        self.notNull = notNull
        self.pos = pos
    def get_value(self,line):
        resultlist = line.split('|')
        if len(resultlist) < 13:
            return None
        resultlist = line.split('|')
        value = resultlist[5]
        return '/PLDT/'+value

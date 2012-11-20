from icms_parser import *


MLU_DESC = [
    ( "type",               NormalField(2, 2) ),
    ( "identifer",          NormalField(11, 10) ),
    ( "pl",                 NormalField(11, 10) ),
    ( "phoneNumber",        NormalField(11, 10) ),
    ( "name",               NormalField(21, 41) ),
    ( "address",            NormalField(62, 60) ),
    ( "otherContactNumber", NormalField(122, 30) ),
    ( "serviceType",        NormalField(157, 2) ),
    ( "accountNumber",      NormalField(183, 10) ),
    ( "pppoeAccount",       NormalField(183, 10) ),
    ( "domainPath",         AdminDomainField(339, 16, 178, 5) ),
    ( "nodeAssign",         NodeAssignmentField(339, 16, 377, 16, 206, 13, 193, 13, 0, 0) )
]


MLR_DESC = [
    ( "type",               NormalField(2, 2) ),
    ( "identifer",          NormalField(11, 10) ),
    ( "pl",                 NormalField(11, 10) ),
    ( "phoneNumber",        NormalField(11, 10) ),
    ( "name",               NormalField(31, 41) ),
    ( "address",            NormalField(72, 60) ),
    ( "otherContactNumber", NormalField(132, 30) ),
    ( "serviceType",        NormalField(167, 2) ),
    ( "status",             NormalField(186, 1) ),
    ( "accountNumber",      NormalField(194, 10) ),
    ( "pppoeAccount",       NormalField(194, 10) ),
    ( "installedDate",      NormalField(599, 9) ),
    ( "domainPath",         AdminDomainField(350, 16, 189, 5) ),
    ( "nodeAssign",         NodeAssignmentField(350, 16, 388, 16, 217, 13, 204, 13, 0, 0) )
]


MLD_DESC = [
    ( "type",               NormalField(2, 2) ),
    ( "identifer",          NormalField(11, 10) ),
    ( "pl",                 NormalField(11, 10) ),
    ( "phoneNumber",        NormalField(11, 10) ),
    ( "name",               NormalField(21, 41) ),
    ( "address",            NormalField(62, 60) ),
    ( "otherContactNumber", NormalField(122, 30) ),
    ( "serviceType",        NormalField(157, 2) ),
    ( "accountNumber",      NormalField(183, 10) ),
    ( "pppoeAccount",       NormalField(183, 10) ),
    ( "domainPath",         AdminDomainField(339, 16, 178, 5) ),
    ( "nodeAssign",         NodeAssignmentField(339, 16, 377, 16, 206, 13, 193, 13, 604, 15) )
]


MLS_DESC = [
    ( "type",               NormalField(2, 2) ),
    ( "identifer",          NormalField(11, 10) ),
    ( "pl",                 NormalField(11, 10) ),
    ( "phoneNumber",        NormalField(11, 10) ),
    ( "name",               NormalField(31, 41) ),
    ( "address",            NormalField(72, 60) ),
    ( "otherContactNumber", NormalField(132, 30) ),
    ( "serviceType",        NormalField(167, 2) ),
    ( "status",             NormalField(186, 1) ),
    ( "accountNumber",      NormalField(194, 10) ),
    ( "pppoeAccount",       NormalField(194, 10) ),
    ( "installedDate",      NormalField(599, 9) ),
    ( "domainPath",         AdminDomainField(350, 16, 189, 5) ),
    ( "nodeAssign",         NodeAssignmentField(350, 16, 388, 16, 217, 13, 204, 13, 650, 15) )
]

BB_DESC = [
    ( "type",               BBField(10) ),
    ( "identifer",          BBField(2) ),
    ( "pl",                 BBField(2) ),
    ( "phoneNumber",        BBField(2) ),
    ( "name",               BBField(0) ),
    ( "address",            BBField(1) ),
    ( "otherContactNumber", BBField(10) ),
    ( "serviceType",        BBField(12) ),
    ( "accountNumber",      BBField(9) ),
    ( "domainPath",         BBDomainPathField(5) ),
    ( "nodeAssign",         BBNodeAssignField(5) )
]

DESCRIPTORS = {
    'mlu' : MLU_DESC,
    'mlr' : MLR_DESC,
    'mld' : MLD_DESC,
    'mls' : MLS_DESC,
    'bb_' : BB_DESC,
    'dt_' : BB_DESC
}

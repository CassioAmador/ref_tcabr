#!/usr/bin/python
from os import system,environ,getcwd
from os.path import isfile

import last_shot as ls

#does the same as the method inside class REF_SETUP. Some day they can be the same
def findshot(tipo):
    if tipo=='data':
        shot=ls.read_shot()+1
    else:
        shot=ls.last_shot(tipo)+1
    return shot

def ref_acq(com):
    system(com)
    if isfile('%s/bin/bindata_1.bin' % (getcwd())):
        return True
    else:
        return False

def pos_acq(tipo):
    shot=findshot(tipo)
    system('for bin in %s/bin/bindata_*.bin; do mv $%s/data/%s_${bin: -5}; done' % (getcwd(),tipo,shot))
    #'cd' to folder is needed, otherwise tar will store full path with files.
    system('cd data/%s && tar -zcvf data/%s/Shot%s_Ref.tgz %s_*' % (tipo,tipo,shot,shot))
    if tipo=='data':
        print "Starting data transfer to SAUSAGE"
        try:
            system('rsync -auv -e ssh /TCABRdata/MDSplusTreeTCABRRef/tcabr_ref_%s* daqref@sausage.if.usp.br:/TCABRdata/MDSplusTreeTCABRRef/' % (shot))
            system('rsync -auv -e ssh /TCABRdata/MDSplusTreeTCABRRef/tcabr_ref_%s* daqref@tcabrcl.if.usp.br:/TCABRdata/MDSplusTreeTCABRRef/' % (shot))
            print "MDSplus tree transfered to SAUSAGE"
        except:
            print "It's was not possible to transfer MDSplus tree to SAUSAGE"
        system('rsync -auv -e ssh %s/data/Shot%s_Ref.tgz root@sausage.if.usp.br:/TCABRdata/data/' % (shot))
        print "data transfered to SAUSAGE"
    print '\nShot%s_Ref done\n' % shot

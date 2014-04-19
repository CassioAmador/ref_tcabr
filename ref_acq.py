#!/usr/bin/python
from os import system,environ,getcwd
from os.path import isfile

import last_shot as ls

lugar='/home/GRS/TCABR'

#does the same as the method inside class REF_SETUP. Some day they can be the same
def findshot(tipo):
    if tipo=='data':
        shot=ls.read_shot()+1
    else:
        shot=ls.last_shot(tipo)+1
    return shot

def ref_acq(com):
    system(com)
    if isfile('%s/bindata_1.bin' % (getcwd())):
        return True
    else:
        return False

def pos_acq(tipo):
    shot=findshot(tipo)
    system('for bin in %s/bindata_*.bin; do mv $bin %s/%s/%s_${bin: -5}; done' % (getcwd(),lugar,tipo,shot))
    # print 'for bin in %s/bindata_*.bin; do mv $bin %s/%s/%s_${bin: -5}; done' % (getcwd(),lugar,tipo,shot)
    #'cd' to folder is needed, otherwise tar will store full path with files.
    system('cd %s/%s && tar -zcvf %s/%s/Shot%s_Ref.tgz %s_*' % (lugar,tipo,lugar,tipo,shot,shot))
    if tipo=='data':
        print "Starting data transfer to SAUSAGE"
        try:
            system('rsync -auv -e ssh /TCABRdata/MDSplusTreeTCABRRef/tcabr_ref_%s.characteristics root@sausage.if.usp.br:/TCABRdata/MDSplusTreeTCABRRef/' % (shot))
            system('rsync -auv -e ssh /TCABRdata/MDSplusTreeTCABRRef/tcabr_ref_%s.datafile root@sausage.if.usp.br:/TCABRdata/MDSplusTreeTCABRRef/' % (shot))
            system('rsync -auv -e ssh /TCABRdata/MDSplusTreeTCABRRef/tcabr_ref_%s.tree root@sausage.if.usp.br:/TCABRdata/MDSplusTreeTCABRRef/' % (shot))
            print "MDSplus tree transfered to SAUSAGE"
        except:
            print "It's was not possible to transfer MDSplus tree to SAUSAGE"
        system('rsync -auv -e ssh %s/data/Shot%s_Ref.tgz root@sausage.if.usp.br:/TCABRdata/data/' % (lugar,shot))
        print "data transfered to SAUSAGE"
    print '\nShot%s_Ref done\n' % shot

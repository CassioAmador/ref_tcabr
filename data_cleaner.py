#!/usr/bin/python
from os import popen
import time
lugar="/home/GRS/TCABR"
lista=popen("ls -rt %s/data| grep Ref" % lugar).readlines()
blacklist=[]
log=open("log_cleaner.dat","w")
log.write("\nCleaning shots older than last 400 shots\n")
log.write(time.strftime("%X_%B_%d_%Y\n"))
log.write("erasing the following files\n")
if len(lista)>400:
    for i in range(len(lista)-400):
        blacklist.append(lista[i].split("Shot")[1].split("_Ref")[0])
for shot in blacklist:
    for channel in range(4):
        arq="%s/data/%s_%s.bin" % (lugar,shot,channel)
        log.write("%s\n" % arq)
    arq="%s/data/%s_info.dat" % (lugar,shot)
    log.write("%s\n" % arq)
    arq="%s/data/Shot%s_Ref.tgz" % (lugar,shot)
    log.write("%s\n" % arq)
log.write("******************************************\n")
log.close()

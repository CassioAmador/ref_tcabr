#!/usr/bin/python
from os import popen
import time
max_shot_number=500
lugar="/home/GRS/TCABR"
lista=popen("ls -rt %s/data| grep Ref" % lugar).readlines()
blacklist=[]
log=open("log_cleaner.dat","a")
log.write("Cleaning shots older than last 400 shots\n")
log.write(time.strftime("%X_%B_%d_%Y\n"))
log.write("erasing data from the following shots:\n")
if len(lista)>max_shot_number:
    for i in range(len(lista)-max_shot_number):
        blacklist.append(lista[i].split("Shot")[1].split("_Ref")[0])
    for shot in blacklist:
        log.write("%s\n" % shot)
    log.write("....\n....\n")
    for shot in blacklist:
        for channel in range(4):
            arq="%s/data/%s_%s.bin" % (lugar,shot,channel)
            log.write("%s\n" % arq)
        arq="%s/data/%s_info.dat" % (lugar,shot)
        log.write("%s\n" % arq)
        arq="%s/data/Shot%s_Ref.tgz" % (lugar,shot)
        log.write("%s\n" % arq)
    log.write("Total number of shots: %s\n" % len(blacklist))
    log.write("Total number of files deleted: %s\n" % (len(blacklist)*6))
else:
    log.write("No more than %s shots! Nothing to do...\n" % max_shot_number)
log.write("******************************************\n\n")
log.close()

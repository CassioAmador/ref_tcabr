from os import write
from os.path import isfile

arq="/home/GRS/TCABR/ref_exists"
def check_ref():
    if not isfile(arq):
        control=open(arq,"w")
        control.write("0")
        control.close()
    control=open(arq,"rw")
    if int(control.read())==1:
        print "\n\nacquisition already running!!!\n\n"
        exit()
    return True

def lock_ref():
    control=open(arq,"w")
    control.write("1")
    control.close()
    
def free_ref():
    control=open(arq,"w")
    control.write("0")
    control.close()

def kill():
    from subprocess import Popen, PIPE
    from os import getpid
    ownpid=getpid()
    for word in ("ref","python"):
        pipe = Popen("ps -e | grep %s" % word, shell=True, stdout=PIPE).stdout
        output = pipe.read()
        if output!="":
            pid=output.split(' ')[1]
            if pid!=ownpid:
                Popen("kill -9 %s" % pid, shell=True, stdout=PIPE).stdout
    free_ref()

if __name__=='__main__':
    kill()

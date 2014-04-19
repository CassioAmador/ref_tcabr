# -*- coding: utf-8 -*-
import os

class Agilent_prog:
    def __init__(self):
        device="/dev/usbtmc1"
        if not os.path.exists(device):
            os.chdir("/home/GRS/Download/usbtmc/")
            os.system("sudo ./usbtmc_load")
        os.system("sudo chmod a+rw %s" % device)
        self.check=True
        try:
            self.porta=os.open(device,os.O_RDWR)
        except OSError:
            self.error_message('   LIGUE','    AQUI')
            self.check=False
            return
        os.write(self.porta,"BURS:STAT OFF")
        os.write(self.porta,"OUTP OFF")
        #programar pulso
        os.write(self.porta,"FUNC PULS")
        #programar volt max
        os.write(self.porta,"VOLT:HIGH 5")
        #programar volt min
        os.write(self.porta,"VOLT:LOW 0")
        #programar tamanho pulso 200ns
        os.write(self.porta,"PULS:WIDT 0.0000002")
        #programar ciclos
        os.write(self.porta,"BURS:MODE TRIG")
        os.write(self.porta,"TRIG:SOUR EXT")
        os.write(self.porta,"TRIG:SLOP NEG")

    def prog(self,mode,times):
        os.write(self.porta,"OUTP OFF")
        if mode=="ff":
            dur=times
            total_time=1e-6
        elif mode=="sf":
            sweep,interv_sweep,dur=times
            total_time=(sweep+interv_sweep)*1e-6
        elif mode=="hf":
            hop_time,dur=times
            total_time=hop_time*1e-6
        os.write(self.porta,"OUTP OFF")
        #programar periodo
        os.write(self.porta,"PULS:PER %f" % (total_time))
        #programar num de ciclos
        if mode=="ff":
            os.write(self.porta,"BURS:NCYC 1")        
        else:
            os.write(self.porta,"BURS:NCYC %d" % (3*dur*1e-3/total_time))       
        os.write(self.porta,"BURS:STAT ON")
        os.write(self.porta,"OUTP ON")
    
    def turn_off(self):
        os.write(self.porta,"OUTP OFF")
        os.write(self.porta,"BURS:STAT OFF")
    
    def error_message(self,linha1,linha2):
        print """
                                   ******************* 
                                   *    GERADOR      *
                                   *   MICROONDAS    *
                                   *******************
                                       | | | |
                                       | | | |

                                   ******************* 
                                   *   *         *   *
                                   *   *         *   *
                                   *   *   ATCA  *   *
                                   *   *         *   *
                                   *******************
                                         |   |
                                         |   |
                                   ******************* 
                  %s         *    GERADOR      *
                  %s  ---->  *   DE FUNÇÕES    *
                                   *******************""" % (linha1,linha2)
        #exit()

def clear():
    os.chdir("/home/GRS/Download/usbtmc/")
    os.system("sudo ./usbtmc_ioctl 1 clear")
    porta=os.open("/dev/usbtmc1",os.O_RDWR)
    os.write(porta,"*RST")
    os.write(porta,"*IDN?")
    a=os.read(porta,100)
    print a

if __name__=="__main__":
#    import check_ref
#    if check_ref.check_ref():
#        agilent=Agilent_prog()
#        agilent.prog("sf",(10,2,150))
#    os.write(agilent.porta,"*IDN?")
#    a=os.read(agilent.porta,100)
    clear()

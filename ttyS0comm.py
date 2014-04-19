# -*- coding: utf-8 -*-
import serial,time
from os import popen,system

class HTO_com:
    def __init__(self):
        #TIMEOUT OF 1 SECOND, SO IT CAN READ BACK, AND XONXOFF SO IT WAITS FOR MESSAGE.
        #This command opens port with port='/dev/ttyS0', baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1, xonxoff=1, rtscts=0, dsrdtr=0
        self.ser=serial.Serial(port='/dev/ttyS0',xonxoff=1,timeout=1)
    
    def send(self,com,multiple=0):
        if multiple==0:
            self.ser.write(com + '\n')
        else:
            self.ser.writelines(com)
        if com=='mode sweep':
            time.sleep(3)
        out=self.ser.readlines()
        print out
        out = out[1]
        return out.split('\r\n')[0]

    def clean(self):
        self.ser.flushInput()
        self.ser.flushOutput()

    def close(self):
        self.ser.close()

class HTO_prog:
    def __init__(self):
        a=popen('ls -al /dev/ttyS0').readlines()
        comp='rw'
        if a[0][6:8]!=comp:
            system('sudo chmod o+rw /dev/ttyS0')
        try:
            self.HTO=HTO_com()
            self.HTO.send('$8')
        except IndexError:
            self.error_message('   LIGUE','    AQUI')
        self.mode=0
        self.oldmode='f'
        self.oldf_start,self.oldf_end,self.oldsweep,self.oldfreq_table=0,0,0,[]
        self.st=0
    def isopen(self):
        if self.HTO.ser.isOpen():
            self.st.append('Serial port still open\n')
        else:
            self.st.append('bad, bad port!\n')
    def sf_prog(self,f_start,f_end,sweep):
        if (self.oldf_start,self.oldf_end,self.oldsweep)!=(f_start,f_end,sweep):
            self.oldf_start,self.oldf_end,self.oldsweep=(f_start,f_end,sweep)
            self.oldmode='sf'
            self.HTO.send('trigger d')
            self.HTO.send('mode normal')
            self.HTO.send('defsw i %d %d %d' % (1e6*f_start,1e6*f_end,sweep))
            a=self.HTO.send('mode sweep')
            self.st.appendtext('%s\n' % a)
#            self.st.appendtext('%s\n' % a)
            self.HTO.send('trigger e')
        self.st.appendtext('HTO ready for sweep frequency')
    def ff_prog(self,f_start):
        if self.oldmode!='ff':
            self.HTO.send('trigger d')
        a=self.HTO.send('mode normal')
        self.st.appendtext('%s\n' % a)
        if self.oldmode=='hf':
            a=self.HTO.send('clearscan')
            self.st.appendtext('%s\n' % a)
        if (self.oldf_start)!=(f_start):
            self.oldmode='ff'
            self.oldf_start=f_start
            self.HTO.send('freq %d' % (1e6*f_start))
        self.st.appendtext('HTO ready for fixed frequency')
    def hf_prog(self,freq_table,sweep):
        if self.oldmode=='hf':
            self.HTO.send('mode normal')
            a=self.HTO.send('clearscan')
            self.st.appendtext('%s\n' % a)
        if (sweep,freq_table)!=(self.oldsweep,self.oldfreq_table):
            self.oldsweep=sweep
            self.oldfreq_table=freq_table
            self.HTO.send('trigger d')
            self.HTO.send('mode normal')
            self.oldmode=='hf'
            for f,freq in enumerate(freq_table):
                self.HTO.send('addplat %s %d' % (f,1e6*freq))
            self.HTO.send('timeout %d' % sweep)
            a=self.HTO.send('mode hop')
            self.st.appendtext('%s\n' % a)
            self.HTO.send('trigger e')
        self.st.appendtext('HTO ready for hopping frequency')
    def close(self):
        if self.mode in ('sf','hf'):
            self.HTO.send('trigger d')
        self.HTO.close()
    def error_message(self,linha1,linha2):
        print """
                                   ******************* 
                  %s         *    GERADOR      *
                  %s  ---->  *   MICROONDAS    *
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
                                   *    GERADOR      *
                                   *   DE FUNÇÕES    *
                                   *******************""" % (linha1,linha2)

        exit()

if __name__=='__main__':
    asd=HTO_com()
    while 1:
        com=raw_input(">> ")
        if com=='exit':
            asd.close()
            exit()
        else:
            msg=asd.send(com)
            print msg
        

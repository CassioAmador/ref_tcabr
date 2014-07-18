#!/usr/bin/python
# -*- coding: utf-8 -*-

import Tkinter as tk
import threading
import time
import Pmw
import sqlite3
import socket
from os import getcwd,popen,system,environ,write,path,getpid
from sys import argv

import last_shot as ls
import ttyS0comm
import agilentcomm
import ref_acq
import MDSTree
import SimpleConfigParser

ref_folder=getcwd()

#Import the configuration parameters from "oper_config.ini"
#They are called inside each class, at the beginning
cp = SimpleConfigParser.SimpleConfigParser()
cp.read('%s/oper_config.ini' % ref_folder)

#THREADING TO MAKE CHILD TIME COUNTER
class backgroundTask(threading.Thread):
    def __init__(self,father_class):
        threading.Thread.__init__(self)
        self.father_class=father_class
        self.setDaemon(True)
        self.start()

    def run(self):
        self.father_class.st.appendtext('\n\t')
        for i in ('...'):
            self.father_class.st.appendtext('\t%s' % i)
            time.sleep(0.2)
        print ""
        self.father_class.root.destroy()

class acquisitonTask(threading.Thread):
    def __init__(self,father_class,command):
        threading.Thread.__init__(self)
        self.com=command
        self.father_class=father_class
        self.setDaemon(True)
        self.start()
    def run(self):
        #returns True if acquisition was successfull
        b=ref_acq.ref_acq(self.com)
        if b:
            self.father_class.savesetup()

class mdstreeTask(threading.Thread):
    def __init__(self,father_class):
        threading.Thread.__init__(self)
        self.father_class=father_class
        self.setDaemon(True)
        self.start()
        self.join(360)
    def run(self):
        #It calls the following parameters: tipo,shot,value,mode,f_start,freqs,time_step,f_end,sweep,interv_sweep
        MDSTree.populate_MDSTree(self.father_class)

class Refsetup:
    def __init__(self,root,database,tipo='data'):
        self.tty=int(cp.getoption('tty'))
        self.func_gen=int(cp.getoption('func_gen'))
        self.tty_read=int(cp.getoption('tty_read'))
        self.freq_min=float(cp.getoption('freq_min'))
        self.freq_max=float(cp.getoption('freq_max'))
        self.sweep_min=int(cp.getoption('sweep_min'))
        self.root=root
        self.root.protocol('WM_DELETE_WINDOW', self.close)
#        self.plls={50:11,62.5:9,100:7,200:1}
        self.plls={50:11,62:9,100:7,125:3,200:1} # actually 62.5:9 MHz
        self.database=database
        self.tipo=tipo
        self.oper=0
        if not path.exists("/dev/pcie0"):
            system("sudo /home/GRS/driver_ATCA/driver/mknod.sh")
            system("sleep 1")
        if self.tty==1:
            self.HTO_prog=ttyS0comm.HTO_prog(self.tty_read)
        if self.func_gen==1:
            self.agilent=agilentcomm.Agilent_prog()
            if not self.agilent.check:
                self.func_gen=0
        self.choose()

    def choose(self):
        self.modeselect=Pmw.RadioSelect(self.root,
            buttontype = 'radiobutton',
            labelpos = 'n',
            label_text = 'Select Operation Mode:',
            hull_borderwidth = 2,
            hull_relief = 'ridge',
        )
        for text in ('Sweep','Fixed','Hopping'):
            self.modeselect.add('%s freq.' % text)
        self.modeselect.invoke('Fixed freq.')
        self.modeselect.pack(expand = 1, padx = 10, pady = 5)
        # Create the button box
        self.buttoninit = Pmw.ButtonBox(self.root)
        self.buttoninit.pack(fill = 'x', expand = 1, padx = 3, pady = 3)

        # Add buttons to the ButtonBox.
        self.buttoninit.add('About', command = self.about_gui)
        self.buttoninit.add('Close', command = self.close)
        self.buttoninit.add('Select', command = self.draw)

        # Make all the buttons the same width.
        self.buttoninit.alignbuttons()
        if hasattr(self,'st'):
            self.st['hull_height']=70
        else:
            self.infobox(70)
        self.st.appendtext('Olá Banzai\n\n')
        self.st.appendtext('Operando em modo: "%s"\n' % self.tipo)
        if self.tty==1:
            self.HTO_prog.st=self.st  
        else:
            self.st.appendtext('sem comunicação com Reflectômetro')

    def draw(self):
#        if self.modeselect.getvalue()=='Hopping Frequency':
#            self.st.clear()
#            self.st.appendtext('Still in construction!\n')
#        else:
        #destroy initial buttons
        self.buttoninit.destroy()
        self.modeselect.destroy()
        self.st.clear()
        self.st['hull_height']=150
        #warns class that is in operation mode
        self.oper=1
        find_proc()
        #read the selection
        if self.modeselect.getvalue()=='Sweep freq.':
            self.mode='sf'
            self.sf()
        elif self.modeselect.getvalue()=='Fixed freq.':
            self.mode='ff'
            self.ff()
        elif self.modeselect.getvalue()=='Hopping freq.':
            self.mode='hf'
            self.hf()
        self.entries_caption.append("Total time (ms)")
        self.keys_entries.append("time_dur")
        if self.tipo=="data":
            self.entries_default.append(170)
        else:
            self.entries_default.append(0.5)

        if self.tty==1:
            self.HTO_prog.mode=self.mode
        self.number_entries=len(self.keys_entries)
        self.entries={}
        for e in range(self.number_entries):
            self.makeentry(self.keys_entries[e],self.entries_caption[e],self.entries_default[e])
        Pmw.alignlabels(self.entries.values())

        self.makeradio_keys()
        self.number_radio=len(self.keys_radio)
        self.radio={}
        for e in range(self.number_radio):
            self.makeradio(self.keys_radio[e],self.radio_caption[e],self.radio_default[e],self.radio_objects[e])

        self.shotLabel()
        self.set_previous_config()
        self.buttons()
        
    def sf(self):
        self.entries_caption=['Sweep time (%ss): ' % u'\u03bc',
                              'Time between sweeps (%ss)' % u'\u03bc',
                            'Freq Start (8.2-13.4 GHz):',
                            'Freq End (8.2-13.4 GHz):',
                            'Angle (grad):','Start Time (ms)\n(0=Ôhmico):']
        self.entries_default=['50','7','8.2','13.4','5','0']
        self.keys_entries=['sweep','interv_sweep',
                            'freq_start','freq_end',
                            'angle','start_time']

    def ff(self):
        self.entries_caption=['Freq (8.2-13.4 GHz):',
                              'Angle (grad)','Start Time (ms)\n(0=Ôhmico):']
        self.entries_default=['9','5','0']
        self.keys_entries=['freq_start','angle','start_time']
        
    def hf(self):
        self.entries_caption=['Freq Table (8.2-13.4 GHz):',
                              'Step Time (%ss):' % u'\u03bc',
                              'Restart Table (ms):','Angle (grad)',
                              'Start Time (ms)\n(0=Ôhmico):']
        self.entries_default=['8.2,8.6,9,10,11','200','200','5','0']
        self.keys_entries=['freq_table','time_step',
                           'restart_table','angle','start_time']

    def makeradio_keys(self):
        self.keys_radio=['rate']
        self.radio_caption=['Acq Rate (MHz):']
        self.radio_objects=[['50','62.5','100','200']]
        self.radio_default=['50']

    def makeentry(self,key,caption, default):
        self.entries[key]=Pmw.EntryField(self.root,
            labelpos = 'w',
            label_text = caption,
            value= default)
        self.entries[key].pack(side= 'top', fill= 'x', expand=1, padx=10, pady=5)

    def makeradio(self,key,caption,default,options):
        self.radio[key] = Pmw.RadioSelect(self.root,
            buttontype = 'radiobutton',
            orient = 'horizontal',
            labelpos = 'w',
            command = None,
            label_text = caption,
#            hull_borderwidth = 2,
#            hull_relief = 'ridge',
        )
        for text in options:
            self.radio[key].add(text)
        self.radio[key].invoke(default)
        self.radio[key].pack(side= 'top', expand = 1, padx = 10, pady = 5)

    def buttons(self):
        # Create the button box
        self.buttonBox = Pmw.ButtonBox(self.root,labelpos = 'nw')
        self.buttonBox.pack(fill = 'x', expand = 1, padx = 3, pady = 3)

        # Add buttons to the ButtonBox.
        self.buttonBox.add('Default', command = self.set_default)
        self.buttonBox.add('Close', command = self.close)
        self.buttonBox.add('Stop Acq', command = find_proc)
        self.buttonBox.add('Set', command = Pmw.busycallback(self.setsetup))

        # Make all the buttons the same width.
        self.buttonBox.alignbuttons()

    def infobox(self,height=150):
        # Create the ScrolledText with headers.
        #'Helvetica', 'Times', 'Fixed', 'Courier' or 'Typewriter'
#        fixedFont = Pmw.logicalfont('Fixed',size=12)
        self.st = Pmw.ScrolledText(self.root,
                borderframe = 1,
                usehullsize = 1,
                hull_height = height,
                text_wrap='word',
#                text_font = fixedFont,
                text_padx = 4,
                text_pady = 4,
        )
        self.st.pack(side='bottom', padx = 5, pady = 5, fill = 'both', expand = 1)
        # Prevent users' modifying text
        self.st.configure(text_state = 'disabled')

    def shotLabel(self):
        self.shotframe=tk.Frame(self.root)
        self.shotframe.pack()

    def value(self,key):
        if key in self.entries.keys():
            try:
                return float(self.entries[key].get())
            except ValueError:
                try:
                    return map(float,self.entries[key].get().split(','))
                except IndexError:
                    return [float(self.entries[key].get())]
        elif key in self.radio.keys():
            return float(self.radio[key].getvalue())

    def findshot(self):
        if self.tipo=='data':
            self.shot=ls.read_shot()+1
        else:
            self.shot=ls.last_shot(self.tipo)+1

    def setsetup(self):
        self.check_values()
        self.angle=self.value('angle')
        if self.mode=='sf':
            self.sweep=self.value('sweep')
            self.f_start=self.value('freq_start')
            self.f_end=self.value('freq_end')
            self.interv_sweep=self.value('interv_sweep')
            if self.tty==1:
                self.HTO_prog.sf_prog(self.f_start,self.f_end,self.sweep)
            self.nchannels=15
        elif self.mode=='ff':
            self.f_start=self.value('freq_start')
            if self.tty==1:
                self.HTO_prog.ff_prog(self.f_start)
            self.nchannels=7
        elif self.mode=='hf':
            self.time_step = self.value('time_step')
            if self.tty==1:
                self.HTO_prog.hf_prog(self.freqs,self.value('restart_table'))
            self.nchannels=15
        pll=self.plls[int(self.value('rate'))]
        #SELF.DUR is duration in ms
        if self.tipo=="data":
            self.dur=170
            self.dur=self.value('time_dur')
        elif self.tipo=='cleaning_plasma':
            self.dur=50
        elif self.tipo=='mirror':
            nsamples=4096
            self.dur=self.value('time_dur')
        nsamples=self.dur*1000*self.value('rate')
        commandline='%s/bin/ref_acq ack nsamples %d file bindata channel %d pll %s' % (ref_folder,nsamples,self.nchannels,pll)
        self.st.appendtext('\n\nDensity probing:')
        if self.mode=='sf':
            self.st.appendtext('\n K: %g - %g (10^13)\n Ka: %g - %g (10^13)\n\n' % (f2ne(self.f_start*2),f2ne(self.f_end*2),f2ne(self.f_start*3),f2ne(self.f_end*3)))
        elif self.mode=='ff':
            self.st.appendtext('\n K: %g (10^13)\n Ka: %g (10^13)\n\n' % (f2ne(self.f_start*2),f2ne(self.f_start*3)))
        elif self.mode=='hf':
#            Ks=','.join(map(lambda u:'%s' % f2ne(u*2),self.freqs))
#            Kas=','.join(map(lambda u:'%s' % f2ne(u*3),self.freqs))
            self.st.appendtext('\n K: %s (10^13)\n Ka: %s (10^13)\n\n' % (','.join(map(lambda u:'%.2f' % f2ne(u*2),self.freqs)),','.join(map(lambda u:'%.2f' % f2ne(u*3),self.freqs))))
        #self.st.appendtext('\nCommand: %s\n\n' % (commandline))
        print '\nCommand: %s\n' % commandline
        find_proc()
        if self.func_gen==1:
            if self.mode=="ff":
                self.agilent.prog("ff",self.dur)
            elif self.mode=="sf":
                self.agilent.prog("sf",(self.sweep,self.value('interv_sweep'),self.dur))
            elif self.mode=="hf":
                self.agilent.prog("hf",(self.value('time_step'),self.dur))
            
        self.acq=acquisitonTask(self,commandline)
        
    def savesetup(self):
        self.findshot()
        self.st.appendtext('Shot number: %s' % self.shot)
        connection=sqlite3.connect(self.database)
        cursor=connection.cursor()
        for mode in ('sf','ff','hf'):
            for i in cursor.execute('SELECT shot FROM %s ORDER BY shot' % mode):
                if i==self.shot:
                    self.shot=00000
                    print 'PLEASE CORRECT THE SHOTNUMBER!!!'
                    self.st.appendtext('PLEASE CORRECT THE SHOTNUMBER!!!')
                    Pmw.displayerror('PLEASE UPDATE THE SHOTNUMBER!!!')
        self.today=time.strftime("%X %B %d %Y")
        data=[self.today,self.shot]
        ndata={}
        ndata['date']=self.today
        ndata['shot']=self.shot
        for e in self.keys_entries:
            data.append(self.value(e))
            if e in ('start_time','time_step','restart_table'):
                ndata[e]=int(self.value(e))
            elif e=='freq_table':
                try:
                    ndata[e]=','.join(map(str,self.value(e)))
                except TypeError:
                    ndata[e]=str(self.value(e))
            else:
                ndata[e]=self.value(e)
        for e in self.keys_radio:
            data.append(self.value(e))
            ndata[e]=self.value(e)
        if self.mode=='sf':
            cursor.execute('INSERT INTO sf VALUES (:date, :shot, :sweep, :freq_start, :freq_end, :angle, :rate, :start_time, :interv_sweep)', ndata)
        elif self.mode=='ff':
            cursor.execute('INSERT INTO ff VALUES (:date, :shot, :freq_start, :angle, :rate, :start_time)', ndata)
        elif self.mode=='hf':
            cursor.execute('INSERT INTO hf VALUES (:date, :shot, :freq_table, :time_step, :restart_table, :angle, :rate, :start_time)', ndata)
        connection.commit()
        connection.close()
        mdstreeTask(self)
        self.create_info_file(data)
        ref_acq.pos_acq(self.tipo)
        self.st.appendtext('\nShot %s done!\n\n' % self.shot)
        if self.tipo!='data':
            ls.add_shot(self.tipo)
        if self.tipo=='data':
            self.setsetup()

    def create_info_file(self,data):
        arq=open('%s/%s/%s_info.dat' % (ref_folder,self.tipo,self.shot),'w')
        arq.write('%s\n' % self.mode)
        arq.write('%s\n' % self.today)
        for e in self.keys_entries[:-1]:
            arq.write('%s: %s\n' % (e,self.value(e)))
        arq.write('rate: %s\n' % self.radio['rate'].getvalue())
        arq.write('time_dur: %s' % self.dur)
        arq.close()

    def check_values(self):
        interv_sweep_min=150
        if self.mode=='hf':
            self.freqs=self.value('freq_table')
            if type(self.freqs)==type(8.):
                self.freqs=[self.freqs]
            freq_end=max(self.freqs)
            freq_start=min(self.freqs)
            if self.value('time_step')<interv_sweep_min:
                self.entries['time_step'].setvalue(interv_sweep_min)
        else:
            if self.value('freq_start')<self.freq_min:
                self.entries['freq_start'].setvalue(self.freq_min)
                self.st.appendtext('minimum frequency: %s GHz\n' % self.freq_min)
            if self.value('freq_start')>self.freq_max:
                self.entries['freq_start'].setvalue(self.freq_max)
                self.st.appendtext('maximum frequency: %s GHz\n' % self.freq_max)
            if self.mode=='sf':
                if self.value('sweep')<self.sweep_min:
                    self.entries['sweep'].setvalue(self.sweep_min)
                    self.st.appendtext('sweep period from %s microseconds to 100 ms\n' % (self.sweep_min))
                if self.value('freq_start')>self.value('freq_end'):
                    self.entries['freq_start'].setvalue(self.freq_min)
                    self.entries['freq_end'].setvalue(self.freq_max)
                    self.st.appendtext('initial freq cannot be greater than last freq\n')
                if self.value('freq_end')<self.freq_min:
                    self.entries['freq_end'].setvalue(self.freq_min)
                    self.st.appendtext('minimum frequency: %s GHz\n' % self.freq_min)
                if self.value('freq_end')>self.freq_max:
                    self.entries['freq_end'].setvalue(self.freq_max)
                    self.st.appendtext('maximum frequency: %s GHz\n' % self.freq_max)

    def set_default(self):
        for e in range(self.number_entries):
            self.entries[self.keys_entries[e]].setvalue(self.entries_default[e])
        for e in range(self.number_radio):
            self.radio[self.keys_radio[e]].invoke(self.radio_default[e])

    def set_previous_config(self):
        connection=sqlite3.connect(self.database)
        cursor=connection.cursor()
        cursor.execute('SELECT * FROM %s ORDER BY shot' % self.mode)
        col_name_list = [tuple[0] for tuple in cursor.description]
        previous_config=cursor.fetchall()[-1]
        connection.close()
        for e in range(len(col_name_list)):
            param_name=col_name_list[e]
            param_config=previous_config[e]
            if param_name in self.keys_entries:
                self.entries[param_name].setvalue(param_config)
            if param_name in self.keys_radio:
                #print param_name,param_config,self.radio_objects,self.radio_objects[0]
                para=str(param_config)
                if '.0' in para:
                    para=para[:-2]
                param_index=self.radio_objects[0].index(para)
                self.radio[param_name].invoke(param_index)

    def close(self):
        if self.oper==1:
            self.st.exportfile('%s/logs/ref_%s_mode_%s.log' % (ref_folder,self.mode,time.strftime("%X_%B_%d_%Y")))
            self.st.clear()
            self.oper=0
            self.buttonBox.destroy()
            for key in self.entries.keys():
                self.entries[key].destroy()
            for key in self.radio.keys():
                self.radio[key].destroy()
            self.choose()
        elif self.oper==0:
            self.st.clear()
            self.st.appendtext("Tchau, Banzai!")
            bg=backgroundTask(self)
            find_proc()
            if self.tty==1:
                self.HTO_prog.close()
            if self.func_gen==1:
                self.agilent.turn_off()

    def about_gui(self):
        Pmw.aboutversion('0.95\n Mar 16 2014')
        Pmw.aboutcopyright('Author: Cassio H. S. Amador')
        Pmw.aboutcontact(
            'For more informations/bug reporting:\n' +
            '  email: cassioamador@yahoo.com.br'
        )
        self.about = Pmw.AboutDialog(self.root, applicationname = 'Ref Setup')
        self.about.withdraw()
        self.about.show()

def find_proc():
    lista=popen('ps -e | grep ref_acq').readlines()
    if len(lista)!=0:
        for i in lista:
            try:
                proc_id=int(i.split(' ')[1])
            except ValueError:
                proc_id=int(i.split(' ')[0])
            popen('kill %d' % proc_id)
            print '\nAcquisition Halted\n'
#            print proc_id

#CONSTANT TO CONVERT FREQUENCY AND DENSITY: DEN=convert*FREQ^2.
convert=0.012404425565580239
def f2ne(f):
    ne=convert*pow(f*1e9,2)*1e-19
#    print r'Frequency: %g GHz ; Density: %g 10^13 m^{-3}' % (f,ne)
    return ne

if __name__=='__main__':
    database='%s/ref.db' % ref_folder
    tipo='data'
    if len(argv)>=2:
        if argv[1]=='mirror':
            database='%s/ref_test.db' % ref_folder
            tipo='mirror'
        elif argv[1]=='clean':
            database='%s/ref_clean.db' % ref_folder
            tipo='cleaning_plasma'
        elif argv[1]=='kill':
            tipo='kill'
    root=tk.Tk()
    root.title('Ref setup')
    Pmw.initialise(fontScheme='pmw2')
    ref=Refsetup(root,database,tipo)
    # root is your root window
    root.mainloop()

#!/usr/bin/python
# -*- coding: utf-8 -*-

import Tkinter as tk
import threading
import time
import Pmw
import sqlite3
from os import getcwd,popen,system,environ,write,path
from sys import argv

import last_shot as ls
import ttyS0comm
import agilentcomm
import check_ref
import ref_acq
import MDSplus
import numpy as np

lugar='/home/GRS/TCABR'

#if HTO is not ON, put tty=0, for test purposes.
tty=1
#if Function Generator is OFF, agilent=0.
agilent=1

#THREADING TO MAKE CHILD TIME COUNTER
class backgroundTask(threading.Thread):
    def __init__(self,pai):
        threading.Thread.__init__(self)
        self.pai=pai
        self.setDaemon(True)
        self.start()

    def run(self):
        self.pai.st.appendtext('\n\t')
        for i in ('...'):
            self.pai.st.appendtext('\t%s' % i)
            time.sleep(0.2)
        self.pai.root.destroy()

class acquisitonTask(threading.Thread):
    def __init__(self,father,command):
        threading.Thread.__init__(self)
        self.com=command
        self.father=father
        self.setDaemon(True)
        self.start()
    def run(self):
        #returns True if acquisition was successfull
        b=ref_acq.ref_acq(self.com)
        if b:
            self.father.savesetup()

class Refsetup:
    def __init__(self,root,database,tipo='data'):
        global agilent,tty
#        if tipo=="kill":
#            find_proc()
#            check_ref.kill()
#            exit()
#        if check_ref.check_ref():
#            check_ref.lock_ref()
        self.root=root
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.plls={50:11,62.5:9,100:7,200:1}
        self.database=database
        self.tipo=tipo
        self.oper=0
        if not path.exists("/dev/pcie0"):
            system("sudo /home/GRS/driver_ATCA/driver/mknod.sh")
            system("sleep 1")
        if tty==1:
            self.HTO_prog=ttyS0comm.HTO_prog()
        if agilent==1:
            self.agilent=agilentcomm.Agilent_prog()
            if not self.agilent.check:
                agilent=0
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
        if tty==1:
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

        if tty==1:
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

        self.buttons()
        
    def sf(self):
        self.entries_caption=['Sweep time (%ss): ' % u'\u03bc',
                              'Time between sweeps (%ss)' % u'\u03bc',
                            'Freq Start (8.2-13.4 GHz):',
                            'Freq End (8.2-13.4 GHz):',
                            'Angle (grad):','Start Time (ms)\n(0=Ôhmico):']
        self.entries_default=['8','7','8.2','13.4','5','0']
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
        self.entries_default=['8.2,12,9,10,11','5000','200','5','0']
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
        self.buttonBox.add('Default', command = self.default)
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
            if tty==1:
                self.HTO_prog.sf_prog(self.f_start,self.f_end,self.sweep)
            self.nchannels=15
        elif self.mode=='ff':
            self.f_start=self.value('freq_start')
            if tty==1:
                self.HTO_prog.ff_prog(self.f_start)
            self.nchannels=7
        elif self.mode=='hf':
            self.time_step = self.value('time_step')
            if tty==1:
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
        commandline='%s/ref_acq ack nsamples %d file bindata channel %d pll %s' % (lugar,nsamples,self.nchannels,pll)
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
        if agilent==1:
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
        try:
            self.populate_MDSTree()
        except:
            pass
        self.create_info_file(data)
        ref_acq.pos_acq(self.tipo)
        self.st.appendtext('\nShot %s done!\n\n' % self.shot)
        if self.tipo!='data':
            ls.add_shot(self.tipo)
        if self.tipo=='data':
            self.setsetup()

    def create_info_file(self,data):
        arq=open('%s/%s/%s_info.dat' % (lugar,self.tipo,self.shot),'w')
        arq.write('%s\n' % self.mode)
        arq.write('%s\n' % self.today)
        for e in self.keys_entries[:-1]:
            arq.write('%s: %s\n' % (e,self.value(e)))
        arq.write('rate: %s\n' % self.radio['rate'].getvalue())
        arq.write('time_dur: %s' % self.dur)
        arq.close()

    def populate_MDSTree(self):
        if self.tipo!="data":
            return
        node_name = ["banda_k", "banda_ka", "mirnov", "trigger"]
        tree_name = "tcabr_ref"
        tree = MDSplus.Tree(tree_name, -1)
        tree.createPulse(self.shot)
        tree = MDSplus.Tree(tree_name, self.shot)
        #Populate signals node
        for channel in range(3):
            node = tree.getNode("\\%s.physicalch" % node_name[channel] )
            node.putData(MDSplus.Int8(channel))
            node = tree.getNode("\\%s.signal" % node_name[channel] )
            data = MDSplus.Int16Array(np.fromfile("bindata_%i.bin" %(channel+1),dtype=np.int16))
            data.setUnits("Counts")
            dim = MDSplus.Range(0, (data.data().size-1)*1e-3/self.value('rate'), 1e-3/self.value('rate'))
            dim.setUnits("ms")
            signal = MDSplus.Signal(data, None, dim)
            node.putData(signal)
        if self.mode!='ff':
            channel = 3
            node = tree.getNode("\\%s.physicalch" % node_name[channel] )
            node.putData(MDSplus.Int8(channel))
            node = tree.getNode("\\%s.signal" % node_name[channel] )
            data = MDSplus.Int16Array(np.fromfile("bindata_%i.bin" %(channel+1),dtype=np.int16))
            data.setUnits("Counts")
            dim = MDSplus.Range(0, (data.data().size-1)*1e-3/self.value('rate') , 1e-3/self.value('rate'))
            dim.setUnits("ms")
            signal = MDSplus.Signal(data, None, dim)
            node.putData(signal)
        #Populate parameter node
        #Commons parameters
        node = tree.getNode("\\ref_parameter.samples")
        node.putData(MDSplus.Int32(data.data().size))
        node = tree.getNode("\\ref_parameter.rate")
        rate = MDSplus.Float32(1e6*self.value('rate'))
        rate.setUnits("Hz")
        node.putData(rate)
        node = tree.getNode("\\ref_parameter.angle" )
        angle = MDSplus.Float32(self.value('angle'))
        angle.setUnits("degrees")
        node.putData(self.angle)
        #Mode dependent parameters
        node = tree.getNode("\\ref_parameter.refmode")
        node.putData(self.mode)
        if self.mode=='ff':
            node = tree.getNode("\\fixedfreq.frequency")
            freq = MDSplus.Float32(self.f_start)
            freq.setUnits("GHz")
            node.putData(freq)
        elif self.mode=='hf':
            node = tree.getNode("\\hopping_freq.freq_table")
            freq_table = MDSplus.Float32(np.array(self.freqs))
            freq_table.setUnits("GHz")
            node.putData(freq_table)
            node = tree.getNode("\\hoppingfreq.restart_time")
            restart_table = MDSplus.Float32(self.value('restart_table'))
            restart_table.setUnits("ms")
            node.putData(restart_table)
            node = tree.getNode("\\hoppingfreq.time_step")
            time_step = MDSplus.Float32(self.time_step)
            time_step.setUnits("µs")
            node.putData(time_step)
        elif self.mode=='sf':
            node = tree.getNode("\\sweepfreq.freq_start")
            freq_start = MDSplus.Float32(self.f_start)
            freq_start.setUnits("GHz")
            node.putData(freq_start)
            node = tree.getNode("\\sweepfreq.freq_end")
            freq_end = MDSplus.Float32(self.f_end)
            freq_end.setUnits("GHz")
            node.putData(freq_end)
            node = tree.getNode("\\sweepfreq.sweep_time")
            sweep_time = MDSplus.Float32(self.sweep)
            sweep_time.setUnits("µs")
            node.putData(sweep_time)
            node = tree.getNode("\\sweepfreq.interv_sweep")
            interv_sweep = MDSplus.Float32(self.interv_sweep)
            interv_sweep.setUnits("µs")
            node.putData(interv_sweep)

    def check_values(self):
        sweep_min=8
        interv_sweep_min=150
        freq_min=8.2
        freq_max=13.4
        if self.mode=='hf':
            self.freqs=self.value('freq_table')
            if type(self.freqs)==type(8.):
                self.freqs=[self.freqs]
            freq_end=max(self.freqs)
            freq_start=min(self.freqs)
            if self.value('time_step')<interv_sweep_min:
                self.entries['time_step'].setvalue(interv_sweep_min)
        else:
            if self.value('freq_start')<freq_min:
                self.entries['freq_start'].setvalue(freq_min)
                self.st.appendtext('minimum frequency: %s GHz\n' % freq_min)
            if self.value('freq_start')>freq_max:
                self.entries['freq_start'].setvalue(freq_max)
                self.st.appendtext('maximum frequency: %s GHz\n' % freq_max)
            if self.mode=='sf':
                if self.value('sweep')<sweep_min:
                    self.entries['sweep'].setvalue(sweep_min)
                    self.st.appendtext('sweep period from %s microseconds to 100 ms\n' % (sweep_min))
                if self.value('freq_start')>self.value('freq_end'):
                    self.entries['freq_start'].setvalue(freq_min)
                    self.entries['freq_end'].setvalue(freq_max)
                    self.st.appendtext('initial freq cannot be greater than last freq\n')
                if self.value('freq_end')<freq_min:
                    self.entries['freq_end'].setvalue(freq_min)
                    self.st.appendtext('minimum frequency: %s GHz\n' % freq_min)
                if self.value('freq_end')>freq_max:
                    self.entries['freq_end'].setvalue(freq_max)
                    self.st.appendtext('maximum frequency: %s GHz\n' % freq_max)

    def default(self):
        for e in range(self.number_entries):
            self.entries[self.keys_entries[e]].setvalue(self.entries_default[e])
        for e in range(self.number_radio):
            self.radio[self.keys_radio[e]].invoke(self.radio_default[e])

    def close(self):
        if self.oper==1:
            self.st.exportfile('%s/logs/ref_%s_mode_%s.log' % (lugar,self.mode,time.strftime("%X_%B_%d_%Y")))
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
            check_ref.free_ref()
            if tty==1:
                self.HTO_prog.close()
            if agilent==1:
                self.agilent.turn_off()

    def about_gui(self):
        Pmw.aboutversion('0.9\n Jan 30 2013')
        Pmw.aboutcopyright('Author: Cassio H. S. Amador')
        Pmw.aboutcontact(
            'For more information/bug reporting:\n' +
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
    database='%s/ref.db' % lugar
    tipo='data'
    if len(argv)>=2:
        if argv[1]=='mirror':
            database='%s/ref_test.db' % lugar
            tipo='mirror'
        elif argv[1]=='clean':
            database='%s/ref_clean.db' % lugar
            tipo='cleaning_plasma'
        elif argv[1]=='kill':
            tipo='kill'
    root=tk.Tk()
    root.title('Ref setup')
    Pmw.initialise(fontScheme='pmw2')
    ref=Refsetup(root,database,tipo)
    # root is your root window
    root.mainloop()

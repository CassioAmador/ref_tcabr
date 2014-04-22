# -*- coding: utf-8 -*-

import MDSplus
import numpy as np

def populate_MDSTree(father_class):
    try:
        if father_class.tipo!="data":
            return
        node_name = ["banda_k", "banda_ka", "mirnov", "trigger"]
        tree_name = "tcabr_ref"
        tree = MDSplus.Tree(tree_name, -1)
        tree.createPulse(father_class.shot)
        tree = MDSplus.Tree(tree_name, father_class.shot)
        #Populate signals node
        for channel in range(3):
            node = tree.getNode("\\%s.physicalch" % node_name[channel] )
            node.putData(MDSplus.Int8(channel))
            node = tree.getNode("\\%s.signal" % node_name[channel] )
            data = MDSplus.Int16Array(np.fromfile("bindata_%i.bin" %(channel+1),dtype=np.int16))
            data.setUnits("Counts")
            dim = MDSplus.Range(0, (data.data().size-1)*1e-3/father_class.value('rate'), 1e-3/father_class.value('rate'))
            dim.setUnits("ms")
            signal = MDSplus.Signal(data, None, dim)
            node.putData(signal)
        if father_class.mode!='ff':
            channel = 3
            node = tree.getNode("\\%s.physicalch" % node_name[channel] )
            node.putData(MDSplus.Int8(channel))
            node = tree.getNode("\\%s.signal" % node_name[channel] )
            data = MDSplus.Int16Array(np.fromfile("bindata_%i.bin" %(channel+1),dtype=np.int16))
            data.setUnits("Counts")
            dim = MDSplus.Range(0, (data.data().size-1)*1e-3/father_class.value('rate') , 1e-3/father_class.value('rate'))
            dim.setUnits("ms")
            signal = MDSplus.Signal(data, None, dim)
            node.putData(signal)
        #Populate parameter node
        #Commons parameters
        node = tree.getNode("\\ref_parameter.samples")
        node.putData(MDSplus.Int32(data.data().size))
        node = tree.getNode("\\ref_parameter.rate")
        rate = MDSplus.Float32(1e6*father_class.value('rate'))
        rate.setUnits("Hz")
        node.putData(rate)
        node = tree.getNode("\\ref_parameter.angle" )
        angle = MDSplus.Float32(father_class.value('angle'))
        angle.setUnits("degrees")
        node.putData(father_class.angle)
        #Mode dependent parameters
        node = tree.getNode("\\ref_parameter.refmode")
        node.putData(father_class.mode)
        if father_class.mode=='ff':
            node = tree.getNode("\\fixedfreq.frequency")
            freq = MDSplus.Float32(father_class.f_start)
            freq.setUnits("GHz")
            node.putData(freq)
        elif father_class.mode=='hf':
            node = tree.getNode("\\hopping_freq.freq_table")
            freq_table = MDSplus.Float32(np.array(father_class.freqs))
            freq_table.setUnits("GHz")
            node.putData(freq_table)
            node = tree.getNode("\\hoppingfreq.restart_time")
            restart_table = MDSplus.Float32(father_class.value('restart_table'))
            restart_table.setUnits("ms")
            node.putData(restart_table)
            node = tree.getNode("\\hoppingfreq.time_step")
            time_step = MDSplus.Float32(father_class.time_step)
            time_step.setUnits("µs")
            node.putData(time_step)
        elif father_class.mode=='sf':
            node = tree.getNode("\\sweepfreq.freq_start")
            freq_start = MDSplus.Float32(father_class.f_start)
            freq_start.setUnits("GHz")
            node.putData(freq_start)
            node = tree.getNode("\\sweepfreq.freq_end")
            freq_end = MDSplus.Float32(father_class.f_end)
            freq_end.setUnits("GHz")
            node.putData(freq_end)
            node = tree.getNode("\\sweepfreq.sweep_time")
            sweep_time = MDSplus.Float32(father_class.sweep)
            sweep_time.setUnits("µs")
            node.putData(sweep_time)
            node = tree.getNode("\\sweepfreq.interv_sweep")
            interv_sweep = MDSplus.Float32(father_class.interv_sweep)
            interv_sweep.setUnits("µs")
            node.putData(interv_sweep)
    except:
        import sys, time
        log=open("error_mdsplus.txt",'a')
        log.write(time.strftime("%X_%B_%d_%Y\n"))
        log.write("%s\n" % sys.exc_info()[1])
        log.write("**************\n")

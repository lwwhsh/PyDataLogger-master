#!/usr/bin/env python
"""
xafs scan
based on EpicsApps.StepScan.

"""
import numpy as np

from .stepscan import StepScan
from .positioner import Positioner
from .saveable import Saveable

from math import sqrt

XAFS_K2E = 3.809980849311092

def etok(energy):
    return np.sqrt(energy/XAFS_K2E)

def ktoe(k):
    return k*k*XAFS_K2E

class ScanRegion(Saveable):
    def __init__(self, start, stop, npts=None,
                 relative=True, e0=None, use_k=False,
                 dtime=None, dtime_final=None, dtime_wt=1):
        Saveable.__init__(self, start, stop, npts=npts,
                          relative=relative,
                          e0=e0, use_k=use_k,
                          dtime=dtime,
                          dtime_final=dtime_final,
                          dtime_wt=dtime_wt)

class XAFS_Scan(StepScan):
    def __init__(self, label=None, energy_pv=None, read_pv=None,
                 extra_pvs=None,  e0=0, **kws):
        self.label = label
        self.e0 = e0
        self.energies = []
        self.regions = []
        StepScan.__init__(self, **kws)
        self.dwelltime = []
        self.energy_pos = None
        self.set_energy_pv(energy_pv, read_pv=read_pv, extra_pvs=extra_pvs)

    def set_energy_pv(self, energy_pv, read_pv=None, extra_pvs=None):
        # LWW disable maybe not use it. # self.energy_pv = energy_pv
        # LWW disable maybe not use it. # self.read_pv = read_pv
        if energy_pv is not None:
            self.energy_pos = Positioner(energy_pv, label='Energy',
                                         extra_pvs=extra_pvs)
            self.positioners = []
            self.add_positioner(self.energy_pos)
        if read_pv is not None:
            self.add_counter(read_pv, label='Energy_readback')

    def add_region(self, start, stop, step=None, npts=None,
                   relative=True, use_k=False, e0=None,
                   dtime=None, dtime_final=None, dtime_wt=1):
        """add a region to an EXAFS scan.
        Note that scans must be added in order of increasing energy
        """
        ''' PLS BL10C calculation, but we change to Matt Newvill ecuation!
        if e0 is None:
            e0 = self.e0
        if dtime is None:
            dtime = self.dtime
        self.e0 = e0
        self.dtime = dtime

        if npts is None and step is None:
            print 'add_region needs start, stop, and either step on npts'
            return

        # calculate etok region are use_k case
        # Eo + (((step*N) + (sqrt(start) * 0.512)) / 0.512) ** 2
        if use_k:
            ii = 0
            a=b=c = float()
            a = sqrt(start) * 0.512  # a = np.sqrt(start) * 0.512
            b = (stop / 0.512) ** 2
            c = ((step + a) / 0.512) ** 2

            en_arr = np.zeros(2000)

            if c > stop:
                print '+++ k space value has something wrong value +++\n'
                return

            en_arr[ii] = e0 + c

            while c < stop:
                ii += 1
                c = (((step * ii) + a) / 0.512) ** 2
                en_arr[ii] = e0 + c

            npts = ii + 1

        # ev mode and relative region case
        elif relative:
           en_arr = list(np.linspace(start, stop, npts))
           for i, v in enumerate(en_arr):
                en_arr[i] = e0 + v
        '''

        if e0 is None:
            e0 = self.e0
        if dtime is None:
            dtime = self.dtime
        self.e0 = e0
        self.dtime = dtime

        if npts is None and step is None:
            print 'add_region needs start, stop, and either step on npts'
            return

        if step is not None:
            if not use_k:
                npts = 1 + int(0.1 + abs(stop - start)/step)
                en_arr = list(np.linspace(start, stop, npts))
            else:
                npts = 1 + int(0.1 + abs(etok(stop) - etok(start)) / step)
                en_arr = list(np.linspace(etok(start), etok(stop), npts))

        # note: save region definition using npts here,
        # even though npts may be reduced below, this set
        # will provide reproducible results, and so can be
        # savd for later re-use.
        self.regions.append(ScanRegion(start, stop, npts=npts,
                                       relative=relative,
                                       e0=e0, use_k=use_k,
                                       dtime=dtime,
                                       dtime_final=dtime_final,
                                       dtime_wt=dtime_wt))

        if use_k:
            for i, k in enumerate(en_arr):
                en_arr[i] = e0 + ktoe(k)
        elif relative:
            for i, v in enumerate(en_arr):
                en_arr[i] = e0 + v


        # note: save region definition using npts here,
        # even though npts may be reduced below, this set
        # will provide reproducible results, and so can be
        # savd for later re-use.
        self.regions.append(ScanRegion(start, stop, npts=npts,
                                       relative=relative,
                                       e0=e0, use_k=use_k,
                                       dtime=dtime,
                                       dtime_final=dtime_final,
                                       dtime_wt=dtime_wt))

        # check that all energy values in this region are greater
        # than previously defined regions
        en_arr.sort()
        if len(self.energies) > 0:
            en_arr = [e for e in en_arr if e > max(self.energies)]

        npts   = len(en_arr)

        dt_arr = [dtime]*npts
        # allow changing counting time linear or by a power law.
        if dtime_final is not None and dtime_wt > 0:
            _vtime = (dtime_final-dtime)*(1.0/(npts-1))**dtime_wt
            dt_arr= [dtime + _vtime *i**dtime_wt for i in range(npts)]
        self.energies.extend(en_arr)
        self.dwelltime.extend(dt_arr)
        self.energy_pos.array = np.array(self.energies)

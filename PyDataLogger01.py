#!/usr/bin/env python
"""
This program is simple XAFS scan with PyQt GUI
Scan core system use pyscan made by Dr. Matt newvill
and XAFS database also use inside larch code.
--------------------------------------------------------------
Copyright (c) 2015 Woulwoo Lee. All rights reserved.

 This program or module is free software: you can redistribute it and/or
 modify it under the terms of the GNU General Public License as published
 by the Free Software Foundation, either version 2 of the License, or
 version 3 of the License, or (at your option) any later version. It is
 provided for educational purposes and is distributed in the hope that
 it will be useful, but WITHOUT ANY WARRANTY; without even the implied
 warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
 the GNU General Public License for more details.
--------------------------------------------------------------
@author: Woulwoo Lee - PAL/POSTECH (lww@postech.ac.kr)
@version: 1.0
@Created: Aug 12 15:41:15 2015
--------------------------------------------------------------
 Modified ABC-protocol: Currently for 3 channel data...
     z,devid_string,a,123.4,b,-345.345,c,3434...
"""

# Import necessary modules
import sys
import time
import logging
import Queue
from PyQt4 import QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import numpy as np
import pyqtgraph as pg
import PyDataLogger16GUI # import PyDataLogger01GUI
import epics
from epics.devices.scaler import Scaler
import lib as scan
import sqlite3
import threading
import re

PACKETS = Queue.Queue()
MSGQUE  = Queue.Queue()
BUFFER_SIZE = 2000

e0Name     = 'mobiis:m4'
BEAM       = 'G:BEAMCURRENT'
COUNT_NAME = 'HFXAFS:scaler1'


class DispEnergy(QObject, threading.Thread):
    def __init__(self, dispSRBeam=QLCDNumber, dispEnergy=QLCDNumber,
                 beamName='G:BEAMCURRENT', e0name='mobiis:m4'):
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.dispBeam = dispSRBeam
        self.dispEnergy = dispEnergy
        self.beamPV = epics.PV(pvname=beamName)
        self.energyPV = epics.PV(pvname=e0name+'.RBV')
        epics.poll(0.001, 1.0)
        try:
            self.dispBeam.display(round(self.beamPV.get(), 2))
        except:
            pass
        try:
            self.dispEnergy.display(round(self.energyPV.get(), 2))
        except:
            pass

        self.beamPV.add_callback(self.beamCallbackFunc)
        self.energyPV.add_callback(self.energyCallbackFunc)

    def run(self):
        time.sleep(0.1)

    def beamCallbackFunc(self, pvname=None, value=None, **kw):
        self.dispBeam.display( round(value, 2) )

    def energyCallbackFunc(self, pvname=None, value=None, **kw):
        epics.poll()
        self.dispEnergy.display( round(value, 2) )


# monitor scalers class, generated emit
class DispCount(QObject, threading.Thread):
    def __init__(self, cntName='HFXAFS:scaler1_',
                 i0=QLCDNumber, it=QLCDNumber, iF=QLCDNumber, ir=QLCDNumber):
        QObject.__init__(self)
        threading.Thread.__init__(self)

        self.cntName =cntName
        self.i0 = i0
        self.it = it
        self.iF = iF
        self.ir = ir

        self.countPV = epics.PV(self.cntName+'_calc2')
        scalerAttrs = ('calc1','calc2','calc3','calc4','calc5','calc6','calc7','calc8')
        self.scalerDev = epics.Device(prefix=self.cntName+'_', delim='',
                                      attrs=scalerAttrs, mutable=False)
        epics.poll()

        try:
            epics.poll(0.001, 1.0)
            val = self.scalerDev.get_all()
            self.i0.display(val['calc2'])
            self.it.display(val['calc3'])
            self.iF.display(val['calc4'])
            self.ir.display(val['calc5'])
        except: pass

        self.countPV.add_callback(self.countersCallbackFunc,run_now=True)


    def run(self):
        time.sleep(0.1)

    def countersCallbackFunc(self, value=None, **kw):
        # ch1: Timer, Ch2:Io, Ch3:It, Ch4:If, Ch5:If, Ch6~Ch8:CH6~CH8
        # BL10C2 use Ch2~Ch5 channels.
        # this callback linked Ch2(HFXAFS:scaler1_calc2) PV
        epics.poll()
        val = self.scalerDev.get_all()
        self.i0.display(value)
        self.it.display(val['calc3'])
        self.iF.display(val['calc4'])
        self.ir.display(val['calc5'])


# for test.
class TestButton(QObject, threading.Thread):
    def __init__(self, label=QLabel, bt=QPushButton):
        # Initialize the DispEnergy as a QObject so it can emit signals
        QObject.__init__(self)
        threading.Thread.__init__(self)
        self.label = label
        self.bt = bt

        self.connect(self.bt, SIGNAL("clicked()"), self.updateLabel)

    def run(self):
        time.sleep(0.1)

    def updateLabel(self):
        print time.strftime('%x %X', time.localtime())
        self.label.setText(time.strftime('%x %X', time.localtime()))


# class MyMainWindow(QMainWindow, PyDataLogger01GUI.Ui_MainWindow):
class MyMainWindow(QMainWindow, PyDataLogger16GUI.Ui_MainWindow):
    # Constructor function
    def __init__(self, parent=None, packets=PACKETS):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)

        self.dir_ = str('/home/data/2015')
        self.dataDir()

        self.fileName = str('/home/data/2015/DDD.001')

        self.dataView.setTitle('Sampled Signals graph...')
        self.dataView.setLabel('left', 'count', units='count')
        self.dataView.setLabel('bottom', 'energy', units='eV')
        self.dataView.showGrid(True, True) # showGrid(x=None, y=None, alpha=None)

        # for thread test with QWidgets.
        self.testThread = TestButton(self.labelOkay, self.pbOkay)
        self.testThread.run()

        # initialize only one plot.The other datas plot added programaticaly.
        self.plotdata   = []
        for i in range(11):
            self.plotdata = [self.dataView.plot() for n in xrange(11)]

        self.scanCnt = int(0)
        self.npts = 0
        # pen color list
        self.pens=[(255,0,0),(255,165,0),(255,255,0),
                   (0,255,0),(0,0,255),(125,38,205),
                   (255,231,186),(0,250,154),(84,139,84),
                   (165,42,42)]

        self.yyd = []
        self.cpt = None
        self.darkCurrent = []

        edges_list = ('K', 'L3', 'L2', 'L1', 'M5')

        self.packets = packets
        self.actionAbout.triggered.connect(self.aboutHelp)
        self.actionDir.triggered.connect(self.dataDir)

        self.actionExit.triggered.connect(myApp.quit) # LWW qApp.quit)

        self.connect(self.btnStartScan, SIGNAL("clicked()"), self.scanStartBt)
        self.connect(self.btnStopScan, SIGNAL("clicked()"), self.scanStop)
        self.connect(self.showItems, SIGNAL("currentIndexChanged(int)"), self.replotGraph)
        self.connect(self.btnE0, SIGNAL("clicked()"), self.moveE0)
        self.connect(self.history, SIGNAL("valueChanged(int)"), self.replotGraph)

        self.makeElementList()
        self.connect(self.elements, SIGNAL("currentIndexChanged(int)"), self.onEdgeChoice)
        self.connect(self.doubleE0, SIGNAL("valueChanged(double)"), self.updateElementList)

        self.dispBeamThread = DispEnergy(dispSRBeam=self.dispSRbeam,
                                         dispEnergy=self.dispEnergy,
                                         beamName=BEAM, e0name=e0Name)
        self.dispBeamThread.start()

        self.dispCountThread = DispCount(cntName=COUNT_NAME,
                                         i0=self.dispIo, it=self.dispIt,
                                         iF=self.dispIf, ir=self.dispIr)
        self.dispCountThread.start()

        # region calculation----------------------------------------------------------
        self.reg_settings = []
        self.reg_settings.append((self.doublePre1Start,  self.doublePre1Stop,
                                  self.doublePre1Step,   self.doublePre1Time,
                                  self.labelPre1Units))
        self.reg_settings.append((self.doublePre2Start,  self.doublePre2Stop,
                                  self.doublePre2Step,   self.doublePre2Time,
                                  self.labelPre2Units))
        self.reg_settings.append((self.doubleXANESStart, self.doubleXANESStop,
                                  self.doubleXANESStep,  self.doubleXANESTime,
                                  self.labelXANESUnits))
        self.reg_settings.append((self.doubleXAFS1Start, self.doubleXAFS1Stop,
                                  self.doubleXAFS1Step,  self.doubleXAFS1Time,
                                  self.XAFS1Units))
        self.reg_settings.append((self.doubleXAFS2Start, self.doubleXAFS2Stop,
                                  self.doubleXAFS2Step,  self.doubleXAFS2Time,
                                  self.XAFS2Units))
        self.reg_settings.append((self.doubleXAFS3Start, self.doubleXAFS3Stop,
                                  self.doubleXAFS3Step,  self.doubleXAFS3Time,
                                  self.XAFS3Units))

        self.selectRegion.currentIndexChanged.connect(self.regionChanged)
        # for table test.
        # self.tableTest.cellClicked.connect(self.tableTestClicked)
        self.regionChanged(self.selectRegion.currentIndex())

        try:
            self.doubleE0.setValue(epics.caget(e0Name+'.RBV', timeout=30))
        except:
            pass
        self.updateElementList()

        self.t = QTimer()
        self.t.timeout.connect(self.updateData)
        self.t.start(10)

        self.plotFlag = False

        self.statusMsg("DataLogging Server..." )
        self.lineEditCMD.setFocus()
        self.tabControl.setCurrentIndex(0)

    def updateElementList(self, evt=7112.0):
        con = sqlite3.connect("xrayref.db")
        cursor = con.cursor()
        try:
            sqlStr = "SELECT element FROM xray_levels WHERE absorption_edge='%s' AND iupac_symbol='K'" %(self.doubleE0.value())
            cursor.execute(sqlStr)
            elementName = cursor.fetchall()

            a = elementName.pop(0)
            if isinstance(a[0], unicode):
                index = self.elements.findText(a[0])
                if index is not -1:
                    self.elements.setCurrentIndex(index)
        except:
            pass
        finally:
            cursor.close()
            con.close()

    def makeElementList(self):
        con = sqlite3.connect("xrayref.db")
        cursor = con.cursor()
        cursor.execute("SELECT element FROM xray_levels WHERE iupac_symbol='K'")
        elementName = cursor.fetchall()
        cursor.close()
        con.close()

        for i, in elementName:
            self.elements.addItem(i)

    def regionChanged(self, value):
        for r in self.reg_settings[:value+2]:
            for i,a in enumerate(r):
                a.setEnabled(True)

        for r in self.reg_settings[value+2:]:
            for i,a in enumerate(r):
                a.setEnabled(False)

    def moveE0(self):
        quit_msg = """Are you sure you want move to e0?
                   You need energy calibration after move e0!!"""
        reply = QtGui.QMessageBox.question(self, 'Move e0 Message',
                         quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            try:
                epics.caput(e0Name, self.doubleE0.value())
            except:
                pass
        else:
            pass

    # Function reimplementing Key Press, Mouse Click and Resize Events
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            try:
                self.scanStop()
            except:
                pass
            self.close()

    def mouseDoubleClickEvent(self, event):
        try:
            self.scanStop()
        except:
            pass
        self.close()

    def scanStop(self):
        try:
            self.numberOfscans.setValue(1)
            self.scanthread.abort = True
        except:
            pass

        self.btnStartScan.setEnabled(True)

    def statusMsg(self, message):
         self.statusBar().showMessage(message)

    def updateData(self):
        val = self.packets.qsize()
        if val != 0:
            try:
                (sockID, datastr) = self.packets.get_nowait()
                self.packets.task_done()

                if datastr is not 'F':

                    self.cpt = datastr

                    xnp = np.array(self.scanthread.counters[0].buff) - self.scanthread.e0
                    self.plotdata[0].setData(x=xnp,
                                             y=np.array(self.scanthread.counters[self.showItems.currentIndex()].buff),
                                             clear=False, symbol='o', pen='w',
                                             symbolSize=4, pxMode=True)

                #for nulti scan need check number of scan
                if datastr is 'F' and self.numberOfscans.value() > 1:
                    time.sleep(0.1)
                    self.scanStart() # self.scanthread.start()
                    self.numberOfscans.setValue(self.numberOfscans.value()-1)

            finally:
                if datastr is not 'F':
                    self.statusMsg("[%s / %s],   %s[eV]" \
                                   %(datastr, self.npts,
                                     self.scanthread.counters[0].buff[-1]))

        val2 = MSGQUE.qsize()
        if val2 != 0:
            self.statusMsg(self.getGlobalStatusMsg())

    def aboutHelp(self):
        QMessageBox.about(self, "About XAFS DataLogger Terminal",
                          "\r\nA Simple Data Logging Terminal Program based on PyQt4\r\n",)

    def dataDir(self):
        dir__ = str(QtGui.QFileDialog.getExistingDirectory(None,
                                            'Select Your Data Directory',
                                            '/home/data',
                                            QtGui.QFileDialog.ShowDirsOnly))
        if dir__ is not '':
            self.dir_ = dir__

    def exitFile(self):
        try:
            self.scanStop()
        except:
            pass

        self.close()

    def getGlobalStatusMsg(self):
        msg = str()
        msg = MSGQUE.get_nowait()
        MSGQUE.task_done()
        return msg

    def check_keyword(self, msg):
        #if msg.startsWith('!q'):
        #    self.close()
        pass

    def replotGraph(self):
        if self.scanCnt is not 0:
            for i, plotCh in enumerate(self.plotdata):
                plotCh.clear() # self.dataView.plot(clear = True)

            if self.history.value() is not 1:
                yydCp = []

                yydCp = self.yyd[-1 * int(self.history.value() - 1):]

                for i in range(len(yydCp)):
                    self.plotdata[i+1].setData(x=yydCp[i][0]-self.scanthread.e0,
                                               y=yydCp[i][self.showItems.currentIndex()],
                                               clear=False, pen=self.pens[i],
                                               symbol=None)

    def measureDarkMsg(self):
        dark_msg = "Are you want measure dark current?"
        reply = QMessageBox.question(self, 'Message',
                     dark_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            QMessageBox.warning(self, 'Close shutter message', ' Please CLOSE shutter ! ' )
            self.measureBackground()
            QMessageBox.warning(self, 'Open shutter message', ' Please OPEN shutter ! ' )

        return reply

    def measureBackground(self):
        s1 = Scaler(COUNT_NAME)
        epics.poll()
        s1.OneShotMode()
        s1.Count(ctime=10.0, wait=True)
        epics.poll()
        backGroundData = s1.Read(use_calc=True)
        backGround1secData = [n/10 for n in backGroundData]
        s1.AutoCountMode()
        del(s1)
        self.darkCurrent = backGround1secData

    #======================================================================================
    def scanStartBt(self):
        a = str(self.enterFileName.text())
        st = re.sub('[^.0-9a-zA-Z_-]', '', a)

        if a is not st or len(a) == 0:
            QMessageBox.warning(self, "Oops file name!", " File name has something wrong! ",
                                QMessageBox.Ok)
            return
        self.fileName = self.dir_ + '/' + st

        self.measureDarkMsg()
        self.scanStart()

    def scanStart(self):
        self.replotGraph()
        # inclease scan counter and clear live data list for live plot.
        self.scanCnt += 1

        # read new scan ini file-----------------------------------------------
        jconf = scan.read_scanconf('jscan.ini')

        if jconf['type'] == 'xafs':
            self.scanthread = scan.XAFS_Scan(energy_pv = jconf['energy_drive'],
                                             read_pv   = jconf['energy_read'],
                                             e0        = self.doubleE0.value())

            t_kw  = jconf['time_kw']
            t_max = jconf['max_time']
            nreg  = len(jconf['regions'])
            kws   = {'relative': jconf['is_relative']}


            for i in range(self.selectRegion.currentIndex()+2):
                li = list(self.reg_settings[i])

                start = li[0].value()
                stop  = li[1].value()
                step  = li[2].value()
                dt    = li[3].value()
                units = False
                kws['use_k'] = False
                if i > 2 :
                    units = li[4].currentIndex() != 0
                    kws['use_k'] = li[4].currentIndex() != 0

                kws['dtime'] =  dt
                # kws['use_k'] =  units.lower() != 'ev'
                if i == nreg-1: # final reg
                    if t_max > dt and t_kw > 0 and kws['use_k']:
                        kws['dtime_final'] = t_max
                        kws['dtime_wt'] = t_kw
                self.scanthread.add_region(start, stop, step, npts=None, **kws)

        for dpars in jconf['detectors']:
            det = scan.get_detector(**dpars)
            self.scanthread.add_detector(det)

        if 'counters' in jconf:
            for ct in jconf['counters']:
                label, pvname = ct
                self.scanthread.add_counter(pvname, label=label)

        self.scanthread.add_extra_pvs(jconf['extra_pvs'])

        # self.scanthread.dwelltime = jconf.get('dwelltime', 1)
        self.scanthread.comments  = jconf.get('user_comments', '')
        # self.scanthread.filename  = jconf.get('filename', 'scan.dat')
        # self.scanthread.filename  = self.dir_ + '/' + self.fileName
        self.scanthread.filename = self.fileName

        # self.scanthread.filename  = 'scan.dat'
        self.scanthread.pos_settle_time = jconf.get('pos_settle_time', 0.01)
        self.scanthread.det_settle_time = jconf.get('det_settle_time', 0.01)

        self.scanthread.messenger = self.messenger
        self.scanthread.messenger = self.report

        self.statusMsg(' SCAN Start...')

        self.btnStartScan.setEnabled(False)

        # print 'READY TO RUN SCAN '
        self.npts = len(self.scanthread.positioners[0].array)

        '''
        # LWW test for cursor region values
        if len(self.yyd) > 0: #self.scanCnt > 1:
            regionPos = self.lr.getRegion()
            self.dataView.removeItem(self.lr)
        else :
            regionPos = [-20, 20]

        self.lr = pg.LinearRegionItem(regionPos)
        self.lr.setZValue(-10)
        self.dataView.addItem(self.lr)
        # Todo: add cursor and value display
        # self.dataView.addLine(x=0, z=10, movable=True)
        # self.lr.setBounds([min(min(self.xxd)), None])
        # self.lr.show()
        # print self.lr.getRegion()
        '''

        self.scanthread.start()
        return

    def messenger(self, cpt=0, npts=1, scan=None, **kws):
        if cpt == 1:
            pass # print dir(scan)
        msg = '%i,' % cpt
        if cpt % 15 == 0:
            msg = "%s\n" % msg

        sys.stdout.write(msg)
        sys.stdout.flush()

    def report(self, scan=None, cpt=0, **kws):
        if cpt is None:
            dataArr = np.array([])
            for i in range(len(self.scanthread.counters)):
                # numpy module need first dimesion use hstack and then use vstack.
                if i is 0:
                    dataArr = np.hstack((dataArr,
                                         self.scanthread.counters[i].buff))
                else:
                    dataArr = np.vstack((dataArr,
                                         self.scanthread.counters[i].buff))
            self.yyd.append(dataArr)

            # we have max 10 history data.
            if len(self.yyd) > 10:
                self.yyd.pop(0)

            self.btnStartScan.setEnabled(True)
            # scan finished.
            self.packets.put_nowait((0, 'F'))

            #Todo : del is need or not? what is advantage?
            del(dataArr)

        #Todo: how can plot in the report(messenger), statusMsg, uis
        #how can plot in the other class?
        else:
            # notify new data to updateData methode.
            self.packets.put_nowait((0, cpt))

    def onEdgeChoice(self, evt=None):
        con = sqlite3.connect('xrayref.db')
        cursor = con.cursor()
        sqlStr = "SELECT absorption_edge FROM xray_levels WHERE element='%s' AND iupac_symbol='K'" %(self.elements.itemText(evt))
        cursor.execute(sqlStr)
        e0val = cursor.fetchall()
        cursor.close()
        con.close()

        a = e0val.pop(0)
        self.doubleE0.setValue(float(a[0]))


if __name__ == '__main__':
    # Exception Handling
    try:
        myApp = QApplication(sys.argv)
        myWin = MyMainWindow()
        myWin.show()
        myApp.exec_()
        sys.exit(0)
    except NameError:
        print("Name Error:", sys.exc_info()[1])
    except SystemExit:
        print("Closing Window...")
    except Exception:
        print(sys.exc_info()[1])

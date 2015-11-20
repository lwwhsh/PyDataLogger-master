__author__ = 'root'

"""******************************************************************
Append serial data to a buffer and update plot from a timer interrupt
******************************************************************"""
#!/usr/bin/python
# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import serial

app = QtGui.QApplication([])

p = pg.plot()
p.setWindowTitle('serial data plot')
curve = p.plot(pen=None, symbol='x')

data = [0]
# raw=serial.Serial("COM3",9600)
raw = serial.Serial("/dev/ttyS0",9600)


def update():
    global curve, data
    line = raw.readline()
    data.append(int(line))
    xdata = np.array(data, dtype='float64')
    curve.setData(xdata)
    app.processEvents()

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
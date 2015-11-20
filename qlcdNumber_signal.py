#!/usr/bin/env python
#-*- coding:utf-8 -*-
import time

from PyQt4 import QtGui, QtCore

class MyThread(QtCore.QThread):
    countChange = QtCore.pyqtSignal(int)
    countReset  = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(MyThread, self).__init__(parent)
        self.stopped = QtCore.QEvent(QtCore.QEvent.User)

    def start(self):
        self.stopped.setAccepted(False)
        self.count = 0

        super(MyThread, self).start()

    def run(self):
        while not self.stopped.isAccepted():
            self.count += 1
            self.countChange.emit(self.count)
            time.sleep(1)

        self.countReset.emit(0)

    def stop(self):
        self.stopped.setAccepted(True)

class MyWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)

        self.lcdNumber = QtGui.QLCDNumber(self)

        self.pushButtonStart = QtGui.QPushButton(self)
        self.pushButtonStart.setText("Start")
        self.pushButtonStart.clicked.connect(self.on_pushButtonStart_clicked)

        self.pushButtonStop = QtGui.QPushButton(self)
        self.pushButtonStop.setText("Stop")
        self.pushButtonStop.clicked.connect(self.on_pushButtonStop_clicked)

        self.pushButtonDone = QtGui.QPushButton(self)
        self.pushButtonDone.setText("Done")
        self.pushButtonDone.clicked.connect(self.on_pushButtonDone_clicked)

        self.layoutHorizontal = QtGui.QHBoxLayout(self)
        self.layoutHorizontal.addWidget(self.lcdNumber)
        self.layoutHorizontal.addWidget(self.pushButtonStart)
        self.layoutHorizontal.addWidget(self.pushButtonStop)
        self.layoutHorizontal.addWidget(self.pushButtonDone)

        self.thread = MyThread(self)
        self.thread.countChange.connect(self.lcdNumber.display)
        self.thread.countReset.connect(self.lcdNumber.display)

    @QtCore.pyqtSlot()
    def on_pushButtonStart_clicked(self):
        self.thread.start()

    @QtCore.pyqtSlot()
    def on_pushButtonStop_clicked(self):
        self.thread.stop()

    @QtCore.pyqtSlot()
    def on_pushButtonDone_clicked(self):
        sys.exit()

if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('MyWindow')

    main = MyWindow()
    main.exec_()

    sys.exit(app.exec_())

__author__ = 'root'

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import *
import time


@pyqtSlot(dict)
def callback(param):
    print "in callback"
    print param


class Test(QThread):
    mySignal = pyqtSignal(dict, name="mySignal")

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        while 1:
            print "Test running"
            self.mySignal.emit({'a': 'b'})
            time.sleep(.01)


if __name__ == "__main__":
    t = Test()
    t.start()
    t.mySignal.connect(callback)
    app = QApplication([])
    app.exec_()

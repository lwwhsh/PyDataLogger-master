__author__ = 'root'

from PyQt4 import QtGui, QtCore
import multiprocessing as mp
 

def initChildProcess():
    app = QtGui.QApplication.instance()
    if app is not None:
        print "QApp already exists in child process."
    else:
        app = QtGui.QApplication([])
     
    win = QtGui.QMainWindow()
    win.setWindowTitle("Child Process")
    win.show()
    app.exec_()
     

def newProcess():
    proc = mp.Process(target=initChildProcess)
    proc.start()
    return proc
     
if __name__ == '__main__':
    # This works as expected:
    # proc = newProcess()
    # app = QtGui.QApplication([])
     
    # This causes crash:

    #app = QtGui.QApplication([])
    proc = newProcess()
     
    #win = QtGui.QMainWindow()
    #win.setWindowTitle("Main Process")
    #win.show()
     
    #app.exec_()

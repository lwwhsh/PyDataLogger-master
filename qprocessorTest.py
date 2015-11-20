__author__ = 'root'

from PyQt4 import QtCore, QtGui
import multiprocessing as mp
import numpy as np
import sys


class Spectra:
    def __init__(self, spectra_name, X, Y):
        self.spectra_name = spectra_name
        self.X = X
        self.Y = Y
        self.iteration = 0

    def complex_processing_on_spectra(self, pipe_conn):
        self.iteration += 1
        pipe_conn.send(self.iteration)


class Spectra_Tab(QtGui.QTabWidget):
    def __init__(self, parent, spectra):
        self.parent = parent
        self.spectra = spectra
        QtGui.QTabWidget.__init__(self, parent)

        self.treeWidget = QtGui.QTreeWidget(self)
        self.properties = QtGui.QTreeWidgetItem(self.treeWidget, ["Properties"])
        self.step = QtGui.QTreeWidgetItem(self.properties, ["Iteration #"])

        self.consumer, self.producer = mp.Pipe()
        # Make process associated with tab
        self.process = mp.Process(target=self.spectra.complex_processing_on_spectra, args=(self.producer,))

    def update_GUI(self, iteration):
        self.step.setText(1, str(iteration))

    def start_computation(self):
        self.process.start()
        while True:
            message = self.consumer.recv()
            if message == 'done':
                break
            self.update_GUI(message)
        self.process.join()
        return


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent = None):
        QtGui.QMainWindow.__init__(self)

        self.setTabShape(QtGui.QTabWidget.Rounded)
        self.centralwidget = QtGui.QWidget(self)
        self.top_level_layout = QtGui.QGridLayout(self.centralwidget)

        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.top_level_layout.addWidget(self.tabWidget, 1, 0, 25, 25)

        process_button = QtGui.QPushButton("Process")
        self.top_level_layout.addWidget(process_button, 0, 1)
        QtCore.QObject.connect(process_button, QtCore.SIGNAL("clicked()"), self.process)

        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setLayout(self.top_level_layout)

        # Open several files in loop from button - simplifed to one here
        X = np.arange(0.1200, .2)
        Y = np.arange(0.1200, .2)
        self.spectra = Spectra('name', X, Y)
        self.spectra_tab = Spectra_Tab(self.tabWidget, self.spectra)
        self.tabWidget.addTab(self.spectra_tab, 'name')

    def process(self):
        self.spectra_tab.start_computation()
        return

if __name__ == "__main__":
    app = QtGui.QApplication([])
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

import sys
from PyQt4 import QtGui, QtCore

class MainWindow(QtGui.QMainWindow):

	DEFAULT_WINDOW_TITLE = "Stopwatch"

	def __init__(self, *args):
		apply(QtGui.QMainWindow.__init__, (self,) + args)

		self.mainWidget = QtGui.QWidget(self);
		self.setCentralWidget(self.mainWidget);
		self.mainLayout = QtGui.QVBoxLayout(self.mainWidget)

		self.buttonsWidget = QtGui.QWidget(self.mainWidget);
		self.buttonsLayout = QtGui.QHBoxLayout(self.buttonsWidget)

		self.txTime  = QtGui.QLCDNumber(self.mainWidget);
		self.txTime.setSegmentStyle(QtGui.QLCDNumber.Flat);
		self.bnStart = QtGui.QPushButton("&Start", self.buttonsWidget);
		self.bnClear = QtGui.QPushButton("&Clear", self.buttonsWidget);

		self.connect(self.bnStart, QtCore.SIGNAL("clicked()"), self.slotBnStartClicked)
		self.connect(self.bnClear, QtCore.SIGNAL("clicked()"), self.slotBnClearClicked)

		self.buttonsLayout.addWidget(self.bnStart);
		self.buttonsLayout.addWidget(self.bnClear);

		self.mainLayout.addWidget(self.txTime);
		self.mainLayout.addWidget(self.buttonsWidget);

		self.counting = False;
		self.msInLastLaps = 0;
		self.timer = QtCore.QTimer(self);
		self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.slotTimerEvent);

		self.displayTime(0, False)
		self.setWindowTitle(self.DEFAULT_WINDOW_TITLE)

		# reduce to minimum size
		self.resize(self.minimumSizeHint())

	def displayTime(self, msecs, exact):
		ms = msecs % 1000
		msecs /= 1000
		sec = msecs % 60
		msecs /= 60
		min = msecs % 60
		msecs /= 60
		hours = msecs
		if exact: 
			timestring = '%02d:%02d:%02d.%03d' % (hours, min, sec, ms)
			self.txTime.setNumDigits(12 if hours > 0 else 9)
			self.txTime.display(timestring)
			self.setWindowTitle(self.DEFAULT_WINDOW_TITLE)
		else:
			timestring = '%02d:%02d:%02d' % (hours, min, sec)
			self.txTime.setNumDigits(8 if hours > 0 else 5)
			self.txTime.display(timestring)
			self.setWindowTitle(timestring)

	def slotBnStartClicked(self):
		if ( self.counting ) :
			print "stop  ", str(QtCore.QTime.currentTime().toString())
			self.timer.stop();
			self.msInLastLaps += self.startTime.msecsTo(QtCore.QTime.currentTime());
			self.displayTime(self.msInLastLaps, True)
			self.bnStart.setText("&Start")
		else:
			self.startTime = QtCore.QTime.currentTime()
			print "start ", str(self.startTime.toString())
			self.timer.start(500)
			self.bnStart.setText("&Stop")
			self.slotTimerEvent()

		self.counting = not self.counting

	def slotBnClearClicked(self):
		print "clear";
		self.msInLastLaps = 0;
		self.startTime = QtCore.QTime.currentTime()
		self.displayTime(0, not self.counting)

	def slotTimerEvent(self):
		self.displayTime(self.msInLastLaps + self.startTime.msecsTo(QtCore.QTime.currentTime()), False)

# Main method as the program entry point
def main(args):
	app = QtGui.QApplication(args)
	win = MainWindow()
	win.show()
	app.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app, QtCore.SLOT("quit()"))
	app.exec_()

if __name__=="__main__":
	main(sys.argv)


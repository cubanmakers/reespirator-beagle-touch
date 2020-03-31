from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
import logging
import serial
from parse import *
import functools
from datetime import datetime

pg.setConfigOption('background', "052049")
#pg.setConfigOption('leftButtonPan', False)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

ser = serial.Serial(port = "/dev/ttyO1", baudrate=115200, timeout=0.010)

class MainWindow(QtWidgets.QDialog):

    def plot(self, chartIndex, widget, title, hour, temperature):
        self.myCurve[chartIndex] = widget.plot(hour, temperature, title=title)
        widget.setXRange(0,self.chunkSize,padding=0)
        if chartIndex == 0:
            widget.setYRange(0, 50)
        else:
            widget.setYRange(-5, 16)
        widget.setMouseEnabled(False, False)
        widget.disableAutoRange()
        widget.showGrid(True, True, 1)

    def __init__(self, *args, **kwargs):
        self._pip = 20
        self._peep = 6
        self._fr = 14

        super(MainWindow, self).__init__(*args, **kwargs)
        #Load the UI Page
        uic.loadUi('testQt.ui', self)
        pg.setConfigOption('background', (230,230,230))
        #pg.setConfigOptions('background', "y")
        self.textPip.setText(str(self._pip))
        self.textPeep.setText(str(self._peep))
        self.textFR.setText(str(self._fr))
        #uic.loadUiType('testQt.ui')
        self.myCurve = [0,0,0]
        self.chunkSize = 200
        self.split = 100
        self.xAxis = np.arange(self.chunkSize)
        #logger.info(self.xAxis)
        self.data1 = np.zeros((self.chunkSize,3))
        #logger.info("data1=" + str(self.data1))
        self.plot(0,self.graphPressure, "P", self.xAxis, self.data1[:,0])
        self.plot(1,self.graphFlow, "C",self.xAxis, self.data1[:,1])
        #self.plot(2,self.graphVolume, "F",self.xAxis, self.data1[:,2])
        self.myCurve[0].setPen(pg.mkPen('fbcca7', width=2))
        self.myCurve[1].setPen(pg.mkPen('a3dade', width=2))
        #self.myCurve[2].setPen(pg.mkPen('y', width=3))
        self.pointer = 0
        self.firstCycle = 1
        self.buttonUpPip.clicked.connect(self.buttonUpPipClicked) # connecting the clicked signal with btnClicked slot
        self.buttonDownPip.clicked.connect(self.buttonDownPipClicked)
        self.buttonUpPeep.clicked.connect(self.buttonUpPeepClicked)
        self.buttonDownPeep.clicked.connect(self.buttonDownPeepClicked)
        self.buttonUpFR.clicked.connect(self.buttonUpFRClicked)
        self.buttonDownFR.clicked.connect(self.buttonDownFRClicked)
        logger.info('Configure')

    def buttonUpPipClicked(self):
        if self._pip <= 79:
            self._pip += 1
        self.textPip.setText(str(self._pip))
        ser.write(b"CONFIG PIP " + bytes(self._pip))

    def buttonDownPipClicked(self):
        if self._pip >= 1:
            self._pip -= 1
        self.textPip.setText(str(self._pip))
        ser.write(b"CONFIG PIP " + bytes(self._pip))

    def buttonUpPeepClicked(self):
        if self._peep < self._pip:
            self._peep += 1
        self.textPeep.setText(str(self._peep))
        ser.write(b"CONFIG PEEP " + bytes(self._peep))

    def buttonDownPeepClicked(self):
        if self._peep > 0:
            self._peep -= 1
        self.textPeep.setText(str(self._peep))
        ser.write(b"CONFIG PEEP " + bytes(self._peep))

    def buttonUpFRClicked(self):
        if self._fr < 30:
            self._fr += 1
        self.textFR.setText(str(self._fr))
        ser.write(b"CONFIG BPM " + bytes(self._fr))

    def buttonDownFRClicked(self):
        if self._fr > 3:
            self._fr -= 1
        self.textFR.setText(str(self._fr))
        ser.write(b"CONFIG BPM " + bytes(self._fr))

    def update(self, pres, flow):
        self.i = self.pointer % (self.chunkSize)
        #logger.info('Updated ' + str(flow) + " at " + str(datetime.now()))
        #logger.info('pointer' + str(self.pointer))
        if self.i == 0 and self.firstCycle == 0:
          logger.info("splitting")
          tmp = np.empty((self.chunkSize,3))
          tmp[:self.split] = self.data1[self.chunkSize - self.split:]
          self.data1 = tmp
          self.pointer = self.split
          self.i = self.pointer
        self.data1[self.i,0] = pres
        #self.data1[self.i,1] = vol 
        self.data1[self.i,1] = float(flow) / 1000.0
        #logger.info(self.data1[:self.i+1])
        self.myCurve[0].setData(x=self.xAxis[:self.i+1], y=self.data1[:self.i+1,0])
        self.myCurve[1].setData(x=self.xAxis[:self.i+1], y=self.data1[:self.i+1,1])
        #self.myCurve[2].setData(x=self.xAxis[:self.i+1], y=self.data1[:self.i+1,2])
        self.pointer += 1
        #logger.info('Updated2 ' + str(flow) + " at " + str(datetime.now()))
        if self.pointer >= self.chunkSize:
            self.firstCycle = 0

_buffer = b""
_t1 = 0
_t2 = 0
import time
_updatePending = False
_r = None


def readSerial(ser, main):
    global _buffer, _t1, _t2, _r, _updatePending
    _t2 = time.time() * 1000
    if _t2 - _t1 > 40:
        logger.info("Fuck" + str(_t2 - _t1))
    _t1 = _t2
    #logger.info("readSerial at " + str(datetime.now()))
    line = ser.read_until(b'\n')
    line =  _buffer + line
    if len(line) != 0:
        if b"\n" in line:
            #logger.info("Readed bytes" + str(len(line)))
            #logger.info(line)
            line = str(line)
            r = search("DT {pres1:d} {pres2:d} {vol:d} {flow:d}", line)
            if r != None:
                #logger.info("pres1" + str(r.named['pres1']) + "----flow" + str(r.named['flow']))
                #main.update(r.named['pres1'], r.named['flow'])
                _r = r
                _updatePending = True
            _buffer = b""
        else:
            #logger.info("Queued" + str(line))
            _buffer += line
    logger.info("readSerial takes ms=" + str(time.time()*1000 - _t2))

def plotUpdate(main):
    global _updatePending, _r
    if _updatePending:
        main.update(_r.named['pres1'], _r.named['flow'])
        _updatePending = False


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    ser.close()
    ser.open()
    timer = pg.QtCore.QTimer()
    timer2 = pg.QtCore.QTimer()
    wrappedReadSerial = functools.partial(readSerial, ser, main)
    timer.timeout.connect(wrappedReadSerial) 
    timer.start(10)
    wrappedPlotUpdate= functools.partial(plotUpdate, main)
    timer2.timeout.connect(wrappedPlotUpdate) 
    timer2.start(50)
    sys.exit(app.exec_())


if __name__ == '__main__':      
    main()
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 ai

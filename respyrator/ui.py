##############################################################################
# For copyright and license notices, see LICENSE file in root directory
##############################################################################
from datetime import datetime
from parse import *
from PyQt5 import QtWidgets, uic
from pyqtgraph import PlotWidget, plot
from respyrator import core, serial
import functools
import numpy as np
import pyqtgraph as pg
import sys

pg.setConfigOption('background', "052049")
# pg.setConfigOption('leftButtonPan', False)


class MainWindow(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serial = None
        self._pip = 20
        self._peep = 6
        self._fr = 14
        self._recruit = False

        uic.loadUi(core.path('ui_main.ui'), self)
        pg.setConfigOption('background', (230, 230, 230))
        self.update_values()

        self.buttonUpPip.clicked.connect(self.buttonUpPipClicked)
        self.buttonDownPip.clicked.connect(self.buttonDownPipClicked)
        self.buttonUpPeep.clicked.connect(self.buttonUpPeepClicked)
        self.buttonDownPeep.clicked.connect(self.buttonDownPeepClicked)
        self.buttonUpFR.clicked.connect(self.buttonUpFRClicked)
        self.buttonDownFR.clicked.connect(self.buttonDownFRClicked)
        # TODO create UI button "buttonRecruitClicked" and bind

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.serial_read)

        self.myCurve = [0, 0, 0]
        self.chunkSize = 200
        self.split = 100
        self.xAxis = np.arange(self.chunkSize)
        self.data1 = np.zeros((self.chunkSize, 3))
        self.plot(0, self.graphPressure, "P", self.xAxis, self.data1[:,0])
        self.plot(1, self.graphFlow, "C", self.xAxis, self.data1[:,1])
        #self.plot(2,self.graphVolume, "F",self.xAxis, self.data1[:,2])
        self.myCurve[0].setPen(pg.mkPen('fbcca7', width=2))
        self.myCurve[1].setPen(pg.mkPen('a3dade', width=2))
        #self.myCurve[2].setPen(pg.mkPen('y', width=3))
        self.pointer = 0
        self.firstCycle = 1

    def show(self, *args, **kwargs):
        res = super().show()
        self.timer.start(10)
        return res

    @property
    def serial(self):
        if self._serial is not None:
            return self._serial
        port = core.config['serial_port']
        if not port and core.debug:
            core.logger.debug(
                'In debug mode connect to fakeSerial, for force port add '
                '"serial_port" in config.yml')
            self._serial = serial.FakeSerial()
            return self._serial
        if not port:
            port = serial.serial_discovery_port()
        core.logger.debug('Connect to port "%s"' % port)
        self._serial = serial.serial_get(port)
        return self._serial

    def serial_send(self, msg):
        core.logger.info('Serial send "%s"' % msg)
        self.serial.write(bytes('%s\r\n' % msg, 'utf-8'))
        self.serial.flush()

    def serial_read(self):
        line = self.serial.read_until()
        if not line:
            return
        line = str(line)
        vals = search("DT {pres1:d} {pres2:d} {vol:d} {flow:d}", line)
        if vals:
            self.update(vals.named['pres1'], vals.named['flow'])

    def plot(self, chartIndex, widget, title, hour, temperature):
        self.myCurve[chartIndex] = widget.plot(hour, temperature, title=title)
        widget.setXRange(0,self.chunkSize,padding=0)
        if chartIndex == 0:
            widget.setYRange(0, 50)
        else:
            widget.setYRange(-20, 30)
        widget.setMouseEnabled(False, False)
        widget.disableAutoRange()
        widget.showGrid(True, True, 1)

    def update(self, pres, flow):
        self.i = self.pointer % (self.chunkSize)
        if self.i == 0 and self.firstCycle == 0:
            tmp = np.empty((self.chunkSize,3))
            tmp[:self.split] = self.data1[self.chunkSize - self.split:]
            self.data1 = tmp
            self.pointer = self.split
            self.i = self.pointer
        self.data1[self.i,0] = pres
        #self.data1[self.i,1] = vol
        self.data1[self.i,1] = float(flow) / 1000.0
        #core.logger.info(self.data1[:self.i+1])
        self.myCurve[0].setData(x=self.xAxis[:self.i+1], y=self.data1[:self.i+1,0])
        self.myCurve[1].setData(x=self.xAxis[:self.i+1], y=self.data1[:self.i+1,1])
        #self.myCurve[2].setData(x=self.xAxis[:self.i+1], y=self.data1[:self.i+1,2])
        self.pointer += 1
        #core.logger.info('Updated2 ' + str(flow) + " at " + str(datetime.now()))
        if self.pointer >= self.chunkSize:
            self.firstCycle = 0

    def update_values(self):
        self.textPip.setText(str(self._pip))
        self.textPeep.setText(str(self._peep))
        self.textFR.setText(str(self._fr))

    def buttonUpPipClicked(self):
        if self._pip <= 79:
            self._pip += 1
        self.update_values()
        self.serial_send('CONFIG PIP %s' % self._pip)

    def buttonDownPipClicked(self):
        if self._pip >= 1:
            self._pip -= 1
        self.update_values()
        self.serial_send('CONFIG PIP %s' % self._pip)

    def buttonUpPeepClicked(self):
        if self._peep < self._pip:
            self._peep += 1
        self.update_values()
        self.serial_send('CONFIG PEEP %s' % self._peep)

    def buttonDownPeepClicked(self):
        if self._peep > 0:
            self._peep -= 1
        self.update_values()
        self.serial_send('CONFIG PEEP %s' % self._peep)

    def buttonUpFRClicked(self):
        if self._fr < 30:
            self._fr += 1
        self.update_values()
        self.serial_send('CONFIG BPM %s' % self._fr)

    def buttonDownFRClicked(self):
        if self._fr > 3:
            self._fr -= 1
        self.update_values()
        self.serial_send('CONFIG BPM %s' % self._fr)

    def buttonRecruitClicked(self):
        self._recruit = not self._recruit
        if self._recruit:
            self.serial_send('RECRUIT ON')
        else:
            self.serial_send('RECRUIT OFF')


def app():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

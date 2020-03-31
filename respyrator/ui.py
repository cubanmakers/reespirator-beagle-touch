##############################################################################
# For copyright and license notices, see LICENSE file in root directory
##############################################################################
from datetime import datetime
from parse import *
from PyQt5 import QtWidgets, uic, QtCore
from pyqtgraph import PlotWidget, plot
from respyrator import core, serial
import numpy as np
import pyqtgraph as pg
import sys

pg.setConfigOption('background', "052049")
pg.setConfigOption('leftButtonPan', False)


class MainWindow(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._serial = None
        self._pres1 = 0
        self._pres2 = 0
        self._pip = 20
        self._peep = 6
        self._fr = 14
        self._vol = 99
        self._config_pip = 20
        self._config_peep = 6
        self._config_fr = 14

        self._recruit = False
        self._recruit_on_text = 'STOP RECRUIT'
        self._recruit_off_text = 'RECRUIT'
        self._recruit_timmer = None

        self.serial_setup()
        uic.loadUi(core.path('ui_main.ui'), self)
        # pg.setConfigOption('background', (230, 230, 230))
        self.buttonUpPip.clicked.connect(self.buttonUpPipClicked)
        self.buttonDownPip.clicked.connect(self.buttonDownPipClicked)
        self.buttonUpPeep.clicked.connect(self.buttonUpPeepClicked)
        self.buttonDownPeep.clicked.connect(self.buttonDownPeepClicked)
        self.buttonUpFR.clicked.connect(self.buttonUpFRClicked)
        self.buttonDownFR.clicked.connect(self.buttonDownFRClicked)
        self.buttonRecruit.clicked.connect(self.buttonRecruitClicked)
        self._recruit_on_stylesheet = "background-color: red"
        self._recruit_off_stylesheet = self.buttonRecruit.styleSheet()
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

        self.update()

    def show(self, *args, **kwargs):
        res = super().show()
        self.timer.start(10)
        return res

    def serial_setup(self):
        file = core.config['serial_file']
        if file:
            self.serial = serial.FileSerial(file)
            return
        port = core.config['serial_port']
        if not port and core.debug:
            core.logger.debug(
                'In debug mode connect to fakeSerial, for force port add '
                '"serial_port" in config.yml')
            self.serial = serial.FakeSerial()
            return
        if not port:
            ports = serial.serial_ports_get()
            port = serial.serial_discovery_port(ports, quick=True)
        if not port:
            print(
                'You must set a "serial_port" value for config file '
                'config.yml')
            sys.exit(-1)
        core.logger.debug('Connect to port "%s"' % port)
        self.serial = serial.serial_get(port)
        if not self.serial.is_open:
            raise Exception('Can\'t open serial port %s' % port)

    def serial_send(self, msg):
        core.logger.info('Serial send "%s"' % msg)
        self.serial.write(bytes('%s\r\n' % msg, 'utf-8'))
        self.serial.flush()

    def serial_read(self):
        line = self.serial.read_until()
        core.logger.debug('Read line: %s' % line)
        if not line:
            return
        line = str(line)
        data = line.split(' ')
        # frame: CONFIG pip peep rpm
        if data[0] == 'CONFIG':
            self._pip = int(data[1])
            self._peep = int(data[2])
            self._fr = int(data[3])
            self.update()
        # frame: DT pres1 pres2 vol flow
        elif data[0] == 'DT':
            self._pres1 = data[1]
            self._pres2 = data[2]
            self._vol = data[3]
            self._flow = data[4]
            self.update()
        # frame: VOL vol
        elif data[0] == 'VOL':
            self._vol = [1]
            self.update()

    def plot(self, chartIndex, widget, title, hour, temperature):
        self.myCurve[chartIndex] = widget.plot(hour, temperature, title=title)
        widget.setXRange(0, self.chunkSize, padding=0)
        if chartIndex == 0:
            widget.setYRange(0, 50)
        else:
            widget.setYRange(-20, 30)
        widget.setMouseEnabled(False, False)
        widget.disableAutoRange()
        widget.showGrid(True, True, 1)

    def update(self):
        self.configPip.setText(str(self._config_pip))
        self.configPeep.setText(str(self._config_peep))
        self.configFr.setText(str(self._config_fr))
        self.textPip.setText(str(self._pip))
        self.textPeep.setText(str(self._peep))
        self.textFr.setText(str(self._fr))
        self.textVol.setText(str(self._vol))
        pres = self._pres1
        flow = self._pres2
        flow = self._fr
        self.i = self.pointer % (self.chunkSize)
        if self.i == 0 and self.firstCycle == 0:
            tmp = np.empty((self.chunkSize, 3))
            tmp[:self.split] = self.data1[self.chunkSize - self.split:]
            self.data1 = tmp
            self.pointer = self.split
            self.i = self.pointer
        self.data1[self.i, 0] = pres
        #self.data1[self.i,1] = vol
        self.data1[self.i, 1] = float(flow) / 1000.0
        self.myCurve[0].setData(
            x=self.xAxis[:self.i + 1],
            y=self.data1[:self.i + 1, 0],
        )
        self.myCurve[1].setData(
            x=self.xAxis[:self.i + 1],
            y=self.data1[:self.i + 1, 1]
        )
        self.pointer += 1
        if self.pointer >= self.chunkSize:
            self.firstCycle = 0

    def kill_recruit_timmer(self):
        if not self._recruit_timmer:
            return
        self._recruit_timmer.stop()
        self._recruit_timmer.deleteLater()
        self._recruit_timmer = None

    def start_recruit_timmer(self):
        self._recruit_timmer = QtCore.QTimer()
        self._recruit_timmer.timeout.connect(self.recruit_off)
        self._recruit_timmer.setSingleShot(True)
        self._recruit_timmer.start(40000)

    def recruit_on(self):
        self.kill_recruit_timmer()
        self.serial_send('RECRUIT ON')
        self._recruit = True
        self.buttonRecruit.setStyleSheet(self._recruit_on_stylesheet)
        self.buttonRecruit.setText(self._recruit_on_text)
        self.start_recruit_timmer()

    def recruit_off(self):
        self.kill_recruit_timmer()
        self.serial_send('RECRUIT OFF')
        self._recruit = False
        self.buttonRecruit.setStyleSheet(self._recruit_off_stylesheet)
        self.buttonRecruit.setText(self._recruit_off_text)

    def buttonUpPipClicked(self):
        if self._config_pip <= 79:
            self._config_pip += 1
        self.update_values()
        self.serial_send('CONFIG PIP %s' % self._config_pip)

    def buttonDownPipClicked(self):
        if self._config_pip >= 1:
            self._config_pip -= 1
        self.update_values()
        self.serial_send('CONFIG PIP %s' % self._config_pip)

    def buttonUpPeepClicked(self):
        if self._config_peep < self._config_pip:
            self._config_peep += 1
        self.update_values()
        self.serial_send('CONFIG PEEP %s' % self._config_peep)

    def buttonDownPeepClicked(self):
        if self._config_peep > 0:
            self._config_peep -= 1
        self.update_values()
        self.serial_send('CONFIG PEEP %s' % self._config_peep)

    def buttonUpFRClicked(self):
        if self._config_fr < 30:
            self._config_fr += 1
        self.update_values()
        self.serial_send('CONFIG BPM %s' % self._config_fr)

    def buttonDownFRClicked(self):
        if self._config_fr > 3:
            self._config_fr -= 1
        self.update_values()
        self.serial_send('CONFIG BPM %s' % self._config_fr)

    def buttonRecruitClicked(self):
        if self._recruit:
            self.recruit_off()
        else:
            self.recruit_on()


def app():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

##############################################################################
# For copyright and license notices, see LICENSE file in root directory
##############################################################################
import os
import serial
import time
import sys
import glob
import threading
import datetime
import respyrator


def serial_ports_get():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def serial_port_frames_get(port, timeout=3):
    def test(frames, port):
        with serial.Serial(port, timeout=0.1) as s:
            frames.append(s.read_until())

    frames = []
    thread = threading.Thread(target=test, args=[frames, port])
    thread.daemon = True
    thread.start()
    time.sleep(timeout)
    threading.currentThread().ident
    return frames


def serial_discovery_port():
    ports = serial_ports_get()
    for port in ports:
        frames = serial_port_frames_get(port)
        if frames and any(['DT' in f for f in frames]):
            return port
    return None


def serial_get(port):
    return Serial(port=port, baudrate=115200, timeout=0.1)


class Serial(serial.Serial):
    def __init__(self, *args, **kwargs):
        self._is_recording = False
        self._frames_record_out = []
        self._frames_record_in = []
        super().__init__(*args, **kwargs)

    def read(self, *args, **kwargs):
        res = super().read(*args, **kwargs)
        if self._is_recording:
            self._frames_record_in.append(res)
        return res

    def write(self, *args, **kwargs):
        res = super().write(*args, **kwargs)
        if self._is_recording:
            self._frames_record_out.append(args[0])
        return res

    def record_start(self):
        self._frames_record = []
        self._is_recording = True

    def record_stop(self):
        fname = 'record-%s' % datetime.datetime.now().strftime('%y%m%d_%H%M%S')
        with open(respyrator.core.path('%s.in' % fname), 'wb') as fp:
            for frame in self._frames_record_in:
                fp.write(frame)
        with open(respyrator.core.path('%s.out' % fname), 'wb') as fp:
            for frame in self._frames_record_out:
                fp.write(frame)
        self._is_recording = False


class FakeSerial:
    def __init__(self):
        self._waiting = True

    @property
    def in_waiting(self):
        return self._waiting

    def read(self, size):
        pass

    def read_until(self, chr='\n'):
        pass

    def write(self, byte):
        pass

    def flush(self):
        pass


class FileSerial:
    def __init__(self, file_name=None, sleep=0.2):
        self._waiting = True
        self.sleep = sleep
        if not os.path.exists(file_name):
            raise Exception(
                'File "%s" with samples frames not exists' % file_name)
        self.file_name = file_name

    @property
    def in_waiting(self):
        return self._waiting

    def read(self, size):
        def _loop(self, size):
            with open(self.file_name, 'rb') as fp:
                while True:
                    byte = fp.read(size)
                    if not byte:
                        break
                    yield byte
                    self._waiting = True
                    time.sleep(self.sleep)
                    self._waiting = False

        generator = _loop(size)
        return next(generator)

    def write(self, byte):
        pass

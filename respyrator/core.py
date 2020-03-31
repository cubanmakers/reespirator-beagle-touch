##############################################################################
# For copyright and license notices, see LICENSE file in root directory
##############################################################################
import logging
import os
import subprocess
import sys
import yaml



class Core:
    version = '0.1'

    def __init__(self):
        print('ResPyrator %s' % self.version)
        sys.path.append(self.path())
        self.debug = False
        self.boot()

    def boot(self):
        self.config = self.load_config()
        self.logger = self.setup_logging()

    def set_debug(self, debug):
        self.debug = debug
        self.boot()

    def load_config(self):
        default = {
            'serial_port': None,
            'record': False,
            'log_level': 'INFO',
            'log_formatter': '%(asctime)s - %(levelname)s - %(message)s',
        }
        config_fname = self.path('..', 'config.yml')
        if not os.path.exists(config_fname):
            with open('config.yml', 'w') as f:
                f.write(yaml.dump(default))
        with open(config_fname) as f:
            config = yaml.load(f.read()) or {}
        default.update(config)
        if self.debug:
            default['log_level'] = 'DEBUG'
        return default

    def setup_logging(self):
        logger = logging.getLogger()
        log_level = (
            logging.DEBUG
            if self.config['log_level'].lower() == 'debug'
            else logging.INFO
        )
        logger.setLevel(log_level)
        formatter = logging.Formatter(self.config['log_formatter'])
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def path(self, *args):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), *args))

    def popen(cmd, verbose=False):
        logging.debug('Execute shell command %s' % ' '.join(cmd))
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr

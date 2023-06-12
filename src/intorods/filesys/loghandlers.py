import logging
import logging.handlers
import sys
from logging.handlers import SysLogHandler

LOG_FORMAT_FILE = "%(asctime)s|%(name)s %(levelname)s: %(message)s"
LOG_PARAMS = {
    "when": "D",
    "interval": 5,
    "backupCount": 20
}


def log_to_file(logger, filename, log_level):
    logger.setLevel(log_level)
    formatter = logging.Formatter(LOG_FORMAT_FILE)
    fh = logging.handlers.TimedRotatingFileHandler(filename, **LOG_PARAMS)
    fh.setFormatter(formatter)
    fh.setLevel(log_level)
    logger.addHandler(fh)


def log_to_syslog(logger, name, log_level):
    logger.setLevel(log_level)
    log_format = f'{name}: %(asctime)s|%(name)s %(levelname)s: %(message)s'
    formatter = logging.Formatter(log_format)
    lg = logging.handlers.SysLogHandler(
        facility=SysLogHandler.LOG_LOCAL6, address='/dev/log')
    lg.setFormatter(formatter)
    lg.setLevel(log_level)
    logger.addHandler(lg)


def log_to_stdout(logger, name, log_level):
    logger.setLevel(log_level)
    log_format = f'{name}: %(asctime)s|%(name)s %(levelname)s: %(message)s'
    formatter = logging.Formatter(log_format)
    lg = logging.StreamHandler(stream=sys.stdout)
    lg.setFormatter(formatter)
    lg.setLevel(log_level)
    logger.addHandler(lg)

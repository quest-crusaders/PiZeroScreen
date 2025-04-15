from enum import Enum
from datetime import datetime


class LogType(Enum):
    DEFAULT = 0
    Error = 1
    SystemInfo = 2
    DataUpdated = 3
    ScreenLogin = 4
    ScreenInfoUpdated = 5
    Login = 6

COLORMAP = {
    LogType.DEFAULT: '\033[0m',
    LogType.Error: '\033[91m',
    LogType.SystemInfo: '\033[95m',
    LogType.DataUpdated: '\033[94m',
    LogType.ScreenLogin: '\033[96m',
    LogType.ScreenInfoUpdated: '\033[93m',
}
LOGGING_LEVELS = {
    "default": [LogType.Error, LogType.SystemInfo, LogType.ScreenLogin, LogType.ScreenInfoUpdated],
    "debug": [i for i in LogType],
    "all": [i for i in LogType],
    "none": [],
    "silent": [],
    "admin_panel": [LogType.Error, LogType.ScreenLogin, LogType.ScreenInfoUpdated],
}
CONF = {"level": "default", "log_logins": "True", "timestamp": "True"}
MESSAGE_LOG = []

def log(*message, msg_type=LogType.DEFAULT):
    tstamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    MESSAGE_LOG.append((tstamp, " ".join([str(m) for m in message]), msg_type))
    if CONF["timestamp"] == "True":
        message = [tstamp] + list(message)
    if msg_type in LOGGING_LEVELS.get(CONF["level"]):
        msg = " ".join([str(m) for m in message])
        if msg_type != LogType.DEFAULT:
            msg = COLORMAP[msg_type] + msg + COLORMAP[LogType.DEFAULT]
        print(msg)
    if CONF["log_logins"] == "True" and msg_type == LogType.Login:
        with open("loggins.log", "a") as F:
            msg = " ".join([str(m) for m in message])
            F.write(msg+"\n")

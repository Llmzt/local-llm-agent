"""项目日志系统：统一初始化日志，并给各模块提供 logger。"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from service.core.env import PROJECT_ROOT,load_env_file

LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE = LOG_DIR / "agent.log"

_CONFIGURED = False

def setup_logging() ->None:
    """
    初始化日志系统
    可多次调用，仅初始化一次
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    
    load_env_file()

    log_level = os.getenv("LOG_LEVEL","INFO").upper()
    log_file = Path(os.getenv("LOG_FILE",DEFAULT_LOG_FILE))
    log_file.parent.mkdir(parents=True,exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    #控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    #文件输出
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",

    )

    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name:str) ->logging.Logger:
    """ 
    获取模块专属logger
    """
    setup_logging()
    return logging.getLogger(name)

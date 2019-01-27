#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
from pathlib import Path


PACKAGENAME = (Path(__file__) / '..').resolve().name

TIP_LVL_NUM = 21
WIZARD_LVL_NUM = 22
CHECKPOINT_LVL_NUM = 23

_logger_level = logging.DEBUG
root_name = ''


def create_logger(name=PACKAGENAME):
    global root_name
    root_name = name
    
    logging.addLevelName(TIP_LVL_NUM, 'TIP')
    logging.Logger.tip = tip
    logging.addLevelName(WIZARD_LVL_NUM, 'WIZARD')
    logging.Logger.wizard = wizard
    logging.addLevelName(CHECKPOINT_LVL_NUM, 'CHECKPOINT')
    logging.Logger.checkpoint = checkpoint
    
    logger = logging.getLogger(name)
    logger.setLevel(_logger_level)
    ch = logging.StreamHandler()
    ch.setLevel(_logger_level)
    formatter = logging.Formatter('%(name)s: [%(levelname)s]: %(message)s')
    ch.setFormatter(formatter)
    del logger.handlers[:]
    logger.addHandler(ch)
    logger.propagate = False
    
    return logger


def get_logger(name):
    global root_name
    
    parents = name.split('.')
    if root_name:
        return logging.getLogger(f'{PACKAGENAME}.{parents[-1]}')
    else:
        return logging.getLogger(parents[-1])
    

def set_level(logger, args):
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif not args.quiet:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.CRITICAL)


def tip(self, message, *args, **kws):
    if self.isEnabledFor(TIP_LVL_NUM):
        self._log(TIP_LVL_NUM, message, args, **kws) 
        
        
def wizard(self, message, *args, **kws):
    if self.isEnabledFor(WIZARD_LVL_NUM):
        self._log(WIZARD_LVL_NUM, message, args, **kws) 
        
        
def checkpoint(self, message, *args, **kws):
    if self.isEnabledFor(CHECKPOINT_LVL_NUM):
        self._log(CHECKPOINT_LVL_NUM, message, args, **kws)
        
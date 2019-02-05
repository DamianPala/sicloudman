#!/usr/bin/env python
# -*- coding: utf-8 -*-


import signal
import sys
from enum import EnumMeta

from . import logger


_logger = logger.get_logger(__name__)


def keyboard_interrupt_handler(_signal, _frame):
    sys.exit('Interrupted by user')

signal.signal(signal.SIGINT, keyboard_interrupt_handler)


def get_data(name, msg):
    return input(f'{name}: [WIZARD]: {msg}: ')


def get_data_and_valid(name, msg, invalid_values):
    is_correct_value = False

    while not is_correct_value:
        data = input(f'{name}: [WIZARD]: {msg}: ')
        if data not in invalid_values:
            is_correct_value = True
        else:
            if data == '':
                _logger.error('Empty value is not allowed! Try again.')
            else:
                _logger.error(f'Value: {data} is not allowed! Try again.')
                
    return data
    
    
def choose_one(name, msg, choices):
    if type(choices) is EnumMeta:
        choices = [item.value for item in choices]
    
    no_choice = True
    while no_choice:
        choice = input(f"{name}: [CHECKPOINT]: {msg} ({'/'.join(choices)}): ")
        for item in choices:
            if item == choice:
                no_choice = False
                break
            
    return choice


def choose_bool(name, msg):
    return True if choose_one(name, msg, ['y', 'n']) == 'y' else False


def is_checkpoint_ok(name, msg, choices=['y', 'n'], valid_value='y'):
    choice = choose_one(name, msg, choices)
            
    return True if choice == valid_value else False

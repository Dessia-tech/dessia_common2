#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" General checks & checklists. """

from typing import List


LEVEL_TO_INT = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3}


class PassedCheck:
    """ Denote the result of a check that has no error. """

    level = 'info'

    def __init__(self, message: str):
        self.message = message

    def __repr__(self):
        return f'[{self.level.upper()}: {self.__class__.__name__}] - {self.message}'

    def to_dict(self):
        return {"level": self.level, "message": self.message, "object_class": self.__class__.__name__}


class CheckWarning(PassedCheck):
    """ Denote a check warning. """

    level = 'warning'


class FailedCheck(PassedCheck):
    """ Denote a failed check. """

    level = 'error'


class BadType(FailedCheck):
    """ Denote a failed check due to a bad type. """


class GeometricInconsistance(FailedCheck):
    """ Denote a failed check due to a geometric inconsistency. """


class CheckList:
    """ A list of checks result. """

    def __init__(self, checks: List[PassedCheck]):
        self.checks = checks

    def __repr__(self):
        rep = f'Check list containing {len(self.checks)} checks:\n'
        for check_idx, check in enumerate(self.checks):
            rep += f'Check {check_idx+1} {check}\n'
        return rep

    def __add__(self, other_checklist: 'CheckList'):
        return self.__class__(self.checks + other_checklist.checks)

    def __len__(self):
        return len(self.checks)

    def __getitem__(self, item: int):
        return self.checks[item]

    def checks_above_level(self, level: str = 'error'):
        """ Return True if no check has a level above given one, else False. """
        checks = []
        for check in self.checks:
            if LEVEL_TO_INT[check.level] >= LEVEL_TO_INT[level]:
                checks.append(check)
        return checks

    def raise_if_above_level(self, level: str = 'error'):
        """ Raise an error if some checks have a level above given one. """
        for check in self.checks_above_level(level=level):
            raise ValueError(f'Check: {check} is above level "{level}"')

    def to_dict(self):
        return {"checks": [c.to_dict() for c in self.checks]}


def is_int(value, level: str = 'error'):
    """ Return if value is a int. """
    if not isinstance(value, int):
        return CheckList([FailedCheck(f'Value {value} is not an int')])
    if level == 'info':
        return CheckList([PassedCheck(f'value {value} is an int')])
    return CheckList([])


def is_float(value, level: str = 'error'):
    """ Return if value is a float. """
    if not isinstance(value, float):
        return CheckList([FailedCheck(f'Value {value} is not a float')])
    if level == 'info':
        return CheckList([PassedCheck(f'value {value} is a float')])
    return CheckList([])


def is_str(value, level: str = 'error'):
    """ Return if value is a str. """
    if not isinstance(value, str):
        return CheckList([FailedCheck(f'Value {value} is not a str')])
    if level == 'info':
        return CheckList([PassedCheck(f'value {value} is a str')])
    return CheckList([])


def type_check(value, expected_type, level: str = 'error'):
    """
    Type check the value against the expected type.

    This is experimental!
    """
    if expected_type is int:
        return is_int(value)
    if expected_type is float:
        return is_float(value)
    if expected_type is str:
        return is_str(value)

    if not isinstance(value, expected_type):
        return CheckList([FailedCheck(f'Value {value} is not of type {expected_type}')])
    if level == 'info':
        return CheckList([PassedCheck(f'value {value} is of expected type {expected_type}')])

    return CheckList([])

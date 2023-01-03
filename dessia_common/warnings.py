"""
Module that stores warnings in dessia_common.
"""


class SerializationWarning(Warning):
    def __init__(self, message: str):
        self.message = message

        Warning.__init__(self, message)

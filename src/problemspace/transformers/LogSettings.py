import typing
import pathlib
import logging

class LogSettings:
    """
    Settings we can pass to transformers for debugging of problem-space changes.
    """

    def __init__(self,
                 debug_coloring: bool = False,
                 logger: typing.Optional[logging.Logger] = None,
                 error_dir: typing.Optional[pathlib.Path] = None):
        """
        :param debug_coloring: if true, we colorize the changes in PDF file
        :param logger: logger, if None, then all messages are print to stdout/stderr,
        otherwise, the logger is used to save all logging messages.
        :param error_dir: if None, nothing saved. If given, it saves the whole
        latex project to error_dir in case of an error---to reproduce the error.
        """

        self.debug_coloring = debug_coloring
        self.logger = logger
        self.error_dir = error_dir
from qtpy import QtCore

import os.path

from typstwriter import enums

from typstwriter import logging
from typstwriter import configuration
from typstwriter import arguments

logger = logging.getLogger(__name__)
config = configuration.Config
args = arguments.Args


class SingleState(QtCore.QObject):
    """Stores a single state in 'Value' and emits 'Signal(value)' whenever 'Value' is reassigned."""

    Signal = QtCore.Signal(object)
    Value = None

    def __init__(self, value=None):
        """Initialize and assign value, if present."""
        QtCore.QObject.__init__(self)
        self.Value = value

    def __setattr__(self, name, value):
        """Emit Signal upon reassignment of Value. Reject assigning any other attribute."""
        if name == "Value":
            super().__setattr__(name, value)
            self.Signal.emit(value)
        elif name == "Signal":
            super().__setattr__(name, value)
        else:
            raise AttributeError("The only valid attributes are 'Value' and 'Signal'.")


class GlobalState:
    """Stores and initializes a collection of SingleStates."""

    def __init__(self):
        """Initiate members according to config and args."""
        wd = os.path.expanduser("~/")
        if args.working_directory:
            if os.path.exists(os.path.expanduser(args.working_directory)):
                wd = os.path.expanduser(args.working_directory)
            else:
                logger.warning("The argument working-directory={!r} is not a valid path.", args.working_directory)
        elif os.path.exists(os.path.expanduser(config.get("General", "working_directory"))):
            wd = os.path.expanduser(config.get("General", "working_directory"))

        self.working_directory = SingleState(os.path.abspath(wd))
        self.compiler_running = SingleState(False)
        self.main_file = SingleState(None)
        self.compiler_mode = SingleState(enums.compiler_mode[config.get("Compiler", "mode")])


# Instantiate the State singleton
State = GlobalState()

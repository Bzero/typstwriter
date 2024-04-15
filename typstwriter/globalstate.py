from qtpy import QtCore

from typstwriter import enums

from typstwriter import logging
from typstwriter import configuration

logger = logging.getLogger(__name__)
config = configuration.Config


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
            raise AttributeError("The only vlaid attributes are 'Value' and 'Signal'.")


class GlobalState():
    """Stores and initializes a collection of SingleStates."""

    def __init__(self):
        """Initiate members according to config."""
        self.working_directory = SingleState(config.get("General", "WorkingDirectory"))
        self.compiler_running = SingleState(False)
        self.main_file = SingleState(None)
        self.compiler_mode = SingleState(enums.compiler_mode[config.get("Compiler", "Mode")])


# Instantiate the State singleton
State = GlobalState()

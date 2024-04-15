from qtpy import QtCore
from qtpy import QtWidgets

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class ToolBar(QtWidgets.QToolBar):
    """Main Window Tool Bar."""

    def __init__(self, actions):
        """Populate Tool Bar."""
        QtWidgets.QToolBar.__init__(self)

        self.setMovable(False)
        self.setFloatable(False)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.addAction(actions.new_File)
        self.addAction(actions.open_File)
        self.addSeparator()
        self.addAction(actions.save)
        self.addAction(actions.save_as)
        self.addSeparator()
        self.addAction(actions.run)

from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import logging
import configuration
import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class CompilerOutput(QtWidgets.QFrame):
    """Displays the compiler output."""

    def __init__(self):
        """Populate the widget up."""
        QtWidgets.QFrame.__init__(self)

        self.OutputDisplay = QtWidgets.QTextEdit()
        self.OutputDisplay.setReadOnly(True)

        self.ClearDisplay = QtWidgets.QPushButton()
        self.ClearDisplay.setText("Clear Output")
        self.ClearDisplay.pressed.connect(self.OutputDisplay.clear)

        self.Layout = QtWidgets.QVBoxLayout(self)
        self.Layout.setContentsMargins(4, 4, 4, 4)
        self.Layout.setSpacing(2)
        self.Layout.addWidget(self.OutputDisplay)
        self.Layout.addWidget(self.ClearDisplay)

    def insert_block(self, text=None):
        """Insert a new block of text."""
        if not self.OutputDisplay.document().isEmpty():
            self.OutputDisplay.insertHtml("<p/><hr/><p/>")

        if text:
            self.OutputDisplay.insertPlainText(text)

    def append_to_block(self, text):
        """Append to the current block of text."""
        self.OutputDisplay.insertPlainText(text)

from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import logging
import configuration
import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class CompilerOptions(QtWidgets.QFrame):

    def __init__(self):
        QtWidgets.QFrame.__init__(self)

        self.FrameLayout = QtWidgets.QVBoxLayout(self)
        self.FrameLayout.setContentsMargins(4, 4, 4, 4)
        self.FrameLayout.setSpacing(2)

        self.HostWidget = QtWidgets.QFrame(self)
        self.HostWidget.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        palette = self.HostWidget.palette()
        palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("white"))
        self.HostWidget.setAutoFillBackground(True)
        self.HostWidget.setPalette(palette)
        self.FrameLayout.addWidget(self.HostWidget)

        self.Layout = QtWidgets.QGridLayout(self.HostWidget)
        self.Layout.setContentsMargins(4, 4, 4, 4)
        self.Layout.setSpacing(2)
        self.Layout.setAlignment(QtGui.Qt.AlignTop)

        # Row 1
        self.label_mode = QtWidgets.QLabel("Mode")
        self.combo_box_mode = QtWidgets.QComboBox()
        self.combo_box_mode.addItem("On Demand")  # For now there is only one compiler mode.

        # Row 2
        self.label_main = QtWidgets.QLabel("Main file")
        self.line_edit_main = QtWidgets.QLineEdit()

        self.Layout.addWidget(self.label_mode, 0, 0)
        self.Layout.addWidget(self.combo_box_mode, 0, 1)
        self.Layout.addWidget(self.label_main, 1, 0)
        self.Layout.addWidget(self.line_edit_main, 1, 1)

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

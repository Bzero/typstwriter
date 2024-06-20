from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import os

from typstwriter import enums
from typstwriter import util

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class CompilerOptions(QtWidgets.QWidget):
    """Displays the compiler options."""

    def __init__(self):
        """Populate the widget."""
        QtWidgets.QWidget.__init__(self)

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

        # Mode
        self.label_mode = QtWidgets.QLabel("Mode")
        self.combo_box_mode = QtWidgets.QComboBox()
        self.combo_box_mode.addItem("On Demand", enums.compiler_mode.on_demand)
        self.combo_box_mode.addItem("Live", enums.compiler_mode.live)
        self.combo_box_mode.currentIndexChanged.connect(self.mode_changed)
        self.combo_box_mode.setCurrentIndex(self.combo_box_mode.findData(state.compiler_mode.Value))

        # Main file
        self.label_main = QtWidgets.QLabel("Main file")
        self.line_edit_main = QtWidgets.QLineEdit(self)
        self.line_edit_main.setText("")
        self.line_edit_main.editingFinished.connect(self.main_path_edited)
        self.folderAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.FolderOpen, QtGui.QIcon(util.icon_path("folder.svg"))), "open"
        )
        self.folderAction.triggered.connect(self.open_file_dialog)
        self.line_edit_main.addAction(self.folderAction, QtWidgets.QLineEdit.LeadingPosition)

        # Insert everything into layout
        self.Layout.addWidget(self.label_mode, 0, 0)
        self.Layout.addWidget(self.combo_box_mode, 0, 1)
        self.Layout.addWidget(self.label_main, 1, 0)
        self.Layout.addWidget(self.line_edit_main, 1, 1)

    @QtCore.Slot()
    def main_path_edited(self):
        """Handle LineEdits editingFinished signal. Change main file path if it is valid and resets otherwise."""
        path = os.path.normpath(os.path.expanduser(self.line_edit_main.text()))
        if os.path.isfile(path):
            state.main_file.Value = path
        else:
            self.line_edit_main.setText(state.main_file.Value)
            logger.info("Attempted to set main file but {!r} is not a valid path.", path)

    @QtCore.Slot()
    def open_file_dialog(self):
        """Open a dialog to select the main file."""
        filters = "Typst Files (*.typ);;Any File (*)"
        path, cd = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", state.working_directory.Value, filters)

        if os.path.isfile(path):
            self.line_edit_main.setText(path)
            state.main_file.Value = path

    @QtCore.Slot(str)
    def main_changed(self, path):
        """Update display of main file."""
        self.line_edit_main.setText(path)

    @QtCore.Slot(int)
    def mode_changed(self, index):
        """Update the compiler mode."""
        mode = self.combo_box_mode.itemData(index)
        state.compiler_mode.Value = mode


class CompilerOutput(QtWidgets.QWidget):
    """Displays the compiler output."""

    def __init__(self):
        """Populate the widget up."""
        QtWidgets.QWidget.__init__(self)

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
        self.insert_text(new_block=True, text=text)

    def append_to_block(self, text):
        """Append to the current block of text."""
        self.insert_text(new_block=False, text=text)

    def insert_text(self, new_block=False, text=None):
        """Insert text."""
        bottom_scrolled = self.OutputDisplay.verticalScrollBar().value() == self.OutputDisplay.verticalScrollBar().maximum()

        if new_block and not self.OutputDisplay.document().isEmpty():
            self.OutputDisplay.insertHtml("<p/><hr/><p/>")

        if text:
            self.OutputDisplay.insertPlainText(text)

        if bottom_scrolled:
            self.OutputDisplay.verticalScrollBar().setValue(self.OutputDisplay.verticalScrollBar().maximum())

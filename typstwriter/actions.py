from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

from typstwriter import util

import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class Actions(QtCore.QObject):
    """Stores the commonly used actions."""

    def __init__(self, parent):
        """Init."""
        super().__init__(parent)

        self.new_File = QtWidgets.QAction(self)
        self.new_File.setIcon(QtGui.QIcon("icons/newFile.svg"))
        self.new_File.setShortcut(QtGui.QKeySequence.New)
        self.new_File.setText("New File")

        self.open_File = QtWidgets.QAction(self)
        self.open_File.setIcon(QtGui.QIcon("icons/openFile.svg"))
        self.open_File.setShortcut(QtGui.QKeySequence.Open)
        self.open_File.setText("Open File")

        self.open_recent_File = QtWidgets.QAction(self)
        self.open_recent_File.setIcon(QtGui.QIcon("icons/recentFile.svg"))
        self.open_recent_File.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL | QtCore.Qt.SHIFT | QtCore.Qt.Key_O))
        self.open_recent_File.setText("Open Recent File")

        self.save = QtWidgets.QAction(self)
        self.save.setIcon(QtGui.QIcon("icons/save.svg"))
        self.save.setShortcut(QtGui.QKeySequence.Save)
        self.save.setText("Save")

        self.save_as = QtWidgets.QAction(self)
        self.save_as.setIcon(QtGui.QIcon("icons/save_as.svg"))
        self.save_as.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL | QtCore.Qt.SHIFT | QtCore.Qt.Key_S))
        self.save_as.setText("Save As")

        self.close = QtWidgets.QAction(self)
        self.close.setIcon(QtGui.QIcon("icons/closeFile.svg"))
        self.close.setShortcut(QtGui.QKeySequence.Close)
        self.close.setText("Close")

        self.quit = QtWidgets.QAction(self)
        self.quit.setIcon(QtGui.QIcon("icons/quit.svg"))
        self.quit.setShortcut(QtGui.QKeySequence.Quit)
        self.quit.setText("Quit")

        self.cut = QtWidgets.QAction(self)
        self.cut.setIcon(QtGui.QIcon("icons/cut.svg"))
        self.cut.setShortcut(QtGui.QKeySequence.Cut)
        self.cut.setText("Cut")

        self.copy = QtWidgets.QAction(self)
        self.copy.setIcon(QtGui.QIcon("icons/copy.svg"))
        self.copy.setShortcut(QtGui.QKeySequence.Copy)
        self.copy.setText("Copy")

        self.paste = QtWidgets.QAction(self)
        self.paste.setIcon(QtGui.QIcon("icons/paste.svg"))
        self.paste.setShortcut(QtGui.QKeySequence.Paste)
        self.paste.setText("Paste")

        self.search = QtWidgets.QAction(self)
        self.search.setIcon(QtGui.QIcon("icons/quit.svg"))
        self.search.setShortcut(QtGui.QKeySequence.Find)
        self.search.setText("Search")

        self.layout_typewriter = QtWidgets.QAction(self)
        self.layout_typewriter.setText("Layout: Typewriter")
        self.layout_typewriter.setCheckable(True)

        self.layout_editorL = QtWidgets.QAction(self)
        self.layout_editorL.setText("Layout: Editor Left")
        self.layout_editorL.setCheckable(True)

        self.layout_editorR = QtWidgets.QAction(self)
        self.layout_editorR.setText("Layout: Editor Right")
        self.layout_editorR.setCheckable(True)

        self.layout = QtWidgets.QActionGroup(self)
        self.layout.addAction(self.layout_typewriter)
        self.layout.addAction(self.layout_editorL)
        self.layout.addAction(self.layout_editorR)

        self.show_fs_explorer = QtWidgets.QAction(self)
        self.show_fs_explorer.setText("Show FS Explorer")
        self.show_fs_explorer.setCheckable(True)

        self.show_compiler_options = QtWidgets.QAction(self)
        self.show_compiler_options.setText("Show Compiler Options")
        self.show_compiler_options.setCheckable(True)

        self.show_compiler_output = QtWidgets.QAction(self)
        self.show_compiler_output.setText("Show Compiler Output")
        self.show_compiler_output.setCheckable(True)

        self.open_config = QtWidgets.QAction(self)
        self.open_config.setText("Open config file")

        self.run = util.TogglingAction(self)
        icon = QtGui.QIcon()
        icon.addFile("icons/start.svg", state=QtGui.QIcon.State.Off)
        icon.addFile("icons/stop.svg", state=QtGui.QIcon.State.On)
        self.run.setIcon(icon)
        self.run.setText("Start", state=QtGui.QIcon.State.Off)
        self.run.setText("Stop", state=QtGui.QIcon.State.On)
        self.run.setShortcut("Ctrl+R")




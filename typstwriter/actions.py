from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

from typstwriter import util

from typstwriter import logging
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
        self.new_File.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.DocumentNew, QtGui.QIcon(util.icon_path("newFile.svg"))))
        self.new_File.setShortcut(QtGui.QKeySequence.New)
        self.new_File.setText("New File")

        self.open_File = QtWidgets.QAction(self)
        self.open_File.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.DocumentOpen, QtGui.QIcon(util.icon_path("openFile.svg"))))
        self.open_File.setShortcut(QtGui.QKeySequence.Open)
        self.open_File.setText("Open File")

        self.open_recent_File = QtWidgets.QAction(self)
        self.open_recent_File.setIcon(
            QtGui.QIcon.fromTheme(QtGui.QIcon.DocumentOpenRecent, QtGui.QIcon(util.icon_path("recentFile.svg")))
        )
        self.open_recent_File.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL | QtCore.Qt.SHIFT | QtCore.Qt.Key_O))
        self.open_recent_File.setText("Open Recent File")

        self.load_last_Session = QtWidgets.QAction(self)
        self.load_last_Session.setIcon(
            QtGui.QIcon.fromTheme("folder-open-recent", QtGui.QIcon(util.icon_path("lastSession.svg")))
        )
        self.load_last_Session.setText("Load last Session")

        self.save = QtWidgets.QAction(self)
        self.save.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.DocumentSave, QtGui.QIcon(util.icon_path("save.svg"))))
        self.save.setShortcut(QtGui.QKeySequence.Save)
        self.save.setText("Save")

        self.save_as = QtWidgets.QAction(self)
        self.save_as.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.DocumentSaveAs, QtGui.QIcon(util.icon_path("save_as.svg"))))
        self.save_as.setShortcut(QtGui.QKeySequence(QtCore.Qt.CTRL | QtCore.Qt.SHIFT | QtCore.Qt.Key_S))
        self.save_as.setText("Save As")

        self.close = QtWidgets.QAction(self)
        self.close.setIcon(QtGui.QIcon.fromTheme("document-close-symbolic", QtGui.QIcon(util.icon_path("closeFile.svg"))))
        self.close.setShortcut(QtGui.QKeySequence.Close)
        self.close.setText("Close")

        self.quit = QtWidgets.QAction(self)
        self.quit.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ApplicationExit, QtGui.QIcon(util.icon_path("quit.svg"))))
        self.quit.setShortcut(QtGui.QKeySequence.Quit)
        self.quit.setText("Quit")

        self.cut = QtWidgets.QAction(self)
        self.cut.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.EditCut, QtGui.QIcon(util.icon_path("cut.svg"))))
        self.cut.setShortcut(QtGui.QKeySequence.Cut)
        self.cut.setText("Cut")

        self.copy = QtWidgets.QAction(self)
        self.copy.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.EditCopy, QtGui.QIcon(util.icon_path("copy.svg"))))
        self.copy.setShortcut(QtGui.QKeySequence.Copy)
        self.copy.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.copy.setText("Copy")

        self.paste = QtWidgets.QAction(self)
        self.paste.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.EditPaste, QtGui.QIcon(util.icon_path("paste.svg"))))
        self.paste.setShortcut(QtGui.QKeySequence.Paste)
        self.paste.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.paste.setText("Paste")

        self.search = QtWidgets.QAction(self)
        self.search.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.EditFind, QtGui.QIcon(util.icon_path("search.svg"))))
        self.search.setShortcut(QtGui.QKeySequence.Find)
        self.search.setText("Search")

        self.font_size_up = QtWidgets.QAction(self)
        self.font_size_up.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ZoomIn, QtGui.QIcon(util.icon_path("plus.svg"))))
        self.font_size_up.setText("Increase Font Size")

        self.font_size_dn = QtWidgets.QAction(self)
        self.font_size_dn.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ZoomOut, QtGui.QIcon(util.icon_path("minus.svg"))))
        self.font_size_dn.setText("Decrease Font Size")

        self.font_size_reset = QtWidgets.QAction(self)
        self.font_size_reset.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ZoomFitBest))
        self.font_size_reset.setText("Reset Font Size")

        self.layout_typewriter = QtWidgets.QAction(self)
        self.layout_typewriter.setIcon(QtGui.QIcon.fromTheme("view-split-top-bottom-symbolic"))
        self.layout_typewriter.setText("Layout: Typewriter")
        self.layout_typewriter.setCheckable(True)

        self.layout_editorL = QtWidgets.QAction(self)
        self.layout_editorL.setIcon(QtGui.QIcon.fromTheme("view-split-left-right-symbolic"))
        self.layout_editorL.setText("Layout: Editor Left")
        self.layout_editorL.setCheckable(True)

        self.layout_editorR = QtWidgets.QAction(self)
        self.layout_editorR.setIcon(QtGui.QIcon.fromTheme("view-split-left-right-symbolic"))
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
        self.open_config.setIcon(QtGui.QIcon.fromTheme("configure-symbolic"))
        self.open_config.setText("Open config file")

        self.run = util.TogglingAction(self)
        self.run.setIcon(
            QtGui.QIcon.fromTheme(QtGui.QIcon.MediaPlaybackStart, QtGui.QIcon(util.icon_path("start.svg"))),
            state=QtGui.QIcon.State.Off,
        )
        self.run.setIcon(
            QtGui.QIcon.fromTheme(QtGui.QIcon.MediaPlaybackStop, QtGui.QIcon(util.icon_path("stop.svg"))),
            state=QtGui.QIcon.State.On,
        )
        self.run.setText("Start", state=QtGui.QIcon.State.Off)
        self.run.setText("Stop", state=QtGui.QIcon.State.On)
        self.run.setShortcut("Ctrl+R")

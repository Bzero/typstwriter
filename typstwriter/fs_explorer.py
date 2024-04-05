from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import os

import util

import logging
import configuration
import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class FSExplorer(QtWidgets.QWidget):
    """A filesystem explorer widget."""

    # directoryChanged = QtCore.Signal(str)
    open_file = QtCore.Signal(str)

    def __init__(self):
        """Populate widget and set initial state."""
        QtWidgets.QWidget.__init__(self)

        # Populate Widget
        self.Layout = QtWidgets.QVBoxLayout(self)
        self.Layout.setContentsMargins(4, 4, 4, 4)
        self.Layout.setSpacing(2)

        self.pathBar = QtWidgets.QLineEdit(self)
        self.pathBar.setText("")
        self.pathBar.editingFinished.connect(self.line_edited)
        self.folderAction = QtWidgets.QAction(QtGui.QIcon("icons/folder.svg"), "open")
        self.folderAction.triggered.connect(self.open_directory_dialog)
        self.pathBar.addAction(self.folderAction, QtWidgets.QLineEdit.LeadingPosition)

        self.tree_view = QtWidgets.QTreeView()
        self.filesystem_model = QtWidgets.QFileSystemModel(self.tree_view)
        self.filesystem_model.setIconProvider(util.FileIconProvider())
        self.tree_view.setModel(self.filesystem_model)
        self.tree_view.setRootIsDecorated(True)
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.header().setSectionsMovable(False)
        self.tree_view.header().setStretchLastSection(False)
        self.tree_view.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.tree_view.header().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.tree_view.doubleClicked.connect(self.doubleclicked)

        # A second filesystem model is needed for the completer because only directories should be shown as completions
        # while both files and directories should be shown in the tree vies.
        # This duplication is somewhat unsatisfying but it was decently simple to implement and the overhead is acceptable.
        self.completer_filesystem_model = QtWidgets.QFileSystemModel()
        self.completer_filesystem_model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        self.completer = QtWidgets.QCompleter()
        self.completer.setModel(self.completer_filesystem_model)
        self.pathBar.setCompleter(self.completer)

        self.Layout.addWidget(self.pathBar)
        self.Layout.addWidget(self.tree_view)

        # Set initial state
        self.set_root(QtCore.QDir.homePath())

    def open_directory_dialog(self):
        """Open a dialog to select root path and open said path."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Working Directory", self.pathBar.text(),
                    QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)

        if os.path.isdir(directory):
            self.set_root(directory)

    def set_root(self, root):
        """Set the root directory of the FSExplorer."""
        self.root = root
        self.filesystem_model.setRootPath(root)
        self.tree_view.setRootIndex(self.filesystem_model.index(root))
        self.completer_filesystem_model.setRootPath(root)
        self.pathBar.setText(root)
        state.working_directory.Value = root
        logger.info(f"Change Working Directory to '{root}'.")
        # self.directoryChanged.emit(root)

    @QtCore.Slot()
    def line_edited(self):
        """Handle LineEdits editingFinished signal. Change root directory if path is valid and resets otherwise."""
        root = os.path.normpath(os.path.expanduser(self.pathBar.text()))
        if os.path.isdir(root):
            self.set_root(root)
        else:
            self.pathBar.setText(self.root)
            logger.info(f"Attempted to change Working Directory but '{root}' is not a valid directory.")

    @QtCore.Slot(QtCore.QModelIndex)
    def doubleclicked(self, index):
        """Handle doubleclick on tree-view entry. Open file or changes root directory."""
        path = self.filesystem_model.filePath(index)
        if os.path.isfile(path):
            self.open_file.emit(path)
        if os.path.isdir(path):
            self.set_root(path)

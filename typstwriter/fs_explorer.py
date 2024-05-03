from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import os

import send2trash

from typstwriter import util

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class FSContextMenu(QtWidgets.QMenu):
    """
    Base context menu for the fs Explorer.

    This class contains all actions and handlers that may be needed in a FS context menu.
    It does not actually construct a menu however, this is done in a subclass which can
    use a selection of the actions declared in this clas to populate the menu.
    """

    def __init__(self, parent):
        """Declare all actions."""
        QtWidgets.QMenu.__init__(self, parent)
        self.context_path = None

        self.action_open = QtWidgets.QAction("Open", triggered=self.handle_open)
        self.action_new_file = QtWidgets.QAction("New file", triggered=self.handle_new_file)
        self.action_new_folder = QtWidgets.QAction("New folder", triggered=self.handle_new_folder)
        self.action_rename = QtWidgets.QAction("Rename", triggered=self.handle_rename)
        self.action_delete = QtWidgets.QAction("Delete", triggered=self.handle_delete)
        self.setRoot = QtWidgets.QAction("Set as Working Directory", triggered=self.handle_set_root)
        self.action_copy_path = QtWidgets.QAction("Copy path", triggered=self.handle_copy_path)
        self.action_main_file = QtWidgets.QAction("Set as main file", triggered=self.handle_set_as_main_file)

    def handle_open(self):
        """Trigger opening a file."""
        self.parent().open_file.emit(self.context_path)

    def handle_new_file(self):
        """Trigger creating a new file."""
        self.parent().new_file_in_dir(self.context_path)

    def handle_new_folder(self):
        """Trigger creating a new folder."""
        self.parent().new_folder_in_dir(self.context_path)

    def handle_rename(self):
        """Trigger renaming folder."""
        self.parent().rename_from(self.context_path)

    def handle_delete(self):
        """Trigger deleteing file or folder."""
        self.parent().delete(self.context_path)

    def handle_set_root(self):
        """Trigger setting the current folder as working directory."""
        self.parent().set_root(self.context_path)

    def handle_copy_path(self):
        """Trigger copying path to the clipboard."""
        QtGui.QGuiApplication.clipboard().setText(self.context_path)

    def handle_set_as_main_file(self):
        """Trigger setting the current file as main file."""
        state.main_file.Value = self.context_path


class NoItemContextMenu(FSContextMenu):
    """Context menu when not clicking on any item."""

    def __init__(self, parent):
        """Assemble Menu."""
        FSContextMenu.__init__(self, parent)

        self.addAction(self.action_new_file)
        self.addAction(self.action_new_folder)


class FileContextMenu(FSContextMenu):
    """Context menu when clicking on a file."""

    def __init__(self, parent):
        """Assemble Menu."""
        FSContextMenu.__init__(self, parent)

        self.addAction(self.action_open)
        self.addAction(self.action_rename)
        self.addAction(self.action_delete)
        self.addAction(self.action_copy_path)
        self.addAction(self.action_main_file)


class FolderContextMenu(FSContextMenu):
    """Context menu when clicking on a folder."""

    def __init__(self, parent):
        """Assemble Menu."""
        FSContextMenu.__init__(self, parent)

        self.addAction(self.action_new_file)
        self.addAction(self.action_new_folder)
        self.addAction(self.action_rename)
        self.addAction(self.action_delete)
        self.addAction(self.setRoot)


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
        self.folderAction = QtWidgets.QAction(QtGui.QIcon(util.icon_path("folder.svg")), "open")
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
        # while both files and directories should be shown in the tree view.
        # This duplication is somewhat unsatisfying but it was decently simple to implement and the overhead is acceptable.
        self.completer_filesystem_model = QtWidgets.QFileSystemModel()
        self.completer_filesystem_model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.NoDotAndDotDot)
        self.completer = QtWidgets.QCompleter()
        self.completer.setModel(self.completer_filesystem_model)
        self.pathBar.setCompleter(self.completer)

        self.Layout.addWidget(self.pathBar)
        self.Layout.addWidget(self.tree_view)

        # Add Context Menu
        self.tree_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.rightclicked)
        self.NoItemContextMenu = NoItemContextMenu(self)
        self.FileContextMenu = FileContextMenu(self)
        self.FolderContextMenu = FolderContextMenu(self)

        # Set initial state
        root_dir = os.path.expanduser(config.get("General", "working_directory"))
        if not os.path.exists(root_dir):
            root_dir = os.path.expanduser("~/")
        self.set_root(root_dir)

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
        logger.debug("Change Working Directory to {!r}.", root)
        # self.directoryChanged.emit(root)

    @QtCore.Slot()
    def line_edited(self):
        """Handle LineEdits editingFinished signal. Change root directory if path is valid and resets otherwise."""
        root = os.path.normpath(os.path.expanduser(self.pathBar.text()))
        if os.path.isdir(root):
            self.set_root(root)
        else:
            self.pathBar.setText(self.root)
            logger.info("Attempted to change Working Directory but {!r} is not a valid directory.", root)

    @QtCore.Slot(QtCore.QModelIndex)
    def doubleclicked(self, index):
        """Handle doubleclick on tree-view entry. Open file or changes root directory."""
        path = self.filesystem_model.filePath(index)
        if os.path.isfile(path):
            self.open_file.emit(path)
        if os.path.isdir(path):
            self.set_root(path)

    def rightclicked(self, event):
        """Handle right click."""
        index = self.tree_view.indexAt(event)
        if not index.isValid():
            self.open_no_item_menu()
        else:
            path = self.filesystem_model.filePath(index)
            if os.path.isfile(path):
                self.open_file_menu(index)
            if os.path.isdir(path):
                self.open_folder_menu(index)

    def open_no_item_menu(self):
        """Open context menu when clicking on no item."""
        path = self.filesystem_model.rootPath()
        self.NoItemContextMenu.context_path = path
        self.NoItemContextMenu.popup(QtGui.QCursor.pos())

    def open_folder_menu(self, index):
        """Open context menu when clicking on a folder."""
        path = self.filesystem_model.filePath(index)
        self.FolderContextMenu.context_path = path
        self.FolderContextMenu.popup(QtGui.QCursor.pos())

    def open_file_menu(self, index):
        """Open context menu when clicking on a file."""
        path = self.filesystem_model.filePath(index)
        self.FileContextMenu.context_path = path
        self.FileContextMenu.popup(QtGui.QCursor.pos())

    #TODO: Possibly move the functions below to an own class or module as they dont directly relate to the FSExplorer
    def new_file_in_dir(self, head_path):
        """Prompts the user to ender a filename and creates that file in head_path."""
        tail_path, ok = QtWidgets.QInputDialog.getText(self, "Typstwriter", "Enter filename:", QtWidgets.QLineEdit.Normal)
        if ok and tail_path:
            path = os.path.join(head_path, tail_path)
            self.new_file(path)

    def new_file(self, path, overwrite=False):
        """Create new file in {path}."""
        if not os.path.exists(path) or overwrite:
            open(path, "w").close()
        else:
            logger.warning("File {!r} already exists. Will not overwrite.", path)
            QtWidgets.QMessageBox.warning(self, "Typstwriter", f"File '{path}' already exists.\nWill not overwrite.")

    def new_folder_in_dir(self, head_path):
        """Prompts the user to enter a foldername and creates that folder in head_path."""
        tail_path, ok = QtWidgets.QInputDialog.getText(self, "Typstwriter", "Enter foldername:", QtWidgets.QLineEdit.Normal)
        if ok and tail_path:
            path = os.path.join(head_path, tail_path)
            self.new_folder(path)

    def new_folder(self, path, overwrite=False):
        """Create new folder in {path}."""
        if not os.path.exists(path) or overwrite:
            os.makedirs(path)
        else:
            logger.warning("Folder {!r} already exists. Will not overwrite.", path)
            QtWidgets.QMessageBox.warning(self, "Typstwriter", f"Folder '{path}' already exists.\nWill not overwrite.")

    def rename_from(self, path_from):
        """Prompts the user to enter a new name."""
        head_path, tail_path_from = os.path.split(path_from)
        tail_path_to, ok = QtWidgets.QInputDialog.getText(self, "Typstwriter", "Enter new name:", QtWidgets.QLineEdit.Normal, text=tail_path_from)
        if ok and tail_path_to:
            path_to = os.path.join(head_path, tail_path_to)
            self.rename(path_from, path_to)

    def rename(self, path_from, path_to, overwrite=False):
        """Rename a file or folder from path_from to path_to."""
        if not os.path.exists(path_to) or overwrite:
            os.rename(path_from, path_to)
        else:
            logger.warning("{!r} already exists. Will not overwrite.", path_to)
            QtWidgets.QMessageBox.warning(self, "Typstwriter", f"'{path_to}' already exists.\nWill not overwrite.")

    def delete(self, path):
        """Delete a folder or file."""
        msg = QtWidgets.QMessageBox.question(self, "Typstwriter", f"Should '{path}' be deleted?")
        if msg == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                send2trash.send2trash(path)
            except send2trash.TrashPermissionError:
                logger.warning("Could not move {!r} to trash.")

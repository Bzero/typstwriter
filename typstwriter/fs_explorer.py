from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import os
import shutil

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
        self.action_open_external = QtWidgets.QAction("Open with external program", triggered=self.handle_open_external)
        self.action_new_file = QtWidgets.QAction("New file", triggered=self.handle_new_file)
        self.action_new_folder = QtWidgets.QAction("New folder", triggered=self.handle_new_folder)
        self.action_rename = QtWidgets.QAction("Rename", triggered=self.handle_rename)
        self.action_delete = QtWidgets.QAction("Delete", triggered=self.handle_delete)
        self.setRoot = QtWidgets.QAction("Set as Working Directory", triggered=self.handle_set_root)
        self.action_copy_path = QtWidgets.QAction("Copy path", triggered=self.handle_copy_path)
        self.action_copy = QtWidgets.QAction("Copy", triggered=self.handle_copy)
        self.action_paste = QtWidgets.QAction("Paste", triggered=self.handle_paste)
        self.action_main_file = QtWidgets.QAction("Set as main file", triggered=self.handle_set_as_main_file)

    def handle_open(self):
        """Trigger opening a file."""
        self.parent().open_file.emit(self.context_path)

    def handle_open_external(self):
        """Trigger opening a file."""
        util.open_with_external_program(self.context_path)

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

    def handle_copy(self):
        """Trigger copying file or folder to the clipboard."""
        self.parent().copy_to_clipboard(self.context_path)

    def handle_paste(self):
        """Trigger pasting from the clipboard."""
        self.parent().paste_from_clipboard(self.context_path)

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
        self.addAction(self.action_paste)


class FileContextMenu(FSContextMenu):
    """Context menu when clicking on a file."""

    def __init__(self, parent):
        """Assemble Menu."""
        FSContextMenu.__init__(self, parent)

        self.addAction(self.action_open)
        self.addAction(self.action_open_external)
        self.addAction(self.action_rename)
        self.addAction(self.action_delete)
        self.addAction(self.action_copy)
        self.addAction(self.action_copy_path)
        self.addAction(self.action_main_file)


class FolderContextMenu(FSContextMenu):
    """Context menu when clicking on a folder."""

    def __init__(self, parent):
        """Assemble Menu."""
        FSContextMenu.__init__(self, parent)

        self.addAction(self.action_new_file)
        self.addAction(self.action_new_folder)
        self.addAction(self.action_copy)
        self.addAction(self.action_copy_path)
        self.addAction(self.action_paste)
        self.addAction(self.action_rename)
        self.addAction(self.action_delete)
        self.addAction(self.setRoot)


class SelectionContextMenu(FSContextMenu):
    """Context menu when clicking on a selection."""

    def __init__(self, parent):
        """Assemble Menu."""
        FSContextMenu.__init__(self, parent)

        self.addAction(self.action_delete)
        self.addAction(self.action_copy)


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

        self.folderAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.FolderOpen, QtGui.QIcon(util.icon_path("folder.svg"))), "open"
        )
        self.folderAction.triggered.connect(self.open_directory_dialog)
        self.pathBar.addAction(self.folderAction, QtWidgets.QLineEdit.LeadingPosition)

        self.parentAction = QtWidgets.QAction(
            QtGui.QIcon.fromTheme(QtGui.QIcon.GoUp, QtGui.QIcon(util.icon_path("parent_dir.svg"))), "up"
        )
        self.parentAction.triggered.connect(self.goto_parent_directory)
        self.pathBar.addAction(self.parentAction, QtWidgets.QLineEdit.TrailingPosition)

        self.tree_view = QtWidgets.QTreeView()
        self.filesystem_model = QtWidgets.QFileSystemModel(self.tree_view)
        self.filesystem_model.setIconProvider(util.FileIconProvider())
        self.tree_view.setModel(self.filesystem_model)
        self.tree_view.setRootIsDecorated(True)
        self.tree_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
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
        self.SelectionContextMenu = SelectionContextMenu(self)

        # Set initial state
        self.set_root(os.path.normpath(state.working_directory.Value))

    def open_directory_dialog(self):
        """Open a dialog to select root path and open said path."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Working Directory",
            self.pathBar.text(),
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks,
        )

        if os.path.isdir(directory):
            self.set_root(directory)

    def set_root(self, root):
        """Set the root directory of the FSExplorer."""
        state.working_directory.Value = root
        self.root_changed(root)

    @QtCore.Slot(str)
    def root_changed(self, root):
        """Update root directory."""
        self.root = root
        self.filesystem_model.setRootPath(root)
        self.tree_view.setRootIndex(self.filesystem_model.index(root))
        self.completer_filesystem_model.setRootPath(root)
        self.pathBar.setText(root)
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

    @QtCore.Slot()
    def goto_parent_directory(self):
        """Set the parent of the current directory as root."""
        path = os.path.dirname(self.root)
        self.set_root(path)

    def rightclicked(self, event):
        """Handle right click."""
        index = self.tree_view.indexAt(event)
        if not index.isValid():
            self.open_no_item_menu()
            return
        else:
            selected_indices = self.tree_view.selectionModel().selectedRows()
            if index in selected_indices and len(selected_indices) > 1:
                self.open_selection_menu(index)
                return
            path = self.filesystem_model.filePath(index)
            if os.path.isfile(path):
                self.open_file_menu(index)
                return
            if os.path.isdir(path):
                self.open_folder_menu(index)
                return

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

    def open_selection_menu(self, index):
        """Open context menu when clicking on a selection."""
        paths = self.selected_paths()
        self.SelectionContextMenu.context_path = paths
        self.SelectionContextMenu.popup(QtGui.QCursor.pos())

    def keyPressEvent(self, e):  # This is an overriding function # noqa: N802
        """Intercept keyPressEvent."""
        if e.key() == QtCore.Qt.Key_Delete and e.modifiers() == QtCore.Qt.NoModifier:
            self.delete(self.selected_paths())
        if e.key() == QtCore.Qt.Key_C and e.modifiers() == QtCore.Qt.ControlModifier:
            self.copy_to_clipboard(self.selected_paths())
        if e.key() == QtCore.Qt.Key_V and e.modifiers() == QtCore.Qt.ControlModifier:
            self.paste_from_clipboard(self.filesystem_model.rootPath())
        super().keyPressEvent(e)

    def selected_paths(self):
        """Return the paths of the currently selected items."""
        selected_paths = []
        for index in self.tree_view.selectionModel().selectedRows():
            if index.isValid():
                path = self.filesystem_model.filePath(index)
                selected_paths.append(path)
        return selected_paths

    # TODO: Possibly move the functions below to an own class or module as they dont directly relate to the FSExplorer
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
        tail_path_to, ok = QtWidgets.QInputDialog.getText(
            self, "Typstwriter", "Enter new name:", QtWidgets.QLineEdit.Normal, text=tail_path_from
        )
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

    def copy_to_clipboard(self, paths):
        """Copy a list of files or foler to the clipboard."""
        if not isinstance(paths, list):
            paths = [paths]

        urls = [QtCore.QUrl.fromLocalFile(path) for path in paths if os.path.exists(path)]

        if urls:
            mime_data = QtCore.QMimeData()
            mime_data.setUrls(urls)
            QtGui.QGuiApplication.clipboard().setMimeData(mime_data)

    def paste_from_clipboard(self, path):
        """Paste a file or folder from cliboard into path."""
        mime_data = QtGui.QGuiApplication.clipboard().mimeData()

        if mime_data.hasUrls():
            for uri in mime_data.data("text/uri-list").data().decode().split():
                fs = QtCore.QUrl(uri).toLocalFile()
                if os.path.exists(fs):
                    head, tail = os.path.split(fs)
                    path_to = os.path.join(path, tail)

                    if os.path.exists(path_to):
                        new_tail, ok = QtWidgets.QInputDialog.getText(
                            self,
                            "Typstwriter",
                            "Destination already exists. Enter new name:",
                            QtWidgets.QLineEdit.Normal,
                            text=tail,
                        )
                        path_to = os.path.join(path, new_tail)
                        if not ok:
                            return

                    self.copy_from_to(fs, path_to)

    def copy_from_to(self, path_from, path_to, overwrite=False):
        """Copy a file or folder from path_from to path_to."""
        if not os.path.isdir(os.path.split(path_to)[0]):
            return

        if not os.path.exists(path_from):
            return

        if not overwrite and os.path.exists(path_to):
            logger.warning("{!r} already exists. Will not overwrite.", path_to)
            QtWidgets.QMessageBox.warning(self, "Typstwriter", f"'{path_to}' already exists.\nWill not overwrite.")
            return

        if os.path.isdir(path_from):
            shutil.copytree(path_from, path_to, dirs_exist_ok=overwrite)
        else:
            shutil.copy2(path_from, path_to)

    def delete(self, paths):
        """Delete a folder or file."""
        if not isinstance(paths, list):
            paths = [paths]

        for path in paths:
            msg = QtWidgets.QMessageBox.question(self, "Typstwriter", f"Should '{path}' be deleted?")
            if msg == QtWidgets.QMessageBox.StandardButton.Yes:
                deletion_succeeded = QtCore.QFile.moveToTrash(path)
                if not deletion_succeeded:
                    logger.warning("Could not move {!r} to trash.", path)

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


class Editor(QtWidgets.QFrame):
    """A tabbed text editor."""

    text_changed = QtCore.Signal()
    recent_files_changed = QtCore.Signal(list)
    active_file_changed = QtCore.Signal(str)

    def __init__(self):
        """Initialize and display welcome page."""
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)

        self.Layout = QtWidgets.QVBoxLayout(self)
        self.Layout.setContentsMargins(0, 0, 0, 0)

        self.TabWidget = QtWidgets.QTabWidget(self)
        self.Layout.addWidget(self.TabWidget)

        self.TabWidget.setTabsClosable(True)
        self.TabWidget.setMovable(True)
        self.TabWidget.setUsesScrollButtons(True)
        self.TabWidget.setDocumentMode(True)
        # self.TabWidget.setTabPosition(QtWidgets.QTabWidget.TabPosition.South)

        self.TabWidget.tabCloseRequested.connect(self.close_tab)
        self.TabWidget.currentChanged.connect(self.tab_changed)
        state.working_directory.Signal.connect(self.update_tab_names)

        self.recentFiles = util.RecentFiles()

        self.welcome()

    def new_file(self):
        """Open a new, empty file."""
        editorpage = EditorPage()
        name = "*new*"
        icon = QtGui.QIcon("icons/newFile.svg")
        self.TabWidget.addTab(editorpage, icon, name)
        self.TabWidget.setCurrentIndex(self.TabWidget.count()-1)
        self.TabWidget.tabBar().setTabTextColor(self.TabWidget.count()-1, QtGui.QColor("green"))

        editorpage.edit.textChanged.connect(self.childtext_changed)
        editorpage.savestatechanged.connect(self.childsavedstate_changed)
        editorpage.pathchanged.connect(self.childpath_changed)

    def open_file(self, path):
        """Open an existing file or switch to it if it is already open."""
        if path not in self.openfiles_list():
            editorpage = EditorPage(path)
            name = os.path.relpath(path, start=state.working_directory.Value)
            icon = util.FileIconProvider().icon(QtCore.QFileInfo(path))
            self.TabWidget.addTab(editorpage, icon, name)
            self.TabWidget.setCurrentIndex(self.TabWidget.count()-1)
            self.recentFiles.append(path)
            self.TabWidget.tabBar().setTabTextColor(self.TabWidget.count()-1, QtGui.QColor("black"))

            editorpage.edit.textChanged.connect(self.childtext_changed)
            editorpage.savestatechanged.connect(self.childsavedstate_changed)
            editorpage.pathchanged.connect(self.childpath_changed)

            self.recent_files_changed.emit(self.recentFiles.list())
        else:
            index = self.openfiles_list().index(path)
            self.TabWidget.setCurrentIndex(index)

    def open_file_dialog(self):
        """Open a dialog to open an existing file."""
        filters = "Typst Files (*.ty);;Any File (*)"
        path, cd = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", QtCore.QDir.homePath(), filters)
        if path:
            self.open_file(path)

    def close_tab(self, index):
        """Close a tab."""
        editorpage = self.TabWidget.widget(index)
        e = editorpage.tryclose()
        if e:
            editorpage.deleteLater()
            self.TabWidget.removeTab(index)

        if len(self.tabs_list()) == 0:
            self.welcome()

    def closeactive_tab(self):
        """Close active tab."""
        self.close_tab(self.TabWidget.currentIndex())

    def saveactive_tab(self):
        """Save active tab."""
        page = self.TabWidget.currentWidget()
        if isinstance(page, EditorPage):
            page.save()

    def saveactive_tab_as(self):
        """Save active tab."""
        page = self.TabWidget.currentWidget()
        if isinstance(page, EditorPage):
            page.save_as()

    def welcome(self):
        """Display welcome tab."""
        welcomepage = WelcomePage(self.recentFiles.list())
        icon = QtGui.QIcon()
        self.TabWidget.addTab(welcomepage, icon, "Welcome")
        self.TabWidget.setCurrentIndex(self.TabWidget.count()-1)
        self.TabWidget.tabBar().setTabTextColor(self.TabWidget.count()-1, QtGui.QColor("blue"))
        welcomepage.button_NewFile.pressed.connect(self.new_file)
        welcomepage.button_OpenFile.pressed.connect(self.open_file_dialog)
        welcomepage.open_file.connect(self.open_file)
        self.recent_files_changed.connect(welcomepage.update_recent_files)

    def tabs_list(self):
        """Return (ordered) list of open tabs."""
        return [self.TabWidget.widget(i) for i in range(0, self.TabWidget.count())]

    def openfiles_list(self):
        """Return (ordered) list of opened files."""
        return [t.path for t in self.tabs_list()]

    def tryclose(self):
        """Try closing the editor, i.e. close all tabs and save the recent files."""
        for t in self.tabs_list():
            s = t.tryclose()
            if not s:
                return False
        self.recentFiles.write()
        return True

    @QtCore.Slot()
    def copy(self):
        """Cut selection of active tab."""
        page = self.TabWidget.currentWidget()
        if isinstance(page, EditorPage):
            page.edit.copy()

    @QtCore.Slot()
    def cut(self):
        """Cut selection of active tab."""
        page = self.TabWidget.currentWidget()
        if isinstance(page, EditorPage):
            page.edit.cut()

    @QtCore.Slot()
    def paste(self):
        """Cut selection of active tab."""
        page = self.TabWidget.currentWidget()
        if isinstance(page, EditorPage):
            page.edit.paste()

    @QtCore.Slot()
    def childtext_changed(self):
        """Trigger textChanged."""
        self.text_changed.emit()

    @QtCore.Slot(bool)
    def childsavedstate_changed(self, savestate):
        """Trigger textChanged."""
        i = self.TabWidget.indexOf(self.sender())
        if savestate:
            self.TabWidget.tabBar().setTabTextColor(i, QtGui.QColor("black"))
        else:
            self.TabWidget.tabBar().setTabTextColor(i, QtGui.QColor("red"))

    @QtCore.Slot(str)
    def childpath_changed(self, path):
        """Update tab name based on new path."""
        i = self.TabWidget.indexOf(self.sender())
        name = os.path.relpath(path, start=state.working_directory.Value)
        self.TabWidget.tabBar().setTabText(i, name)

    @QtCore.Slot()
    def update_tab_names(self):
        """Update all tab names according to the current working directory."""
        for i, t in enumerate(self.tabs_list()):
            if t.path:
                name = os.path.relpath(t.path, start=state.working_directory.Value)
                self.TabWidget.tabBar().setTabText(i, name)

    @QtCore.Slot(int)
    def tab_changed(self, i):
        """Emit active_file_changed signal."""
        page = self.TabWidget.widget(i)
        if page:
            self.active_file_changed.emit(page.path)


class EditorPage(QtWidgets.QFrame):
    """A single editor page."""

    savestatechanged = QtCore.Signal(bool)
    pathchanged = QtCore.Signal(str)

    def __init__(self, path=None):
        """Set up and load file if path is given."""
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)

        self.edit = QtWidgets.QPlainTextEdit()
        self.verticalLayout.addWidget(self.edit)

        self.edit.textChanged.connect(self.modified)

        self.path = path
        self.issaved = True
        if path:
            self.load(path)

    def load(self, path):
        """Load file."""
        try:
            with open(path, "r") as file:
                filecontent = file.read()

            self.edit.setPlainText(filecontent)
            self.issaved = True
            self.path = path
            self.pathchanged.emit(self.path)

        except UnicodeError:
            msg = f"'{path}' is not a text file."
            logger.warning(msg)
            self.show_error(msg)

        except OSError:
            msg = f"'{path}' is not a valid file."
            logger.warning(msg)
            self.show_error(msg)

    def save(self):
        """Save file."""
        if not self.path:
            return self.save_as()

        logger.info(f"Saving to: {self.path}.")

        try:
            with open(self.path, "w") as f:
                f.write(self.edit.document().toPlainText())

            self.issaved = True
            self.savestatechanged.emit(self.issaved)
            return True
        except OSError:
            logger.info(f"Could not saved file {self.path}")
            return False

    def save_as(self):
        """Save file under a new name."""
        path, cd = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", state.working_directory.Value)

        if (os.path.exists(path) or os.access(os.path.dirname(path), os.W_OK)):
            self.path = path
            self.save()
            self.pathchanged.emit(self.path)
            return True
        else:
            logger.info(f"Attempted to save file but {path} is not a valid path")
            return False

    def tryclose(self):
        """Try closing the page. Succeeds if file is or can be saved or is discarded, fails otherwise."""
        if not self.issaved:
            if self.path:
                name = os.path.basename(self.path)
            else:
                name = "*new*"

            box = QtWidgets.QMessageBox()
            box.setWindowTitle("Closing Document")
            box.setText(f"The document '{name}' has been modified.\nShould the changes be saved or discarded?")
            box.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            box.setDefaultButton(QtWidgets.QMessageBox.Save)

            ans = box.exec()

            if ans == QtWidgets.QMessageBox.Save:
                return self.save()
            elif ans == QtWidgets.QMessageBox.Discard:
                return True
            elif ans == QtWidgets.QMessageBox.Cancel:
                return False

        return True

    def modified(self):
        """Set status to unsaved."""
        self.issaved = False
        self.savestatechanged.emit(self.issaved)

    def show_error(self, msg):
        """Show an error page."""
        self.edit.deleteLater()

        self.gridLayout = QtWidgets.QGridLayout()

        self.label_w = QtWidgets.QLabel()
        self.label_w.setPixmap(QtGui.QPixmap("icons/warning.svg"))
        self.label_t = QtWidgets.QLabel("<h1>" + msg + "</h1>")

        self.gridLayout.addWidget(self.label_w, 0, 1)
        self.gridLayout.addWidget(self.label_t, 0, 2)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 0)
        self.gridLayout.setColumnStretch(2, 0)
        self.gridLayout.setColumnStretch(3, 1)

        self.verticalLayout.addLayout(self.gridLayout)


class WelcomePage(QtWidgets.QFrame):
    """Welcome Page."""

    open_file = QtCore.Signal(str)

    def __init__(self, recent_files=[]):
        """Populate welcome page."""
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)

        self.path = None

        self.gridLayout = QtWidgets.QGridLayout(self)

        self.label = QtWidgets.QLabel("<h1>Recently opened files</h1>")
        self.button_NewFile = QtWidgets.QPushButton("New File")
        self.button_OpenFile = QtWidgets.QPushButton("Open File")
        self.button_OpenFolder = QtWidgets.QPushButton("Open Workspace")

        self.recentFilesModel = util.RecentFilesModel(recent_files)

        self.listView = QtWidgets.QListView()
        self.listView.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
        self.listView.setModel(self.recentFilesModel)

        self.recentFilesModel.layoutChanged.emit()

        self.gridLayout.addWidget(self.label, 1, 1, 1, 2, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.gridLayout.addWidget(self.listView, 2, 1, 1, 2)
        self.gridLayout.addWidget(self.button_NewFile, 3, 1)
        self.gridLayout.addWidget(self.button_OpenFile, 3, 2)

        self.gridLayout.setRowStretch(0, 2)
        self.gridLayout.setRowStretch(1, 1)
        self.gridLayout.setRowStretch(2, 8)
        self.gridLayout.setRowStretch(3, 1)
        self.gridLayout.setRowStretch(4, 2)

        self.gridLayout.setColumnStretch(0, 2)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)
        self.gridLayout.setColumnStretch(3, 2)

        self.listView.doubleClicked.connect(self.doubleclicked)

    def update_recent_files(self, recent_files):
        """Update the recent files list."""
        self.recentFilesModel.recent_files = recent_files
        self.recentFilesModel.layoutChanged.emit()

    def doubleclicked(self, index):
        """Handle doubleclick on listView item."""
        path = self.recentFilesModel.data(index, QtCore.Qt.DisplayRole)
        if os.path.isfile(path):
            self.open_file.emit(path)

    def tryclose(self):
        """Close page."""
        return True

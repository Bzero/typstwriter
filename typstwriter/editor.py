from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import os
import collections

from typstwriter import util
from typstwriter import enums
from typstwriter import syntax_highlighting

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate

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

        self.TabWidget.tabBar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.TabWidget.tabBar().customContextMenuRequested.connect(self.tab_bar_rightclicked)

        self.recentFiles = util.RecentFiles()

        self.font_size = config.get("Editor", "font_size", typ="int")

        self.welcome()

    def tab_bar_rightclicked(self, event):
        """Handle right click on the tab bar."""
        tab_index = self.TabWidget.tabBar().tabAt(event)
        tab = self.TabWidget.widget(tab_index)
        if isinstance(tab, EditorPage):
            cm = EditorPageBarContextMenu(self, tab_index)
            cm.popup(QtGui.QCursor.pos())
        elif isinstance(tab, WelcomePage):
            cm = WelcomePageBarContextMenu(self, tab_index)
            cm.popup(QtGui.QCursor.pos())

    def new_file(self):
        """Open a new, empty file."""
        editorpage = EditorPage(font_size=self.font_size)
        name = "*new*"
        icon = QtGui.QIcon.fromTheme(QtGui.QIcon.DocumentNew, QtGui.QIcon(util.icon_path("newFile.svg")))
        self.TabWidget.addTab(editorpage, icon, name)
        self.TabWidget.setCurrentIndex(self.TabWidget.count() - 1)
        self.TabWidget.tabBar().setTabTextColor(self.TabWidget.count() - 1, QtGui.QColor("green"))

        editorpage.edit.textChanged.connect(self.childtext_changed)
        editorpage.savestatechanged.connect(self.childsavedstate_changed)
        editorpage.pathchanged.connect(self.childpath_changed)

    def open_file(self, path):
        """Open an existing file or switch to it if it is already open."""
        if path not in self.openfiles_list():
            editorpage = EditorPage(path, self.font_size)
            name = os.path.relpath(path, start=state.working_directory.Value)
            icon = util.FileIconProvider().icon(QtCore.QFileInfo(path))
            self.TabWidget.addTab(editorpage, icon, name)
            self.TabWidget.setCurrentIndex(self.TabWidget.count() - 1)
            self.TabWidget.tabBar().setTabTextColor(self.TabWidget.count() - 1, QtGui.QColor("black"))

            editorpage.edit.textChanged.connect(self.childtext_changed)
            editorpage.savestatechanged.connect(self.childsavedstate_changed)
            editorpage.pathchanged.connect(self.childpath_changed)

            if editorpage.isloaded is True:
                self.recentFiles.append(path)
                self.recent_files_changed.emit(self.recentFiles.list())
        else:
            index = self.openfiles_list().index(path)
            self.TabWidget.setCurrentIndex(index)

    def open_file_dialog(self):
        """Open a dialog to open an existing file."""
        filters = "Typst Files (*.typ);;Any File (*)"
        path, cd = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", state.working_directory.Value, filters)
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
        self.TabWidget.setCurrentIndex(self.TabWidget.count() - 1)
        self.TabWidget.tabBar().setTabTextColor(self.TabWidget.count() - 1, QtGui.QColor("blue"))
        welcomepage.button_NewFile.pressed.connect(self.new_file)
        welcomepage.button_OpenFile.pressed.connect(self.open_file_dialog)
        welcomepage.open_file.connect(self.open_file)
        self.recent_files_changed.connect(welcomepage.update_recent_files)

    def tabs_list(self):
        """Return (ordered) list of open tabs."""
        return [self.TabWidget.widget(i) for i in range(0, self.TabWidget.count())]

    def openfiles_list(self):
        """Return (ordered) list of opened files."""
        return [t.path for t in self.tabs_list() if t.path]

    def tryclose(self):
        """Try closing the editor, i.e. close all tabs and save the recent files."""
        for t in self.tabs_list():
            s = t.tryclose()
            if not s:
                return False
        self.recentFiles.write()
        return True

    @QtCore.Slot()
    def save_all(self):
        """Save all tabs."""
        for t in self.tabs_list():
            if isinstance(t, EditorPage):
                t.save()

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
    def search(self):
        """Open the search bar of the active tab."""
        page = self.TabWidget.currentWidget()
        if isinstance(page, EditorPage):
            page.search_bar.show()
            # page.search_bar.edit_search.setFocus()

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
        """Update tab name and icon based on new path."""
        i = self.TabWidget.indexOf(self.sender())
        name = os.path.relpath(path, start=state.working_directory.Value)
        icon = util.FileIconProvider().icon(QtCore.QFileInfo(path))
        self.TabWidget.tabBar().setTabText(i, name)
        self.TabWidget.tabBar().setTabIcon(i, icon)

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

    @QtCore.Slot(collections.defaultdict)
    def apply_errors(self, errors):
        """Apply all compiler errors."""
        for t in self.tabs_list():
            if t.path in errors:
                t.edit.highlight_errors(errors[t.path])

    @QtCore.Slot()
    def clear_errors(self):
        """Clear all compiler errors."""
        for t in self.tabs_list():
            if isinstance(t, EditorPage):
                t.edit.clear_errors()

    @QtCore.Slot()
    def increase_font_size(self):
        """Increase the font size."""
        self.font_size = min(40, self.font_size * 1.25)
        self.set_font_size()

    @QtCore.Slot()
    def decrease_font_size(self):
        """Decrease the font size."""
        self.font_size = max(4, self.font_size * 0.8)
        self.set_font_size()

    @QtCore.Slot()
    def reset_font_size(self):
        """Reset the font size to the config default."""
        self.font_size = config.get("Editor", "font_size", typ="int")
        self.set_font_size()

    def set_font_size(self):
        """Apply font size to all editor tabs."""
        for t in self.tabs_list():
            if isinstance(t, EditorPage):
                t.edit.set_font_size(self.font_size)


class EditorPageBarContextMenu(QtWidgets.QMenu):
    """ContextMenu for EditorPage tabbar."""

    def __init__(self, parent, tab_index):
        """Declare all actions."""
        QtWidgets.QMenu.__init__(self, parent)

        self.tab_index = tab_index

        self.action_close = QtWidgets.QAction("Close file", triggered=self.handle_close)
        self.action_use_as_main = QtWidgets.QAction("Use as main file", triggered=self.handle_use_as_main)
        self.action_use_as_working_directory = QtWidgets.QAction(
            "Use containing folder as working directory", triggered=self.handle_use_as_working_directory
        )

        self.addAction(self.action_close)
        self.addAction(self.action_use_as_main)
        self.addAction(self.action_use_as_working_directory)

    def handle_close(self):
        """Trigger closing the tab."""
        self.parent().close_tab(self.tab_index)

    def handle_use_as_main(self):
        """Trigger using this file as main file."""
        state.main_file.Value = self.parent().TabWidget.widget(self.tab_index).path

    def handle_use_as_working_directory(self):
        """Trigger using the folder containing this file as working directory."""
        state.working_directory.Value = os.path.dirname(self.parent().TabWidget.widget(self.tab_index).path)


class WelcomePageBarContextMenu(QtWidgets.QMenu):
    """ContextMenu for WelcomePage tabbar."""

    def __init__(self, parent, tab_index):
        """Declare all actions."""
        QtWidgets.QMenu.__init__(self, parent)

        self.tab_index = tab_index

        self.action_close = QtWidgets.QAction("Close Tab", triggered=self.handle_close)
        self.addAction(self.action_close)

    def handle_close(self):
        """Trigger closing the tab."""
        self.parent().close_tab(self.tab_index)


class EditorPage(QtWidgets.QFrame):
    """A single editor page."""

    savestatechanged = QtCore.Signal(bool)
    pathchanged = QtCore.Signal(str)

    def __init__(self, path=None, font_size=None):
        """Set up and load file if path is given."""
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)

        syntax_conf = config.get("Editor", "highlight_syntax", "bool")
        line_numbers_conf = config.get("Editor", "show_line_numbers", "bool")
        line_conf = config.get("Editor", "highlight_line", "bool")
        use_spaces = config.get("Editor", "use_spaces", "bool")
        syntax = syntax_highlighting.get_lexer_name_by_filename(path)

        self.edit = CodeEdit(
            font_size=font_size,
            highlight_synatx=syntax_conf,
            show_line_numbers=line_numbers_conf,
            highlight_line=line_conf,
            use_spaces=use_spaces,
            syntax=syntax,
        )
        self.edit.textChanged.connect(self.modified)
        self.verticalLayout.addWidget(self.edit)

        self.search_bar = SearchBar(self)
        self.verticalLayout.addWidget(self.search_bar)
        self.search_bar.hide()

        self.status_bar = EditorStatusBar(self)
        self.status_bar.syntax_combo_box.setCurrentText(syntax if syntax and syntax_conf else "Text only")
        self.verticalLayout.addWidget(self.status_bar)

        self.file_changed_warning = None

        self.filesystemwatcher = QtCore.QFileSystemWatcher()
        self.filesystemwatcher.fileChanged.connect(self.show_file_changed_warning)

        self.status_bar.syntax_changed.connect(self.edit.set_syntax)

        self.path = path
        self.issaved = True
        self.isloaded = False
        self.changed_on_disk = False
        self.justsaved = False
        self.any_match_found = False
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
            self.isloaded = True
            self.changed_on_disk = False

            if self.filesystemwatcher.files():
                self.filesystemwatcher.removePaths(self.filesystemwatcher.files())
            self.filesystemwatcher.addPath(path)

            self.savestatechanged.emit(self.issaved)

        except UnicodeError:
            msg = f"{path!r} is not a text file."
            logger.warning(msg)
            self.show_error(msg)
            self.isloaded = False

        except OSError:
            msg = f"{path!r} is not a valid file."
            logger.warning(msg)
            self.show_error(msg)
            self.isloaded = False

    def write(self):
        """Write file to disk."""
        logger.debug("Saving to: {!r}.", self.path)

        try:
            with open(self.path, "w") as f:
                f.write(self.edit.document().toPlainText())

            self.justsaved = True
            self.issaved = True
            self.changed_on_disk = False
            self.savestatechanged.emit(self.issaved)

            return True
        except OSError:
            logger.info("Could not saved file {!r}", self.path)
            return False

    def save(self):
        """Save file."""
        if not self.path:
            return self.save_as()

        if self.changed_on_disk:
            ans = QtWidgets.QMessageBox.question(
                self,
                "Typstwriter",
                f"File '{self.path}' was changed on disk.\nDo you really want to save this file and overwrite the one on disk?",
            )
            if ans == QtWidgets.QMessageBox.StandardButton.No:
                return False

        self.write()
        return True

    def save_as(self):
        """Save file under a new name."""
        path, cd = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", state.working_directory.Value)

        if os.path.exists(path) or os.access(os.path.dirname(path), os.W_OK):
            self.path = path
            self.filesystemwatcher.removePaths(self.filesystemwatcher.files())
            self.filesystemwatcher.addPath(path)
            self.pathchanged.emit(self.path)

            self.write()
            return True
        else:
            logger.info("Attempted to save file but {!r} is not a valid path", path)
            return False

    def tryclose(self):
        """Try closing the page. Succeeds if file is or can be saved or is discarded, fails otherwise."""
        if not self.issaved:
            name = os.path.basename(self.path) if self.path else "*new*"

            box = QtWidgets.QMessageBox()
            box.setWindowTitle("Closing Document")
            box.setText(f"The document '{name}' has been modified.\nShould the changes be saved or discarded?")
            box.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            box.setDefaultButton(QtWidgets.QMessageBox.Save)

            match box.exec():
                case QtWidgets.QMessageBox.Save:
                    return self.save()
                case QtWidgets.QMessageBox.Discard:
                    return True
                case QtWidgets.QMessageBox.Cancel:
                    return False

        return True

    def modified(self):
        """Set status to unsaved."""
        self.issaved = False
        self.savestatechanged.emit(self.issaved)

    @QtCore.Slot(str)
    def show_file_changed_warning(self, path):
        """Show the file changed warning."""
        # Abort if the file was just saved before
        if self.justsaved:
            self.justsaved = False
            return

        self.changed_on_disk = True
        if not self.file_changed_warning:
            self.file_changed_warning = FileChangedWarning(path)
            self.verticalLayout.insertWidget(0, self.file_changed_warning)
            self.file_changed_warning.button_reload.pressed.connect(self.file_changed_reload)
            self.file_changed_warning.button_ignore.pressed.connect(self.remove_file_changed_warning)

    @QtCore.Slot()
    def file_changed_reload(self):
        """Reload the canged file from disk."""
        self.load(self.path)
        self.remove_file_changed_warning()

    @QtCore.Slot()
    def remove_file_changed_warning(self):
        """Remove the file changed warning."""
        self.verticalLayout.removeWidget(self.file_changed_warning)
        self.file_changed_warning.deleteLater()
        self.file_changed_warning = None

    def show_error(self, msg):
        """Show an error page."""
        self.edit.hide()

        self.HLayout = QtWidgets.QHBoxLayout()
        self.verticalLayout.insertLayout(1, self.HLayout)

        self.label_w = QtWidgets.QLabel()
        if QtGui.QIcon.hasThemeIcon("data-warning"):
            self.label_w.setPixmap(QtGui.QIcon.fromTheme("data-warning").pixmap(64))
        else:
            self.label_w.setPixmap(QtGui.QPixmap(util.icon_path("warning.svg")))

        self.label_t = QtWidgets.QLabel(msg)
        font = self.label_t.font()
        font.setPointSize(font.pointSize() * 2)
        font.setBold(True)
        self.label_t.setFont(font)
        self.label_t.setWordWrap(True)

        self.HLayout.addStretch()
        self.HLayout.addWidget(self.label_w, alignment=QtCore.Qt.AlignmentFlag.AlignRight)
        self.HLayout.addWidget(self.label_t, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        self.HLayout.addStretch()


class FileChangedWarning(QtWidgets.QFrame):
    """Show a warning that the opened file changed on disk."""

    def __init__(self, path):
        """Init."""
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Shape.Box)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self)

        self.label_icon = QtWidgets.QLabel()
        if QtGui.QIcon.hasThemeIcon(QtGui.QIcon.DialogWarning):
            self.label_icon.setPixmap(QtGui.QIcon.fromTheme(QtGui.QIcon.DialogWarning).pixmap(self.fontMetrics().height() * 2))
        else:
            self.label_icon.setPixmap(
                QtGui.QPixmap(util.icon_path("warning.svg")).scaledToHeight(self.fontMetrics().height() * 2)
            )
        self.horizontalLayout.addWidget(self.label_icon)

        self.label_text = QtWidgets.QLabel()
        self.label_text.setText(f"The file '{path!r}' has been changed on disk.")
        self.label_text.setWordWrap(True)
        self.horizontalLayout.addWidget(self.label_text)

        icon = QtGui.QIcon.fromTheme(QtGui.QIcon.ViewRefresh, QtGui.QIcon(util.icon_path("reload.svg")))
        self.button_reload = QtWidgets.QPushButton(icon, "Reload")
        self.horizontalLayout.addWidget(self.button_reload)

        icon = QtGui.QIcon.fromTheme("dialog-cancel", QtGui.QIcon(util.icon_path("ignore.svg")))
        self.button_ignore = QtWidgets.QPushButton(icon, "Ignore")
        self.horizontalLayout.addWidget(self.button_ignore)

        self.horizontalLayout.setStretch(1, 1)


class SearchBar(QtWidgets.QWidget):
    """A search and replace bar."""

    def __init__(self, parent, path=None):
        """Set up and load file if path is given."""
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.Layout = QtWidgets.QGridLayout(self)
        self.Layout.setContentsMargins(4, 4, 0, 4)

        self.label_search = QtWidgets.QLabel("Search: ")
        self.edit_search = QtWidgets.QLineEdit()

        self.label_replace = QtWidgets.QLabel("Replace: ")
        self.edit_replace = QtWidgets.QLineEdit()

        self.label_mode = QtWidgets.QLabel("Mode: ")
        self.combo_box_mode = QtWidgets.QComboBox()
        self.combo_box_mode.addItem("Case Insensitive", enums.search_mode.case_insensitive)
        self.combo_box_mode.addItem("Case Sensitive", enums.search_mode.case_sensitive)
        self.combo_box_mode.addItem("Whole Words", enums.search_mode.whole_words)
        self.combo_box_mode.addItem("Regular Expression", enums.search_mode.regex)

        self.button_replace_current = QtWidgets.QPushButton("Replace Current")
        self.button_replace_all = QtWidgets.QPushButton("Replace All")

        self.button_close = QtWidgets.QToolButton()
        self.button_close.setText("Close")
        self.button_close.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.WindowClose, QtGui.QIcon(util.icon_path("close.svg"))))

        self.button_prev = QtWidgets.QToolButton()
        self.button_prev.setText("Previous Match")
        self.button_prev.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.GoUp, QtGui.QIcon(util.icon_path("uarrow.svg"))))
        self.button_next = QtWidgets.QToolButton()
        self.button_next.setText("Next Match")
        self.button_next.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.GoDown, QtGui.QIcon(util.icon_path("darrow.svg"))))

        self.Layout.addWidget(self.label_search, 0, 0, 1, 1)
        self.Layout.addWidget(self.edit_search, 0, 1, 1, 4)
        self.Layout.addWidget(self.label_replace, 1, 0, 1, 1)
        self.Layout.addWidget(self.edit_replace, 1, 1, 1, 4)
        self.Layout.addWidget(self.label_mode, 2, 0, 1, 1)
        self.Layout.addWidget(self.combo_box_mode, 2, 1, 1, 1)
        self.Layout.setColumnStretch(2, 1)
        self.Layout.addWidget(self.button_replace_current, 2, 3, 1, 1)
        self.Layout.addWidget(self.button_replace_all, 2, 4, 1, 1)
        self.Layout.addWidget(self.button_prev, 0, 5, 1, 1)
        self.Layout.addWidget(self.button_next, 1, 5, 1, 1)
        self.Layout.addWidget(self.button_close, 2, 5, 1, 1)

        self.edit_search.textChanged.connect(self.find_all)
        self.edit_search.returnPressed.connect(self.next_match)
        self.combo_box_mode.currentIndexChanged.connect(self.find_all)
        self.button_next.pressed.connect(self.next_match)
        self.button_prev.pressed.connect(self.prev_match)
        self.edit_replace.returnPressed.connect(self.replace_current)
        self.button_replace_current.pressed.connect(self.replace_current)
        self.button_replace_all.pressed.connect(self.replace_all)
        self.button_close.pressed.connect(self.hide)
        self.parent().edit.textChanged.connect(self.find_all_if_visible)

    def show(self):
        """Show the search bar."""
        super().show()
        self.edit_search.setFocus()
        self.find_all()

    def hide(self):
        """Hide the search bar."""
        super().hide()
        self.parent().edit.clear_search_highlights()

    def find_all(self):
        """Find and highlight all occurencies of the query."""
        if not self.isVisible():
            return

        self.parent().edit.highlight_all_matches(self.edit_search.text(), self.combo_box_mode.currentData())

        palette = self.edit_search.palette()
        if self.parent().edit.any_match_found:
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#90ee90"))
        else:
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#ee9090"))
        if not self.edit_search.text():
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#ffffff"))
        self.edit_search.setPalette(palette)

    def find_all_if_visible(self):
        """Find all if search bar is visible."""
        if self.isVisible():
            self.find_all()

    def next_match(self):
        """Go to the next match."""
        self.parent().edit.jump_to_match(
            self.edit_search.text(), self.combo_box_mode.currentData(), enums.search_direction.next
        )

    def prev_match(self):
        """Go to the previous match."""
        self.parent().edit.jump_to_match(
            self.edit_search.text(), self.combo_box_mode.currentData(), enums.search_direction.previous
        )

    def replace_current(self):
        """Replace the currently selected match."""
        self.parent().edit.replace_current_match(
            self.edit_search.text(), self.combo_box_mode.currentData(), self.edit_replace.text()
        )

    def replace_all(self):
        """Replace all matches."""
        self.parent().edit.replace_all_matches(
            self.edit_search.text(), self.combo_box_mode.currentData(), self.edit_replace.text()
        )


class EditorStatusBar(QtWidgets.QWidget):
    """A status bar for the editor."""

    syntax_changed = QtCore.Signal(str)

    def __init__(self, parent):
        """Set up."""
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)

        self.Layout = QtWidgets.QHBoxLayout(self)
        self.Layout.setContentsMargins(4, 4, 0, 0)

        self.syntax_combo_box = QtWidgets.QComboBox()
        for name in sorted(syntax_highlighting.available_lexers(), key=str.lower):
            self.syntax_combo_box.addItem(name)
        self.syntax_combo_box.textActivated.connect(lambda text: self.syntax_changed.emit(text))

        self.Layout.addStretch()
        self.Layout.addWidget(self.syntax_combo_box)


class WelcomePage(QtWidgets.QFrame):
    """Welcome Page."""

    open_file = QtCore.Signal(str)

    def __init__(self, recent_files=None):
        """Populate welcome page."""
        QtWidgets.QFrame.__init__(self)
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)

        self.path = None

        self.gridLayout = QtWidgets.QGridLayout(self)

        self.label = QtWidgets.QLabel("<h1>Recently opened files</h1>")
        self.button_NewFile = QtWidgets.QPushButton("New File")
        self.button_OpenFile = QtWidgets.QPushButton("Open File")
        self.button_OpenFolder = QtWidgets.QPushButton("Open Workspace")

        self.recentFilesModel = util.RecentFilesModel(recent_files or [])

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


class CodeEdit(QtWidgets.QPlainTextEdit):
    """A code editor widget."""

    def __init__(
        self, font_size=None, highlight_synatx=True, show_line_numbers=True, highlight_line=True, use_spaces=True, syntax=None
    ):
        """Init and set options."""
        super().__init__()

        highlight_style = config.get("Editor", "highlighter_style")
        lexer = syntax_highlighting.get_lexer_by_name(syntax if highlight_synatx else None)
        self.highlighter = syntax_highlighting.CodeSyntaxHighlight(self.document(), lexer, highlight_style)
        palette = self.palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(self.highlighter.background_color))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(self.highlighter.font_color))
        self.setPalette(palette)

        self.line_highlight = []
        self.error_highlight = []
        self.search_highlights = []

        if font_size:
            self.set_font_size(font_size)

        if show_line_numbers:
            self.line_numbers = LineNumberWidget(self)
            self.blockCountChanged.connect(self.line_numbers.update_width)
            self.updateRequest.connect(self.line_numbers.update_requested)
            self.line_numbers.update_width()
        else:
            self.line_numbers = None

        if highlight_line:
            self.cursorPositionChanged.connect(self.highlight_current_line)
            self.highlight_current_line()

        self.use_spaces = use_spaces

    def resizeEvent(self, *e):  # This is an overriding function # noqa: N802
        """Resize."""
        super().resizeEvent(*e)

        if self.line_numbers:
            cr = self.contentsRect()
            width = self.line_numbers.width()
            rect = QtCore.QRect(cr.left(), cr.top(), width, cr.height())
            self.line_numbers.setGeometry(rect)

    def keyPressEvent(self, e):  # This is an overriding function # noqa: N802
        """Intercept, modify and forward keyPressEvent."""
        # Indent if Tab pressed
        if e.key() == QtCore.Qt.Key_Tab and e.modifiers() == QtCore.Qt.NoModifier:
            if self.textCursor().hasSelection():
                self.indent()
            elif self.use_spaces:
                self._insert_tab(self.textCursor())
            return

        # Unindent if Shift+Tab pressed
        if e.key() == QtCore.Qt.Key_Backtab and e.modifiers() == QtCore.Qt.ShiftModifier:
            if self.textCursor().hasSelection():
                self.unindent()
            else:
                self._remove_tab_l(self.textCursor())
            return

        # Toggle comments if Ctrl+/ pressed
        if e.key() == QtCore.Qt.Key_Slash and e.modifiers() == QtCore.Qt.ControlModifier:
            self.toggle_comment()
            return

        # Avoid inserting line break characters
        if e.key() == QtCore.Qt.Key_Return and e.modifiers() == QtCore.Qt.ShiftModifier:
            e = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Return, QtCore.Qt.NoModifier, "\r")

        super().keyPressEvent(e)

    def set_font_size(self, font_size):
        """Set the font size."""
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

    def set_syntax(self, name):
        """Set the syntax for syntax highlighting."""
        with QtCore.QSignalBlocker(self):
            highlight_style = config.get("Editor", "highlighter_style")
            lexer = syntax_highlighting.get_lexer_by_name(name)
            self.highlighter = syntax_highlighting.CodeSyntaxHighlight(self.document(), lexer, highlight_style)
            self.highlighter.rehighlight()

    def apply_extra_selections(self):
        """Apply line, error and search highlight extra selections."""
        self.setExtraSelections(self.line_highlight + self.error_highlight + self.search_highlights)

    @QtCore.Slot()
    def highlight_current_line(self):
        """Highlight the current line, unless some text is selected."""
        if not self.textCursor().hasSelection():
            highlight = QtWidgets.QTextEdit.ExtraSelection()
            highlight.format.setBackground(QtGui.QColor(self.highlighter.highlight_color))
            highlight.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            highlight.cursor = self.textCursor()
            self.line_highlight = [highlight]
        else:
            self.line_highlight = []

        self.apply_extra_selections()

    @QtCore.Slot()
    def highlight_errors(self, errors):
        """Highlight compiler errors."""
        highlights = []
        for e in errors:
            (error, line, col, length) = e
            # the error code is not currently used but it may be displayed in the editor in the future

            cursor = QtGui.QTextCursor(self.document())
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.NextBlock, QtGui.QTextCursor.MoveMode.MoveAnchor, line - 1)
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right, QtGui.QTextCursor.MoveMode.MoveAnchor, col)
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right, QtGui.QTextCursor.MoveMode.KeepAnchor, length)

            mark_line = QtWidgets.QTextEdit.ExtraSelection()
            mark_line.format.setBackground(QtGui.QColor("#ffeeee"))
            mark_line.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            mark_line.cursor = cursor
            mark_line.cursor.clearSelection()
            highlights.append(mark_line)

            mark_span = QtWidgets.QTextEdit.ExtraSelection()
            mark_span.format.setUnderlineStyle(QtGui.QTextCharFormat.DashUnderline)
            mark_span.format.setUnderlineColor("#cc1b1b")
            mark_span.cursor = cursor
            highlights.append(mark_span)

        self.error_highlight = highlights
        self.apply_extra_selections()

    def clear_errors(self):
        """Clear all error highlights."""
        if self.error_highlight:
            self.error_highlight = []
            self.apply_extra_selections()

    def _insert_tab(self, cursor):
        """Insert a tab (or four spaces) right of the cursor."""
        tab = "    " if self.use_spaces else "\t"
        cursor.insertText(tab)

    def _remove_tab_r(self, cursor):
        """Remove a tab or up to four spaces right of the cursor."""
        ntext = cursor.block().text()[cursor.positionInBlock() :: 1]
        if ntext.startswith("\t"):
            cursor.deleteChar()
        else:
            for c in ntext[0:4]:
                if c != " ":
                    break
                cursor.deleteChar()

    def _remove_tab_l(self, cursor):
        """Remove a tab or up to four spaces left of the cursor."""
        ntext = cursor.block().text()[cursor.positionInBlock() - 1 :: -1]
        if ntext.startswith("\t"):
            cursor.deletePreviousChar()
        else:
            for c in ntext[0:4]:
                if c != " ":
                    break
                cursor.deletePreviousChar()

    def indent(self):
        """Indent the selected lines."""
        cursor = self.textCursor()
        cursor.setPosition(self.textCursor().selectionStart())
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)

        cursor.beginEditBlock()
        for _ in range(util.selection_end_block(self.textCursor()) - util.selection_start_block(self.textCursor()) + 1):
            if cursor.block().text():
                self._insert_tab(cursor)
            cursor.movePosition(QtGui.QTextCursor.NextBlock)
        cursor.endEditBlock()

    def unindent(self):
        """Unindent the selected lines."""
        cursor = self.textCursor()
        cursor.setPosition(self.textCursor().selectionStart())
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)

        cursor.beginEditBlock()
        for _ in range(util.selection_end_block(self.textCursor()) - util.selection_start_block(self.textCursor()) + 1):
            self._remove_tab_r(cursor)
            cursor.movePosition(QtGui.QTextCursor.NextBlock)
        cursor.endEditBlock()

    def toggle_comment(self):
        """Toggle comment of the selected lines."""
        cursor = self.textCursor()
        cursor.setPosition(self.textCursor().selectionStart())
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)

        all_lines_commented = True
        for _ in range(util.selection_end_block(self.textCursor()) - util.selection_start_block(self.textCursor()) + 1):
            if not cursor.block().text().strip().startswith("//"):
                all_lines_commented = False
                break
            cursor.movePosition(QtGui.QTextCursor.NextBlock)

        if not all_lines_commented:
            self.comment()
        else:
            self.uncomment()

    def comment(self):
        """Comment the selected lines."""
        cursor = self.textCursor()
        cursor.setPosition(self.textCursor().selectionStart())
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)

        cursor.beginEditBlock()
        for _ in range(util.selection_end_block(self.textCursor()) - util.selection_start_block(self.textCursor()) + 1):
            cursor.insertText("//")
            cursor.movePosition(QtGui.QTextCursor.NextBlock)
        cursor.endEditBlock()

    def uncomment(self):
        """Uncomment the selected lines."""
        cursor = self.textCursor()
        cursor.setPosition(self.textCursor().selectionStart())
        cursor.movePosition(QtGui.QTextCursor.StartOfBlock)

        cursor.beginEditBlock()
        for _ in range(util.selection_end_block(self.textCursor()) - util.selection_start_block(self.textCursor()) + 1):
            line = cursor.block().text()
            if line.lstrip().startswith("//"):
                indent = len(line) - len(line.lstrip())
                cursor.movePosition(QtGui.QTextCursor.Right, n=indent)
                cursor.deleteChar()
                cursor.deleteChar()
            cursor.movePosition(QtGui.QTextCursor.NextBlock)
        cursor.endEditBlock()

    def _find(self, query, mode, cursor, direction=enums.search_direction.next):
        """Find the next/previous match from the provided cursor in the current document."""
        doc = self.document()

        match mode:
            case enums.search_mode.case_insensitive:
                options = QtGui.QTextDocument.FindFlags()
            case enums.search_mode.case_sensitive:
                options = QtGui.QTextDocument.FindFlag.FindCaseSensitively
            case enums.search_mode.whole_words:
                options = QtGui.QTextDocument.FindFlag.FindCaseSensitively | QtGui.QTextDocument.FindFlag.FindWholeWords
            case enums.search_mode.regex:
                query = QtCore.QRegularExpression(query)
                options = QtGui.QTextDocument.FindFlag.FindCaseSensitively
                if not query.isValid():
                    return QtGui.QTextCursor()

        if direction is enums.search_direction.previous:
            options = options | QtGui.QTextDocument.FindFlag.FindBackward

        return doc.find(query, cursor, options=options)

    def highlight_all_matches(self, query, mode):
        """Highlight all matches of the search query."""
        highlights = []

        cursor = QtGui.QTextCursor(self.document())

        while not cursor.isNull() and not cursor.atEnd():
            cursor = self._find(query, mode, cursor)

            if not cursor.isNull():
                if not cursor.hasSelection():
                    cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right)
                    continue

                highlight = QtWidgets.QTextEdit.ExtraSelection()
                highlight.cursor = cursor
                highlight.format.setBackground(QtGui.QColor(self.highlighter.highlight_color).darker(120))
                highlights.append(highlight)

        self.search_highlights = highlights
        self.any_match_found = bool(highlights)

        self.apply_extra_selections()

    def clear_search_highlights(self):
        """Clear all search highlights."""
        self.search_highlights = []
        self.any_match_found = False
        self.apply_extra_selections()

    def jump_to_match(self, query, mode, direction=enums.search_direction.next):
        """Jump to the next/previous match of the search query."""
        self.highlight_all_matches(query, mode)
        if self.any_match_found:
            cur = self._find(query, mode, self.textCursor(), direction)
            if cur.isNull():  # Cursor is at the start or end of the document: wrap around
                cur = QtGui.QTextCursor(self.document())
                if direction is enums.search_direction.next:
                    cur.movePosition(QtGui.QTextCursor.MoveOperation.Start)
                else:
                    cur.movePosition(QtGui.QTextCursor.MoveOperation.End)
                cur = self._find(query, mode, cur, direction)

            self.setTextCursor(cur)

    def replace_all_matches(self, query, mode, replace_text):
        """Replace all matches of the search query."""
        cur = self.textCursor()
        cur.beginEditBlock()

        cursor = QtGui.QTextCursor(self.document())
        while not cursor.isNull():
            cursor = self._find(query, mode, cursor)
            if not cursor.isNull():
                cursor.removeSelectedText()
                cursor.insertText(replace_text)

        cur.endEditBlock()

        self.highlight_all_matches(query, mode)

    def replace_current_match(self, query, mode, replace_text):
        """Replace current match of the search query."""
        c = self.textCursor()
        c.setPosition(c.anchor(), QtGui.QTextCursor.MoveMode.MoveAnchor)

        cursor = self._find(query, mode, c)

        if cursor == self.textCursor():
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(replace_text)
            cursor.endEditBlock()

        self.highlight_all_matches(query, mode)
        self.jump_to_match(query, mode, direction=enums.search_direction.next)


class LineNumberWidget(QtWidgets.QWidget):
    """A widget supposed to be attached to a QPlainTextEdit showing line numbers."""

    left_spacing = 10
    right_spacing = 10

    def __init__(self, parent):
        """Init."""
        QtWidgets.QWidget.__init__(self, parent)

    def paintEvent(self, event):  # This is an overriding function # noqa: N802
        """Paint the widget."""
        painter = QtGui.QPainter(self)

        # paint background
        painter.fillRect(event.rect(), QtGui.QColor(self.parentWidget().highlighter.line_number_background_color))

        # paint line numbers
        painter.setPen(QtGui.QColor(self.parentWidget().highlighter.line_number_color))
        block = self.parentWidget().firstVisibleBlock()

        while block and block.isValid():
            offset = self.parentWidget().contentOffset()
            y = int(self.parentWidget().blockBoundingGeometry(block).translated(offset).top())
            line_number = str(block.blockNumber() + 1)
            text_width = self.width() - self.right_spacing
            text_height = self.fontMetrics().height()
            painter.drawText(0, y, text_width, text_height, QtCore.Qt.AlignRight, line_number)

            if y <= event.rect().bottom():  # noqa: SIM108
                block = block.next()
            else:
                block = None

        painter.end()

    @QtCore.Slot(QtCore.QRect, int)
    def update_requested(self, rect, dy):
        """Update."""
        if dy:
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

    @QtCore.Slot()
    def update_width(self):
        """Update the Line Number Widget to take the width required to display all digits."""
        text_width = self.fontMetrics().horizontalAdvance(str(self.parentWidget().blockCount()))
        width = self.left_spacing + text_width + self.right_spacing
        self.setFixedWidth(width)
        self.parentWidget().setViewportMargins(width, 0, 0, 0)

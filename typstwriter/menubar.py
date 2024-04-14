from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class MenuBar(QtWidgets.QMenuBar):
    """Main Window Menu Bar."""

    def __init__(self, actions):
        """Populate menu bar."""
        QtWidgets.QMenuBar.__init__(self)

        self.menuFile = QtWidgets.QMenu(self)
        self.menuEdit = QtWidgets.QMenu(self)
        self.menuView = QtWidgets.QMenu(self)
        self.menuSettings = QtWidgets.QMenu(self)

        self.menuFile.setTitle("File")
        self.menuEdit.setTitle("Edit")
        self.menuView.setTitle("View")
        self.menuSettings.setTitle("Settings")

        self.addAction(self.menuFile.menuAction())
        self.addAction(self.menuEdit.menuAction())
        self.addAction(self.menuView.menuAction())
        self.addAction(self.menuSettings.menuAction())

        self.menuFile.addAction(actions.new_File)
        self.menuFile.addSeparator()
        self.menuFile.addAction(actions.open_File)
        self.recent_files_menu = RecentFilesMenu()
        self.menuFile.addMenu(self.recent_files_menu)
        self.menuFile.addSeparator()
        self.menuFile.addAction(actions.save)
        self.menuFile.addAction(actions.save_as)
        self.menuFile.addSeparator()
        self.menuFile.addAction(actions.close)
        self.menuFile.addSeparator()
        self.menuFile.addAction(actions.quit)
        self.menuFile.addSeparator()

        self.menuEdit.addAction(actions.copy)
        self.menuEdit.addAction(actions.cut)
        self.menuEdit.addAction(actions.paste)

        self.menuView.addActions(actions.layout.actions())
        self.menuView.addSeparator()
        self.menuView.addAction(actions.show_fs_explorer)
        self.menuView.addAction(actions.show_compiler_options)
        self.menuView.addAction(actions.show_compiler_output)

        self.menuSettings.addAction(actions.open_config)


class RecentFilesMenu(QtWidgets.QMenu):
    """Menu showing the recently used files."""

    open_file = QtCore.Signal(str)

    def __init__(self):
        """Init."""
        QtWidgets.QMenu.__init__(self)

        self.setIcon(QtGui.QIcon("icons/recentFile.svg"))
        self.setTitle("Open recent file")

        self.addAction("")

        self.triggered.connect(self.open_from_action)

    def display_recent_files(self, recent_files):
        """Diplay a list of recent files."""
        self.clear()
        for f in recent_files:
            self.addAction(f)

    def open_from_action(self, action):
        """Emit open_file signal with text of given action."""
        self.open_file.emit(action.text())

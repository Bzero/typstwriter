from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import collections
import os
import platform
import subprocess

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class FileIconProvider(QtWidgets.QFileIconProvider):
    """Adds a typst icon to the default QFileIconProvider."""

    def icon(self, info):
        """Return icon associated with info."""
        if isinstance(info, QtCore.QFileInfo): # noqa SIM102
            if info.suffix() == "typ":
                return QtGui.QIcon(icon_path("typst.png"))
        return super().icon(info)


class RecentFilesModel(QtCore.QAbstractListModel):
    """A data model of the recently used files."""

    def __init__(self, recent_files):
        """Initialize and store data."""
        QtCore.QAbstractListModel.__init__(self)
        self.recent_files = recent_files

    def data(self, index, role):
        """Return the filepath (or its icon) stored under a given index."""
        path = self.recent_files[index.row()]

        match role:
            case QtCore.Qt.DisplayRole:
                return path
            case QtCore.Qt.DecorationRole:
                return FileIconProvider().icon(QtCore.QFileInfo(path))
            case _:
                return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole): # noqa: N802 This is an overriding function
        """Return the header name."""
        return "Filepath"

    def rowCount(self, index): # noqa: N802 This is an overriding function
        """Return the number of stored filepaths."""
        return len(self.recent_files)


class RecentFiles(QtCore.QObject):
    """Stores, reads and writes a fixed-size list of recently used files."""

    recent_files_changed = QtCore.Signal(list)

    def __init__(self, path=None):
        """
        Initialize and load recent files list.

        The path of the file storing the list of recent files is set to path argument if given, otherwise use the config value.
        """
        QtCore.QObject.__init__(self)

        maxlen = config.get("Internals", "recent_files_length", "int")
        self.recent_files = collections.deque(maxlen=maxlen)

        if not path:
            path = config.get("Internals", "recent_files_path")

        self.path = os.path.expanduser(path)
        self.read()

    def append(self, file):
        """Append file to the recent files list."""
        if file not in self.recent_files:
            self.recent_files.appendleft(file)
        else:
            self.recent_files.remove(file)
            self.recent_files.appendleft(file)

        self.recent_files_changed.emit(list(self.recent_files))

    def clear(self):
        """Clear the recent files list."""
        self.recent_files.clear()
        self.recent_files_changed.emit(list(self.recent_files))

    def list(self):
        """Return the recent files list."""
        return list(self.recent_files)

    def read(self):
        """Read the list of recently used files from disk."""
        self.clear()
        try:
            with open(self.path, "r") as f:
                for line in f:
                    self.recent_files.append(line.strip())
        except OSError:
            logger.info("Could not read file {!r}.", self.path)

    def write(self):
        """Write the list of recently used files to disk."""
        try:
            with open(self.path, "w") as f:
                for line in self.recent_files:
                    f.write(line + "\n")
        except OSError:
            logger.info("Could not write file {!r}.", self.path)


def open_with_external_program(path):
    """Open a file in an external program."""
    if os.path.exists(path):
        match platform.system():
            case "Linux":
                subprocess.call(["xdg-open", path])
            case "Windows":
                os.startfile(path)
            case "Darwin":
                subprocess.call(["open", path])
            case _:
                logger.error("Unsupported system : {}.", platform.system())
    else:
        logger.warning("Attempted to open file with external program but {!r} is not a valid path.", path)


def pdf_path(typst_path):
    """Convert a input path to a pdf output path."""
    (trunk, ext) = os.path.splitext(typst_path)
    pdf_path = trunk + ".pdf"
    return pdf_path


class TogglingAction(QtWidgets.QAction):
    """
    A QAction that can be toggled.

    It automatically changes text and icon when being toggled.
    User triggering causes the activated/deactivated signals being emitted.
    """

    activated = QtCore.Signal()
    deactivated = QtCore.Signal()

    def __init__(self, parent):
        """Init."""
        QtWidgets.QAction.__init__(self, parent)
        self.setCheckable(True)
        self.text_on = ""
        self.text_off = ""
        self.toggled.connect(self.update_text)  # User or progammatic interaction
        self.triggered.connect(self.handle_triggered)  # User interaction

    def setText(self, text, state=None): # noqa N802
        """Extend parent setText with state information."""
        if state == QtGui.QIcon.State.On or state is None:
            self.text_on = text
        if state == QtGui.QIcon.State.Off or state is None:
            self.text_off = text
        self.update_text()

    def update_text(self):
        """Update text when toggling."""
        if self.isChecked() is True:
            super().setText(self.text_on)
        else:
            super().setText(self.text_off)

    def handle_triggered(self, checked):
        """Handle toggling."""
        self.update_text()
        if checked:
            self.activated.emit()
        else:
            self.deactivated.emit()


def icon_path(name):
    """Get an icon by filename."""
    packagedir = os.path.dirname(__file__)
    path = os.path.join(packagedir, "icons", name)
    return path

from qtpy import QtCore
from qtpy import QtGui

import logging

from typstwriter import util


class TestFileIconProvider:
    """Test util.FileIconProvider."""

    def test_dottyp(self, qtbot):
        """Test if the .typ icon is available."""
        finfo = QtCore.QFileInfo(QtCore.QDir("some/path/"), "file.typ")
        fip = util.FileIconProvider()
        icon = fip.icon(finfo)
        assert isinstance(icon, QtGui.QIcon)

    def test_dotother(self, qtbot):
        """Test if the .typ icon is available."""
        finfo = QtCore.QFileInfo(QtCore.QDir("some/path/"), "file.other")
        fip = util.FileIconProvider()
        icon = fip.icon(finfo)
        assert isinstance(icon, QtGui.QIcon)


class TestRecentFilesModel:
    """Test util.RecentFilesModel."""

    file_list = ["a.txt", "b.typ", "c.py"]  # noqa RUF012

    def test_data_data(self):
        """Make sure correct data is returned."""
        model = util.RecentFilesModel(self.file_list)
        for i, f in enumerate(self.file_list):
            assert model.data(model.createIndex(i, 0, None), QtCore.Qt.DisplayRole) == f

    def test_data_icon(self):
        """Make sure an icon is returned."""
        model = util.RecentFilesModel(self.file_list)
        for i, _ in enumerate(self.file_list):
            assert isinstance(model.data(model.createIndex(i, 0, None), QtCore.Qt.DecorationRole), QtGui.QIcon)

    def test_data_other(self):
        """Make sure an None is returned for other role."""
        model = util.RecentFilesModel(self.file_list)
        for i, _ in enumerate(self.file_list):
            assert model.data(model.createIndex(i, 0, None), QtCore.Qt.EditRole) is None

    def test_rowCount(self):
        """Make sure the row_count is correct."""
        model = util.RecentFilesModel(self.file_list)
        assert model.rowCount(0) == len(self.file_list)

    def test_header(self):
        """Make sure the header is a string."""
        model = util.RecentFilesModel([])
        header = model.headerData(0, QtCore.Qt.Vertical)
        assert isinstance(header, str)


class TestRecentFiles:
    """Test util.RecentFiles."""

    def test_successful_read(self, tmp_path):
        """Test if reading a valid file is successful."""
        p = tmp_path / "recent_files"
        p.write_text("a.typ\nb.txt\nfolder/c.typ")
        r = util.RecentFiles(p)
        assert r.list() == ["a.typ", "b.txt", "folder/c.typ"]

    def test_successful_write(self, tmp_path):
        """Test if writing a valid file is successful."""
        p = tmp_path / "recent_files"
        p.write_text("")
        r = util.RecentFiles(p)
        r.append("a.txt")
        r.append("b.txt")
        r.append("folder/c.txt")
        r.write()
        assert p.read_text() == "folder/c.txt\nb.txt\na.txt\n"

    def test_failed_read(self, tmp_path, caplog):
        """Test if nonexistent file fails."""
        caplog.set_level(logging.INFO)
        p = tmp_path / "inexistent_file"
        util.RecentFiles(p)
        assert "Could not read" in caplog.text

    def test_failed_write(self, tmp_path, caplog):
        """Test if writing to a write protected file fails."""
        caplog.set_level(logging.INFO)
        p = tmp_path / "recent_files"
        p.write_text("")
        r = util.RecentFiles(p)
        p.chmod(0o000)
        r.write()
        assert "Could not write" in caplog.text

    def test_manipulation(self, tmp_path):
        """Test manipulationn of the recent files list."""
        # Create temporary recent files file
        p = tmp_path / "recent_files"
        p.write_text("")

        # Actual tests
        r = util.RecentFiles(p)
        r.append("a.txt")
        assert r.list() == ["a.txt"]
        r.append("b.txt")
        assert r.list() == ["b.txt", "a.txt"]
        r.append("folder/c.txt")
        assert r.list() == ["folder/c.txt", "b.txt", "a.txt"]
        r.append("b.txt")
        assert r.list() == ["b.txt", "folder/c.txt", "a.txt"]
        r.clear()
        assert r.list() == []


def test_pdf_path():
    """Test util.pdf_path()."""
    assert util.pdf_path("a/b/c/d.typ") == "a/b/c/d.pdf"
    assert util.pdf_path("a/b/c/d.txt") == "a/b/c/d.pdf"
    assert util.pdf_path("a/b/c/d") == "a/b/c/d.pdf"
    assert util.pdf_path("a/b/c/.d.typ") == "a/b/c/.d.pdf"
    assert util.pdf_path("d.typ") == "d.pdf"
    assert util.pdf_path(".d.typ") == ".d.pdf"


class TestTogglingAction:
    """Test util.TestTogglingAction."""

    def test_text_toggle(self):
        """Make sure the text toggles."""
        action = util.TogglingAction()
        action.setText("Off", state=QtGui.QIcon.State.Off)
        action.setText("On", state=QtGui.QIcon.State.On)

        action.setChecked(True)
        assert action.text() == "On"

        action.toggle()
        assert action.text() == "Off"

        action.toggle()
        assert action.text() == "On"

    def test_triggered_signal(self, qtbot):
        """Make sure the activated and deactivated signals are emitted."""
        action = util.TogglingAction()

        action.setChecked(True)

        with qtbot.waitSignal(action.deactivated):
            action.trigger()

        with qtbot.waitSignal(action.activated):
            action.trigger()


def test_typst_available(monkeypatch):
    """Test util.typst_available."""
    monkeypatch.setattr(QtCore.QProcess, "start", lambda *args: None)
    monkeypatch.setattr(QtCore.QProcess, "exitCode", lambda *args: 2)
    monkeypatch.setattr(QtCore.QProcess, "exitStatus", lambda *args: QtCore.QProcess.ExitStatus.NormalExit)

    # Typst available
    monkeypatch.setattr(QtCore.QProcess, "readAll", lambda *args: b"The Typst compiler")
    assert util.typst_available()

    # Typst not available
    monkeypatch.setattr(QtCore.QProcess, "readAll", lambda *args: b"Some other program")
    assert not util.typst_available()


def test_qstring_length():
    """Test util.qstring_length."""
    assert util.qstring_length("asdf") == 4  # noqa: PLR2004
    assert util.qstring_length("Some\nText") == 9  # noqa: PLR2004
    assert util.qstring_length("👍") == 2  # noqa: PLR2004
    assert util.qstring_length('"Happy Birthday 🎉"') == 19  # noqa: PLR2004

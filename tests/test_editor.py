from qtpy import QtCore
from qtpy import QtGui

from typstwriter import editor


class TestWelcomePage:
    """Test editor.WelcomePage."""

    def test_update_recent_files(self, qtbot):
        """Test updating the recent files."""
        recent_files = ["A.typ", "B.typ", "C.txt"]

        welcome_page = editor.WelcomePage()
        welcome_page.update_recent_files(recent_files)

        assert welcome_page.recentFilesModel.recent_files == recent_files
        for i, f in enumerate(recent_files):
            assert welcome_page.recentFilesModel.itemData(welcome_page.recentFilesModel.index(i))[0] == f

    def test_open_file(self, qtbot, tmp_path):
        """Test doubleclick in recent files."""
        path = tmp_path / "file.typ"
        path.touch()

        welcome_page = editor.WelcomePage()
        welcome_page.update_recent_files([str(path)])
        qtbot.addWidget(welcome_page)

        with qtbot.waitSignal(welcome_page.open_file) as blocker:
            welcome_page.doubleclicked(welcome_page.recentFilesModel.index(0))
        assert blocker.args[0] == str(path)

    def test_tryclose(self):
        """Test trying to close the Page."""
        welcome_page = editor.WelcomePage()
        assert welcome_page.tryclose() is True


class TestCodeEdit:
    """Test editor.CodeEdit."""

    # TODO: Test syntax highlighting
    # TODO: Test line numbers

    def test_line_highlighting_on(self, qtbot):
        """Test line highlighting."""
        code_edit = editor.CodeEdit(highlight_synatx=False, show_line_numbers=False, highlight_line=True)
        code_edit.insertPlainText("Just\nsome\nexample\ntext.")

        # Selecting a single line should highlight
        code_edit.moveCursor(QtGui.QTextCursor.Start)
        code_edit.moveCursor(QtGui.QTextCursor.NextBlock, QtGui.QTextCursor.MoveMode.MoveAnchor)
        assert code_edit.extraSelections()[0].cursor == code_edit.textCursor()

        # Selecting multiple lines should not highlight
        code_edit.moveCursor(QtGui.QTextCursor.Start)
        code_edit.moveCursor(QtGui.QTextCursor.NextBlock, QtGui.QTextCursor.MoveMode.KeepAnchor)
        assert not code_edit.extraSelections()

    def test_line_highlighting_off(self, qtbot):
        """Test line highlighting."""
        code_edit = editor.CodeEdit(highlight_synatx=False, show_line_numbers=False, highlight_line=False)
        code_edit.insertPlainText("Just\nsome\nexample\ntext.")
        code_edit.moveCursor(QtGui.QTextCursor.Start)
        code_edit.moveCursor(QtGui.QTextCursor.NextBlock)
        assert not code_edit.extraSelections()

    def test_key_press_tab(self, qtbot):
        """Test key press interception when pressing tab."""
        code_edit = editor.CodeEdit(highlight_synatx=False, show_line_numbers=False, use_spaces=True)
        qtbot.keyPress(code_edit, QtCore.Qt.Key_Tab)
        assert code_edit.toPlainText() == "    "

    def test_key_press_linebreak(self, qtbot):
        """Test key press interception when pressing shift enter."""
        code_edit = editor.CodeEdit(highlight_synatx=False, show_line_numbers=False, use_spaces=True)
        qtbot.keyPress(code_edit, QtCore.Qt.Key_Return, QtCore.Qt.ShiftModifier)
        assert code_edit.toPlainText() == "\n"

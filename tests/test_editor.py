from qtpy import QtCore
from qtpy import QtGui

import pytest

from typstwriter import editor
from typstwriter import enums

search_data = [
    (
        "Fischers Fritz fischt frische Fische,\nfrische Fische fischt Fischers Fritz",
        "Fisch",
        enums.search_mode.case_insensitive,
        [(0, 5), (15, 20), (30, 35), (46, 51), (53, 58), (60, 65)],
        "_",
        "_ers Fritz _t frische _e,\nfrische _e _t _ers Fritz",
    ),
    (
        "Fischers Fritz fischt frische Fische,\nfrische Fische fischt Fischers Fritz",
        "Fisch",
        enums.search_mode.case_sensitive,
        [(0, 5), (30, 35), (46, 51), (60, 65)],
        "_",
        "_ers Fritz fischt frische _e,\nfrische _e fischt _ers Fritz",
    ),
    (
        "Fischers Fritz fischt frische Fische,\nfrische Fische fischt Fischers Fritz",
        "Fische",
        enums.search_mode.whole_words,
        [(30, 36), (46, 52)],
        "_",
        "Fischers Fritz fischt frische _,\nfrische _ fischt Fischers Fritz",
    ),
    (
        "Fischers Fritz fischt frische Fische,\nfrische Fische fischt Fischers Fritz",
        r"\bFischers \w+\b",
        enums.search_mode.regex,
        [(0, 14), (60, 74)],
        "_",
        "_ fischt frische Fische,\nfrische Fische fischt _",
    ),
]

comment_text = [
    ("Just some text.", "//Just some text.", "Just some text.", (0, 0)),
    ("Just\nsome\ntext.", "//Just\n//some\ntext.", "Just\nsome\ntext.", (0, 1)),
    ("Just\n//some\ntext.", "//Just\n////some\n//text.", "Just\n//some\ntext.", (0, 2)),
    ("Just\n//some\ntext.", "Just\nsome\ntext.", "Just\n//some\ntext.", (1, 1)),
    ("Just\n  //some\ntext.", "Just\n  some\ntext.", "Just\n//  some\ntext.", (1, 1)),
    ("Just\nsome//more\ntext.", "Just\n//some//more\ntext.", "Just\nsome//more\ntext.", (1, 1)),
]


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

    @pytest.mark.parametrize(("text", "query", "mode", "_spans", "replace_text", "result"), search_data)
    def test_replace_all_matches(self, query, mode, text, replace_text, result, _spans):  # noqa PT019
        """Test replace_all_matches() for all four query modes."""
        code_edit = editor.CodeEdit(highlight_synatx=False, show_line_numbers=False, use_spaces=True)
        code_edit.insertPlainText(text)
        code_edit.replace_all_matches(query, mode, replace_text)
        assert code_edit.toPlainText() == result

    @pytest.mark.parametrize(("text", "query", "mode", "spans", "_replace_text", "_result"), search_data)
    def test_highlight_all_matches(self, query, mode, text, spans, _replace_text, _result):  # noqa PT019
        """Test highlight_all_matches() for all four query modes."""
        code_edit = editor.CodeEdit(highlight_synatx=False, show_line_numbers=False, use_spaces=True)
        code_edit.insertPlainText(text)
        code_edit.highlight_all_matches(query, mode)
        for selection, span in zip(code_edit.search_highlights, spans, strict=True):
            assert selection.cursor.anchor() == span[0]
            assert selection.cursor.position() == span[1]

    @pytest.mark.parametrize(("text", "toggle", "retoggle", "selection"), comment_text)
    def test_highlight_all_matches(self, text, toggle, retoggle, selection):  # noqa PT019
        """Test toggle_comment() for various selections."""
        start, stop = selection
        code_edit = editor.CodeEdit(highlight_synatx=False, show_line_numbers=False, use_spaces=True)
        code_edit.insertPlainText(text)
        cursor = code_edit.textCursor()
        cursor.setPosition(0)
        cursor.movePosition(QtGui.QTextCursor.NextBlock, QtGui.QTextCursor.MoveAnchor, start)
        cursor.movePosition(QtGui.QTextCursor.NextBlock, QtGui.QTextCursor.KeepAnchor, stop - start)
        code_edit.setTextCursor(cursor)

        code_edit.toggle_comment()
        assert code_edit.toPlainText() == toggle

        code_edit.toggle_comment()
        assert code_edit.toPlainText() == retoggle

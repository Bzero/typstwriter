from qtpy import QtWidgets

from typstwriter import compiler_tools

from typstwriter import globalstate


class TestCompilerOptions:
    """Test compiler_tools.CompilerOptions."""

    def test_main_changed(self, qtbot, tmp_path):
        """Check the behaviour when main changes."""
        pth = tmp_path / "some_file.typ"
        compileroptions = compiler_tools.CompilerOptions()
        compileroptions.main_changed(str(pth))
        assert compileroptions.line_edit_main.text() == str(pth)

    def test_main_path_edited(self, qtbot, tmp_path):
        """Check the behaviour when the main_path is edited."""
        pth = tmp_path / "some_file.typ"
        compileroptions = compiler_tools.CompilerOptions()

        # invalid path
        compileroptions.line_edit_main.setText(str(pth))
        compileroptions.line_edit_main.editingFinished.emit()
        assert compileroptions.line_edit_main.text() != str(pth)
        assert globalstate.State.main_file.Value != str(pth)

        # valid path
        pth.touch()
        compileroptions.line_edit_main.setText(str(pth))
        compileroptions.line_edit_main.editingFinished.emit()
        assert compileroptions.line_edit_main.text() == str(pth)
        assert globalstate.State.main_file.Value == str(pth)

    def test_file_dialog(self, qtbot, tmp_path, monkeypatch):
        """Test setting the main file via file dialog."""
        pth = tmp_path / "some_file.typ"
        pth.touch()
        compileroptions = compiler_tools.CompilerOptions()
        monkeypatch.setattr(QtWidgets.QFileDialog, "getOpenFileName", lambda *args: (str(pth), ""))

        compileroptions.open_file_dialog()
        assert compileroptions.line_edit_main.text() == str(pth)
        assert globalstate.State.main_file.Value == str(pth)

    def test_mode_changed(self, qtbot, tmp_path):
        """Test canging mode."""
        pth = tmp_path / "some_file.typ"
        pth.touch()
        compileroptions = compiler_tools.CompilerOptions()
        compileroptions.combo_box_mode.setCurrentIndex(0)
        assert globalstate.State.compiler_mode.Value == compileroptions.combo_box_mode.itemData(0)
        compileroptions.combo_box_mode.setCurrentIndex(1)
        assert globalstate.State.compiler_mode.Value == compileroptions.combo_box_mode.itemData(1)


class TestCompilerOutput:
    """Test compiler_tools.CompilerOutput."""

    def test_clear_button(self, qtbot):
        """Make sure clearing the display works."""
        compileroutput = compiler_tools.CompilerOutput()
        compileroutput.OutputDisplay.insertPlainText("Test")
        assert compileroutput.OutputDisplay.toPlainText() == "Test"
        compileroutput.ClearDisplay.click()
        assert compileroutput.OutputDisplay.toPlainText() == ""

    def test_insert_insert_block(self, qtbot):
        """Test compiler_tools.insert_block."""
        compileroutput = compiler_tools.CompilerOutput()

        compileroutput.insert_block(text="Test")
        assert compileroutput.OutputDisplay.toPlainText() == "Test"
        assert "<hr />" not in compileroutput.OutputDisplay.toHtml()
        compileroutput.insert_block(text="Test")
        assert "<hr />" in compileroutput.OutputDisplay.toHtml()
        compileroutput.OutputDisplay.clear()

    def test_append_to_block(self, qtbot):
        """Test compiler_tools.append_to_block."""
        compileroutput = compiler_tools.CompilerOutput()

        compileroutput.append_to_block(text="Test\n")
        compileroutput.append_to_block(text="Test")
        assert compileroutput.OutputDisplay.toPlainText() == "Test\nTest"
        assert "<hr />" not in compileroutput.OutputDisplay.toHtml()

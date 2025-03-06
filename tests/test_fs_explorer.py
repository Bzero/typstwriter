from qtpy import QtWidgets

from typstwriter import fs_explorer


class TestFSExplorer:
    """Test fs_explorer.FSExplorer."""

    def test_open_directory_dialog(self, tmp_path, qtbot, monkeypatch):
        """Make sure the root can be set."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)

        existant_path = tmp_path / "test_folder_existant"
        existant_path.mkdir()
        monkeypatch.setattr(QtWidgets.QFileDialog, "getExistingDirectory", lambda *args: str(existant_path))
        fse.open_directory_dialog()
        assert fse.root == str(existant_path)

        non_existant_path = tmp_path / "test_folder_non_existant"
        monkeypatch.setattr(QtWidgets.QFileDialog, "getExistingDirectory", lambda *args: str(non_existant_path))
        fse.open_directory_dialog()
        assert fse.root != str(non_existant_path)

    def test_root_setting(self, tmp_path, qtbot):
        """Make sure the root can be set."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)
        fse.set_root(str(tmp_path))

        assert fse.root == str(tmp_path)
        assert fse.filesystem_model.rootPath() == str(tmp_path)
        assert fse.completer_filesystem_model.rootPath() == str(tmp_path)
        assert fse.pathBar.text() == str(tmp_path)
        assert fs_explorer.state.working_directory.Value == str(tmp_path)

    def test_line_edited(self, tmp_path, qtbot):
        """Make sure line_edited changes root if valid."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)

        # Valid path
        fse.pathBar.setText(str(tmp_path))
        fse.pathBar.editingFinished.emit()
        assert fse.root == str(tmp_path)

        # Invalid path
        text = fse.pathBar.text()
        root = fse.root
        fse.pathBar.setText(str(tmp_path / "nonexistent_dir"))
        fse.pathBar.editingFinished.emit()
        assert fse.root == root
        assert fse.pathBar.text() == text

    def test_goto_parent_directory(self, tmp_path, qtbot):
        """Make sure the root can be set."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)

        path = tmp_path / "test_path"
        path.mkdir()
        fse.set_root(str(path))
        fse.goto_parent_directory()
        assert fse.root == str(tmp_path)

    def test_new_file(self, tmp_path, qtbot, caplog, monkeypatch):
        """Make sure a new file behaves correctly."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)
        monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *args: QtWidgets.QMessageBox.Ok)

        file_name = "test_file.dat"
        file_path = tmp_path / file_name

        # Automatically answer dialog
        monkeypatch.setattr(QtWidgets.QInputDialog, "getText", lambda *args: (file_name, True))

        # Make sure the file can be created
        assert not file_path.exists()
        fse.new_file_in_dir(str(tmp_path))
        assert file_path.exists()

        # Make sure the file is not overwritten
        file_path.write_text("Test")
        assert file_path.read_text() == "Test"
        fse.new_file_in_dir(str(tmp_path))
        assert "already exists" in caplog.text
        assert file_path.read_text() == "Test"

        # Make sure the file is overwritten if flag is set
        file_path.write_text("Test")
        assert file_path.read_text() == "Test"
        fse.new_file(str(file_path), overwrite=True)
        assert file_path.read_text() != "Test"

    def test_new_folder(self, tmp_path, qtbot, caplog, monkeypatch):
        """Make sure a new folder behaves correctly."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)
        monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *args: QtWidgets.QMessageBox.Ok)

        folder_name = "test_folder"
        folder_path = tmp_path / folder_name

        # Automatically answer dialog
        monkeypatch.setattr(QtWidgets.QInputDialog, "getText", lambda *args: (folder_name, True))

        # Make sure the folder can be created
        assert not folder_path.exists()
        fse.new_folder_in_dir(str(tmp_path))
        assert folder_path.exists()

        # Make sure the folder is not overwritten
        assert folder_path.exists()
        fse.new_folder_in_dir(str(tmp_path))
        assert "already exists" in caplog.text

    def test_rename(self, tmp_path, qtbot, caplog, monkeypatch):
        """Make sure rename works."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)
        monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *args: QtWidgets.QMessageBox.Ok)

        from_name = "test_file_from"
        to_name = "test_file_to"
        from_path = tmp_path / from_name
        to_path = tmp_path / to_name
        from_path.touch()

        # Automatically answer dialog
        monkeypatch.setattr(QtWidgets.QInputDialog, "getText", lambda *args, **kwargs: (to_name, True))

        # Make sure the file can be renamed
        assert from_path.exists()
        assert not to_path.exists()
        fse.rename_from(str(from_path))
        assert not from_path.exists()
        assert to_path.exists()

        # Make sure the file is not overwritten
        from_path.touch()
        assert from_path.exists()
        assert to_path.exists()
        fse.rename_from(str(from_path))
        assert "already exists" in caplog.text
        assert from_path.exists()
        assert to_path.exists()

    def test_copy_from_to(self, tmp_path, qtbot, caplog, monkeypatch):
        """Make sure copying works."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)
        monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *args: QtWidgets.QMessageBox.Ok)

        name = "test_file_name"
        from_dir = tmp_path / "from"
        to_dir = tmp_path / "to"
        from_dir.mkdir()
        to_dir.mkdir()
        from_path = from_dir / name
        to_path = to_dir / name

        from_path.touch()

        # Make sure the file can be copied
        assert from_path.exists()
        assert not to_path.exists()
        fse.copy_from_to(str(from_path), str(to_path))
        assert from_path.exists()
        assert to_path.exists()

        # Make sure the file is not overwritten
        from_path.touch()
        to_path.touch()
        assert from_path.exists()
        assert to_path.exists()
        fse.copy_from_to(str(from_path), str(to_path))
        assert "already exists" in caplog.text
        assert from_path.exists()
        assert to_path.exists()

    def test_delete(self, tmp_path, qtbot, monkeypatch):
        """Make sure a folder or file can be deleted."""
        fse = fs_explorer.FSExplorer()
        qtbot.addWidget(fse)

        folder_path = tmp_path / "test_folder"
        file_path = tmp_path / "test_file.dat"

        folder_path.mkdir()
        file_path.touch()
        assert file_path.exists()
        assert folder_path.exists()

        # Decline deletion
        monkeypatch.setattr(QtWidgets.QMessageBox, "question", lambda *args: QtWidgets.QMessageBox.StandardButton.No)
        fse.delete(str(folder_path))
        fse.delete(str(file_path))
        assert file_path.exists()
        assert folder_path.exists()

        # Accept deletion
        monkeypatch.setattr(QtWidgets.QMessageBox, "question", lambda *args: QtWidgets.QMessageBox.StandardButton.Yes)
        fse.delete(str(folder_path))
        fse.delete(str(file_path))
        assert not file_path.exists()
        assert not folder_path.exists()

import pytest

import configparser

from typstwriter import configuration

example_config = """
[Section_1]
key_1 = /home/user/Documents/

[Section_2]
key_1 = 200
key_2 = Some Text
key_3 = True
key_4 = 3.5

[Compiler]
name = custom_typst_cli
mode = on_demand
"""


@pytest.fixture()
def custom_config(tmp_path):
    """Write a custom config file and return the corresponding path."""
    config_file_path = tmp_path / "config_file.ini"
    config_file_path.write_text(example_config)
    return config_file_path


class TestConfigManager:
    """Test configuration.ConfigManager."""

    def test_constructor_default_config(self, tmp_path):
        """Make sure the constructor correctly loads the default config."""
        cm = configuration.ConfigManager()

        assert cm.config.get("Compiler", "name") == "typst"
        assert cm.writepath == str(configuration.default_config_path)

    def test_constructor_custom_config(self, custom_config):
        """Make sure the constructor correctly loads a config file."""
        cm = configuration.ConfigManager(custom_config)

        assert cm.config.get("Compiler", "name") == "custom_typst_cli"
        assert cm.writepath == str(custom_config)

    def test_get(self, custom_config, caplog):
        """Test the get function."""
        cm = configuration.ConfigManager(custom_config)

        assert cm.get("Section_2", "key_1") == "200"
        assert cm.get("Section_2", "key_2", typ="string") == "Some Text"
        assert cm.get("Section_2", "key_1", typ="int") == 200  # noqa: PLR2004
        assert cm.get("Section_2", "key_4", typ="float") == 3.5  # noqa: PLR2004
        assert cm.get("Section_2", "key_3", typ="bool") is True
        assert cm.get("Section_2", "key_3", typ="no_type") is None
        assert "Unknown type" in caplog.text

        with pytest.raises(configparser.NoOptionError):
            cm.get("Section_2", "no_such_key")

    def test_set(self, custom_config):
        """Test the set function."""
        cm = configuration.ConfigManager(custom_config)

        cm.set("Section_2", "key_1", 44)
        assert cm.config.get("Section_2", "key_1") == "44"

        cm.set("Section_2", "key_1", "44")
        assert cm.config.get("Section_2", "key_1") == "44"

        cm.set("Section_2", "key_1", False)
        assert cm.config.get("Section_2", "key_1") == "False"

    def test_read_default(self, custom_config, caplog):
        """Test the read function with no path provided."""
        # Initially no file provided
        cm = configuration.ConfigManager()
        cm.read()
        assert "No file to read from was specified." in caplog.text

        # Initial file provided
        cm = configuration.ConfigManager(custom_config)
        cm.set("Compiler", "name", "typst")
        assert cm.config.get("Compiler", "name") == "typst"
        cm.read()
        assert cm.config.get("Compiler", "name") == "custom_typst_cli"

    def test_read_path(self, custom_config):
        """Test the read function with path provided."""
        cm = configuration.ConfigManager()
        assert cm.config.get("Compiler", "name") == "typst"
        cm.read(paths=custom_config)
        assert cm.config.get("Compiler", "name") == "custom_typst_cli"

    def test_write_default(self, custom_config):
        """Test the write function with no path provided."""
        cm = configuration.ConfigManager(custom_config)
        custom_config.unlink()
        assert not custom_config.exists()
        cm.write()
        assert custom_config.exists()

    def test_write_path(self, custom_config, tmp_path):
        """Test the write function with path provided."""
        cm = configuration.ConfigManager(custom_config)
        file_out = tmp_path / "folder" / "configfile.ini"
        assert not file_out.exists()
        cm.write(path=file_out)
        assert file_out.exists()

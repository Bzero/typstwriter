import os
import configparser
import logging

logger = logging.getLogger(__name__)


default_config_path = os.path.expanduser("~/.config/typstwriter/typstwriter.ini")

config_paths = ["/etc/typstwriter/typstwriter.ini",
                "/usr/local/etc/typstwriter/typstwriter.ini",
                default_config_path,
                os.path.expanduser("~/.typstwriter.ini"),
                "./typstwriter.ini"]

default_config = {"General": {"WorkingDirectory": ""},
                  "Compiler": {"Name": "typst",
                               "Mode": "on_demand"},
                  "Editor": {"saveatrun": "true",
                             "highlighter-style": "sas"},  # Can be any style from https://pygments.org/styles/
                  "Internals": {"recentFilesPath": "~/.config/typstwriter/recentFiles.txt",
                                "recentFilesLength": 16}}


class ConfigManager:
    """Handle configuration."""

    def __init__(self, paths=None):
        """Set config to default and attempt to read config files, if given."""
        self.config = configparser.ConfigParser(empty_lines_in_values=False)

        # load default config
        self.config.read_dict(default_config)

        self.readpaths = paths
        self.writepath = default_config_path

        # read config
        if paths:
            usedfile = self.config.read(self.readpaths)

            # Check if read was successful
            if usedfile:
                self.writepath = usedfile[-1]
            else:
                logger.warning(f"No valid config file found in {paths}")

    def get(self, section, key, typ="str"):
        """Get config value."""
        match typ:
            case "int" | "integer":
                return self.config.getint(section, key)
            case "float":
                return self.config.getfloat(section, key)
            case "bool" | "boolean":
                return self.config.getboolean(section, key)
            case "str" | "string":
                return self.config.get(section, key)
            case _:
                logger.error(f"Unknown type '{str(typ)}'")
                return None

    def set(self, section, key, value):
        """Set config value."""
        self.config.set(section, key, str(value))

    def read(self, paths=None):
        """Read the config from file."""
        if paths is None:
            paths = self.readpaths

        if paths:
            usedfile = self.config.read(paths)
            if not usedfile:
                logger.warning(f"No valid config file found in {paths}")
        else:
            logger.warning("No file to read from was specified.")

    def write(self, path=None):
        """Write the config to file."""
        if path is None:
            path = self.writepath

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as cf:
            self.config.write(cf)


Config = ConfigManager(config_paths)

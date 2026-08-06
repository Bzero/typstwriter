from qtpy import QtWidgets

import qt_themes

from typstwriter import configuration
from typstwriter import logging

logger = logging.getLogger(__name__)
config = configuration.Config


class SettingsDialog(QtWidgets.QDialog):
    """Settings Dialog."""

    def __init__(self, parent=None):
        """Init."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 400)

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.tabs = QtWidgets.QTabWidget(self)
        self.main_layout.addWidget(self.tabs)

        self.init_general_tab()
        self.init_compiler_tab()
        self.init_editor_tab()
        self.init_layout_tab()
        self.init_internals_tab()

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_settings)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

    def init_general_tab(self):
        """Initialize the General tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)

        self.general_working_directory = QtWidgets.QLineEdit(config.get("General", "working_directory"))
        layout.addRow("Working Directory:", self.general_working_directory)

        self.general_resume_session = QtWidgets.QCheckBox()
        self.general_resume_session.setChecked(config.get("General", "resume_last_session", "bool"))
        layout.addRow("Resume Last Session:", self.general_resume_session)

        self.general_theme = QtWidgets.QComboBox()
        theme_names = ["System Default", *sorted(qt_themes.get_themes().keys())]
        for t in theme_names:
            if t == "System Default":
                self.general_theme.addItem(t, None)
            else:
                self.general_theme.addItem(t.title().replace("_", " "), t)
        current_theme = config.get("General", "theme")
        index = self.general_theme.findData(current_theme)
        self.general_theme.setCurrentIndex(index if index >= 0 else 0)
        layout.addRow("Theme:", self.general_theme)

        hint_label = QtWidgets.QLabel()
        hint_label.setWordWrap(True)
        hint_label.setText(
            "<br><b>Typstwriter looks for configuration files in the following locations, in reverse order:</b> <br>"
            "- /etc/typstwriter/typstwriter.ini <br>"
            "- /usr/local/etc/typstwriter/typstwriter.ini <br>"
            "- $XDG_CONFIG_HOME/typstwriter/typstwriter.ini (Linux/Unix Only) <br>"
            "- %USERPROFILE%\\AppData\\Local\\typstwriter\\typstwriter.ini (Windows Only) <br>"
            "- ~/.typstwriter.ini <br>"
            "- ./typstwriter.ini (Working Directory) <br>"
            "You can either edit the settings here in this GUI, or manually through the configuration file \
             in the aforementioned locations."
        )
        layout.addRow(hint_label)
        self.tabs.addTab(tab, "General")

    def init_compiler_tab(self):
        """Initialize the Compiler tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)

        self.compiler_name = QtWidgets.QLineEdit(config.get("Compiler", "name"))
        layout.addRow("Name of Typst executable:", self.compiler_name)

        self.compiler_mode = QtWidgets.QComboBox()
        self.compiler_mode.addItem("Live", "live")
        self.compiler_mode.addItem("On Demand", "on_demand")
        current_mode = config.get("Compiler", "mode")
        index = self.compiler_mode.findData(current_mode)
        if index >= 0:
            self.compiler_mode.setCurrentIndex(index)
        layout.addRow("Mode:", self.compiler_mode)

        self.tabs.addTab(tab, "Compiler")

    def init_editor_tab(self):
        """Initialize the Editor tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)

        self.editor_font_size = QtWidgets.QSpinBox()
        self.editor_font_size.setRange(4, 72)
        self.editor_font_size.setValue(config.get("Editor", "font_size", "int"))
        layout.addRow("Font Size:", self.editor_font_size)

        self.editor_save_at_run = QtWidgets.QCheckBox()
        self.editor_save_at_run.setChecked(config.get("Editor", "save_at_run", "bool"))
        layout.addRow("Save at run:", self.editor_save_at_run)

        self.editor_highlighter_style = QtWidgets.QLineEdit(config.get("Editor", "highlighter_style"))
        layout.addRow("Highlighter Style:", self.editor_highlighter_style)

        hint_label = QtWidgets.QLabel()
        hint_label.setText(
            "<i>See <a href='https://pygments.org/styles/'>https://pygments.org/styles/</a>\
             for available options</i>"
        )
        hint_label.setOpenExternalLinks(True)
        layout.addRow("", hint_label)

        self.editor_highlight_syntax = QtWidgets.QCheckBox()
        self.editor_highlight_syntax.setChecked(config.get("Editor", "highlight_syntax", "bool"))
        layout.addRow("Highlight Syntax:", self.editor_highlight_syntax)

        self.editor_show_line_numbers = QtWidgets.QCheckBox()
        self.editor_show_line_numbers.setChecked(config.get("Editor", "show_line_numbers", "bool"))
        layout.addRow("Show Line Numbers:", self.editor_show_line_numbers)

        self.editor_highlight_line = QtWidgets.QCheckBox()
        self.editor_highlight_line.setChecked(config.get("Editor", "highlight_line", "bool"))
        layout.addRow("Highlight Line:", self.editor_highlight_line)

        self.editor_use_spaces = QtWidgets.QCheckBox()
        self.editor_use_spaces.setChecked(config.get("Editor", "use_spaces", "bool"))
        layout.addRow("Use Spaces:", self.editor_use_spaces)

        self.tabs.addTab(tab, "Editor")

    def init_layout_tab(self):
        """Initialize the Layout tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)

        self.layout_default_layout = QtWidgets.QComboBox()
        self.layout_default_layout.addItem("Typewriter (Editor under Preview)", "typewriter")
        self.layout_default_layout.addItem("Editor Right of Preview", "editor_right")
        self.layout_default_layout.addItem("Editor Left of Preview", "editor_left")
        current_layout = config.get("Layout", "default_layout")
        index = self.layout_default_layout.findData(current_layout)
        if index >= 0:
            self.layout_default_layout.setCurrentIndex(index)

        layout.addRow("Default Layout:", self.layout_default_layout)

        self.layout_show_fs_explorer = QtWidgets.QCheckBox()
        self.layout_show_fs_explorer.setChecked(config.get("Layout", "show_fs_explorer", "bool"))
        layout.addRow("Show FS Explorer:", self.layout_show_fs_explorer)

        self.layout_show_compiler_options = QtWidgets.QCheckBox()
        self.layout_show_compiler_options.setChecked(config.get("Layout", "show_compiler_options", "bool"))
        layout.addRow("Show Compiler Options:", self.layout_show_compiler_options)

        self.layout_show_compiler_output = QtWidgets.QCheckBox()
        self.layout_show_compiler_output.setChecked(config.get("Layout", "show_compiler_output", "bool"))
        layout.addRow("Show Compiler Output:", self.layout_show_compiler_output)

        self.tabs.addTab(tab, "Layout")

    def init_internals_tab(self):
        """Initialize the Internals tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(tab)

        self.internals_recent_files_path = QtWidgets.QLineEdit(config.get("Internals", "recent_files_path"))
        layout.addRow("Recent Files Path:", self.internals_recent_files_path)

        self.internals_recent_files_length = QtWidgets.QSpinBox()
        self.internals_recent_files_length.setRange(1, 100)
        self.internals_recent_files_length.setValue(config.get("Internals", "recent_files_length", "int"))
        layout.addRow("Recent Files Length:", self.internals_recent_files_length)

        self.internals_session_path = QtWidgets.QLineEdit(config.get("Internals", "session_path"))
        layout.addRow("Session Path:", self.internals_session_path)

        self.tabs.addTab(tab, "Internals")

    def save_settings(self):
        """Write the settings to the configuration file."""
        config.set("General", "working_directory", self.general_working_directory.text())
        config.set("General", "resume_last_session", self.general_resume_session.isChecked())
        config.set("General", "theme", self.general_theme.currentData())

        config.set("Compiler", "name", self.compiler_name.text())
        config.set("Compiler", "mode", self.compiler_mode.currentData())

        config.set("Editor", "font_size", self.editor_font_size.value())
        config.set("Editor", "save_at_run", self.editor_save_at_run.isChecked())
        config.set("Editor", "highlighter_style", self.editor_highlighter_style.text())
        config.set("Editor", "highlight_syntax", self.editor_highlight_syntax.isChecked())
        config.set("Editor", "show_line_numbers", self.editor_show_line_numbers.isChecked())
        config.set("Editor", "highlight_line", self.editor_highlight_line.isChecked())
        config.set("Editor", "use_spaces", self.editor_use_spaces.isChecked())

        config.set("Layout", "default_layout", self.layout_default_layout.currentData())
        config.set("Layout", "show_fs_explorer", self.layout_show_fs_explorer.isChecked())
        config.set("Layout", "show_compiler_options", self.layout_show_compiler_options.isChecked())
        config.set("Layout", "show_compiler_output", self.layout_show_compiler_output.isChecked())

        config.set("Internals", "recent_files_path", self.internals_recent_files_path.text())
        config.set("Internals", "recent_files_length", self.internals_recent_files_length.value())
        config.set("Internals", "session_path", self.internals_session_path.text())

        config.write()
        self.accept()

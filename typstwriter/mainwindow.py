from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

from typstwriter import menubar
from typstwriter import toolbar
from typstwriter import actions
from typstwriter import editor
from typstwriter import pdf_viewer
from typstwriter import fs_explorer
from typstwriter import compiler_tools
from typstwriter import compiler
from typstwriter import util

from typstwriter import logging
from typstwriter import configuration
from typstwriter import globalstate
from typstwriter import arguments

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State
args = arguments.Args


class MainWindow(QtWidgets.QMainWindow):
    """The main window."""

    def __init__(self):
        """Init."""
        super(self.__class__, self).__init__()

        self.setWindowTitle("Typstwriter")
        self.setObjectName("MainWindow")
        self.setWindowIcon(QtGui.QIcon(util.icon_path("typstwriter.svg")))

        # Actions
        self.actions = actions.Actions(self)

        # Menubar
        self.menubar = menubar.MenuBar(self.actions)
        self.setMenuBar(self.menubar)

        # Toolbar
        self.toolbar = toolbar.ToolBar(self.actions)
        self.addToolBar(self.toolbar)

        # Host Widget for Editor and PDF Viewer
        self.WidtetCore = QtWidgets.QWidget(self)
        self.CoreLayout_v = QtWidgets.QVBoxLayout(self.WidtetCore)
        self.CoreLayout_v.setContentsMargins(4, 4, 4, 4)
        self.CoreLayout_v.setSpacing(0)
        self.setCentralWidget(self.WidtetCore)

        self.splitter = QtWidgets.QSplitter(self.WidtetCore)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.CoreLayout_v.addWidget(self.splitter)

        # Host widget for PDF Viewer
        self.Widgetidget_31 = QtWidgets.QWidget(self.splitter)
        self.verticalLayout_1 = QtWidgets.QVBoxLayout(self.Widgetidget_31)
        self.verticalLayout_1.setContentsMargins(0, 0, 0, 0)

        # Host Widget for Editor
        self.Widgetidget = QtWidgets.QWidget(self.splitter)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.Widgetidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)

        # PDF Viewer
        self.PDFWidget = pdf_viewer.PDFViewer()
        self.verticalLayout_1.addWidget(self.PDFWidget)

        # Editor
        self.editor = editor.Editor()
        self.verticalLayout_3.addWidget(self.editor)

        # FSExplorer
        self.FSExplorer = fs_explorer.FSExplorer()
        self.FSdock = QtWidgets.QDockWidget("File System Explorer", self)
        self.FSdock.setWidget(self.FSExplorer)
        self.FSdock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.FSdock.setAllowedAreas(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea | QtCore.Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.FSdock)

        # CompilerOptions
        self.CompilerOptions = compiler_tools.CompilerOptions()
        self.CompilerOptionsdock = QtWidgets.QDockWidget("Compiler Options", self)
        self.CompilerOptionsdock.setWidget(self.CompilerOptions)
        self.CompilerOptionsdock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.CompilerOptionsdock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea | QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.CompilerOptionsdock)

        # Compiler Output
        self.CompilerOutput = compiler_tools.CompilerOutput()
        self.CompilerOutputdock = QtWidgets.QDockWidget("Compiler Output", self)
        self.CompilerOutputdock.setWidget(self.CompilerOutput)
        self.CompilerOutputdock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.CompilerOutputdock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea | QtCore.Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.CompilerOutputdock)

        # CompilerConnector
        self.CompilerConnector = compiler.WrappedCompilerConnector(state.compiler_mode.Value)

        # Connect signals and slots
        self.actions.new_File.triggered.connect(self.editor.new_file)
        self.actions.open_File.triggered.connect(self.editor.open_file_dialog)
        self.editor.recent_files_changed.connect(self.menubar.recent_files_menu.display_recent_files)
        self.menubar.recent_files_menu.open_file.connect(self.editor.open_file)
        self.menubar.recent_files_menu.display_recent_files(self.editor.recentFiles.list())
        self.actions.load_last_Session.triggered.connect(self.load_session)
        self.actions.save.triggered.connect(self.editor.saveactive_tab)
        self.actions.save_as.triggered.connect(self.editor.saveactive_tab_as)
        self.actions.close.triggered.connect(self.editor.closeactive_tab)
        self.actions.quit.triggered.connect(self.close)
        self.actions.copy.triggered.connect(self.editor.copy)
        self.actions.cut.triggered.connect(self.editor.cut)
        self.actions.paste.triggered.connect(self.editor.paste)
        self.actions.search.triggered.connect(self.editor.search)
        self.actions.layout_typewriter.triggered.connect(self.set_layout_typewriter)
        self.actions.layout_editorL.triggered.connect(self.set_layout_editorL)
        self.actions.layout_editorR.triggered.connect(self.set_layout_editorR)
        self.actions.font_size_up.triggered.connect(self.editor.increase_font_size)
        self.actions.font_size_dn.triggered.connect(self.editor.decrease_font_size)
        self.actions.font_size_reset.triggered.connect(self.editor.reset_font_size)
        self.actions.show_fs_explorer.toggled.connect(self.set_fs_explorer_visibility)
        self.actions.show_compiler_options.toggled.connect(self.set_compiler_options_visibility)
        self.actions.show_compiler_output.toggled.connect(self.set_compiler_output_visibility)
        self.actions.show_fs_explorer.setChecked(True)
        self.actions.show_compiler_options.setChecked(True)
        self.actions.show_compiler_output.setChecked(True)
        if config.get("Editor", "save_at_run", "bool"):
            self.actions.run.activated.connect(self.editor.save_all)
        self.actions.run.activated.connect(self.prepare_compilation)
        self.actions.run.activated.connect(self.CompilerConnector.start)
        self.actions.run.deactivated.connect(self.CompilerConnector.stop)
        self.CompilerConnector.started.connect(lambda: self.actions.run.setChecked(True))
        self.CompilerConnector.stopped.connect(lambda: self.actions.run.setChecked(False))
        self.actions.open_config.triggered.connect(self.open_config)

        self.FSExplorer.open_file.connect(self.editor.open_file)
        state.working_directory.Signal.connect(self.FSExplorer.root_changed)
        self.editor.text_changed.connect(self.CompilerConnector.source_changed)
        self.CompilerConnector.document_changed.connect(self.PDFWidget.reload)
        self.CompilerConnector.compilation_finished.connect(self.editor.clear_errors)
        self.CompilerConnector.error_report.connect(self.editor.apply_errors)
        state.main_file.Signal.connect(lambda s: self.CompilerConnector.stop())
        state.main_file.Signal.connect(lambda s: self.CompilerOptions.main_changed(s))
        state.main_file.Signal.connect(lambda s: self.PDFWidget.open(util.pdf_path(s)))

        # For now only display errors
        self.CompilerConnector.compilation_started.connect(self.CompilerOutput.insert_block)
        self.CompilerConnector.new_stderr.connect(self.CompilerOutput.append_to_block)
        state.compiler_mode.Signal.connect(self.CompilerConnector.switch_compiler)

        # Display
        self.showMaximized()

        # Use default layout
        self.use_default_layout()

        # Open files if given as arguments
        for file in args.files:
            self.editor.open_file(file)

        # Check if typst is available
        QtCore.QTimer().singleShot(0, self.check_typst_availability)

        if config.get("General", "resume_last_session", "bool"):
            QtCore.QTimer().singleShot(0, self.load_session)

        logger.info("Gui ready")

    def set_layout_typewriter(self):
        """Set Typstwriter Layout: PDF on top, Editor on bottom."""
        # Vertical orientation
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        # Reorder widgets
        self.splitter.addWidget(self.Widgetidget_31)
        self.splitter.addWidget(self.Widgetidget)

    def set_layout_editorR(self):  # noqa: N802
        """Set Layout to Editor right, PDF left."""
        # Horizontal orientation
        self.splitter.setOrientation(QtCore.Qt.Horizontal)

        # Reorder widgets
        self.splitter.addWidget(self.Widgetidget_31)
        self.splitter.addWidget(self.Widgetidget)

    def set_layout_editorL(self):  # noqa: N802
        """Set Layout to Editor left, PDF right."""
        # Horizontal orientation
        self.splitter.setOrientation(QtCore.Qt.Horizontal)

        # Reorder widgets
        self.splitter.addWidget(self.Widgetidget)
        self.splitter.addWidget(self.Widgetidget_31)

    def use_default_layout(self):
        """Adjust the layout set in the config."""
        match config.get("Layout", "default_layout"):
            case "typewriter":
                self.actions.layout_typewriter.trigger()
            case "editor_right":
                self.actions.layout_editorR.trigger()
            case "editor_left":
                self.actions.layout_editorL.trigger()
            case _:
                self.actions.layout_typewriter.trigger()

        self.actions.show_fs_explorer.setChecked(config.get("Layout", "show_fs_explorer", typ="bool"))
        self.actions.show_compiler_options.setChecked(config.get("Layout", "show_compiler_options", typ="bool"))
        self.actions.show_compiler_output.setChecked(config.get("Layout", "show_compiler_output", typ="bool"))

    def set_fs_explorer_visibility(self, visibility):
        """Set the visibility of the fs explplorer."""
        self.FSdock.setVisible(visibility)

    def set_compiler_options_visibility(self, visibility):
        """Set the visibility of the fs explplorer."""
        self.CompilerOptionsdock.setVisible(visibility)

    def set_compiler_output_visibility(self, visibility):
        """Set the visibility of the fs explplorer."""
        self.CompilerOutputdock.setVisible(visibility)

    def open_config(self):
        """Open config file."""
        config.write()
        util.open_with_external_program(config.writepath)

    def closeEvent(self, event):  # noqa: N802
        """Handle close event."""
        self.CompilerConnector.stop()
        self.save_session()
        s = self.editor.tryclose()
        if s:
            event.accept()
        else:
            event.ignore()

    def prepare_compilation(self):
        """Set appropriate input and output files before compiling."""
        if state.main_file.Value is None:  # noqa: SIM108
            main = self.editor.TabWidget.currentWidget().path
        else:
            main = state.main_file.Value

        if main:
            self.CompilerConnector.set_fin(main)
            self.CompilerConnector.set_fout(util.pdf_path(main))
            self.PDFWidget.open(util.pdf_path(main))

    def load_session(self):
        """Load the last session."""
        logger.info("Loading last session.")
        session = util.read_session_file()
        if session:
            (working_directory, files) = session
            state.working_directory.Value = working_directory
            for f in files:
                self.editor.open_file(f)

    def save_session(self):
        """Save the current session."""
        logger.debug("Saving last session.")
        util.write_session_file(state.working_directory.Value, self.editor.openfiles_list())

    def check_typst_availability(self):
        """Check if typst is available."""
        if not util.typst_available():
            logger.warning("The typst executable was not found.")

            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.setWindowTitle("Typst not found")
            msg_box.setText(
                "The typst executable could not be found found:\nTypstwriter will not be able to compile documents."
            )
            msg_box.setInformativeText(
                "Please install typst, make sure it was added to the 'PATH' environment variable \
and check the typstwriter configuration file."
            )
            msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ignore | QtWidgets.QMessageBox.StandardButton.Abort)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ignore)

            match msg_box.exec():
                case QtWidgets.QMessageBox.StandardButton.Ignore:
                    pass
                case QtWidgets.QMessageBox.StandardButton.Abort:
                    self.close()

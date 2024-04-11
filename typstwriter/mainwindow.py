from qtpy import QtGui
from qtpy import QtCore
from qtpy import QtWidgets

import menubar
import toolbar
import actions
import editor
import pdf_viewer
import fs_explorer
import compiler_tools
import compiler
import util
import enums

import logging
import configuration
import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


class MainWindow(QtWidgets.QMainWindow):
    """The main window."""

    def __init__(self):
        """Init."""
        super(self.__class__, self).__init__()

        self.setWindowTitle("Typstwriter")
        self.setObjectName("MainWindow")
        self.setWindowIcon(QtGui.QIcon("icons/typstwriter.png"))

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
        self.CompilerOptionsdock.setAllowedAreas(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea | QtCore.Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.CompilerOptionsdock)

        # Compiler Output
        self.CompilerOutput = compiler_tools.CompilerOutput()
        self.CompilerOutputdock = QtWidgets.QDockWidget("Compiler Output", self)
        self.CompilerOutputdock.setWidget(self.CompilerOutput)
        self.CompilerOutputdock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.CompilerOutputdock.setAllowedAreas(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea | QtCore.Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.CompilerOutputdock)

        # CompilerConnector
        self.CompilerConnector = compiler.WrappedCompilerConnector(state.compiler_mode.Value)

        # Connect signals and slots
        self.actions.new_File.triggered.connect(self.editor.new_file)
        self.actions.open_File.triggered.connect(self.editor.open_file_dialog)
        self.editor.recent_files_changed.connect(self.menubar.recent_files_menu.display_recent_files)
        self.menubar.recent_files_menu.open_file.connect(self.editor.open_file)
        self.menubar.recent_files_menu.display_recent_files(self.editor.recentFiles.list())
        self.actions.save.triggered.connect(self.editor.saveactive_tab)
        self.actions.save_as.triggered.connect(self.editor.saveactive_tab_as)
        self.actions.close.triggered.connect(self.editor.closeactive_tab)
        self.actions.quit.triggered.connect(self.close)
        self.actions.copy.triggered.connect(self.editor.copy)
        self.actions.cut.triggered.connect(self.editor.cut)
        self.actions.paste.triggered.connect(self.editor.paste)
        self.actions.layout_typewriter.triggered.connect(self.set_layout_typewriter)
        self.actions.layout_editorL.triggered.connect(self.set_layout_editorL)
        self.actions.layout_editorR.triggered.connect(self.set_layout_editorR)
        self.actions.show_fs_explorer.triggered.connect(self.set_fs_explorer_visibility)
        self.actions.show_compiler_options.triggered.connect(self.set_compiler_options_visibility)
        self.actions.show_compiler_output.triggered.connect(self.set_compiler_output_visibility)
        self.actions.show_fs_explorer.setChecked(True)
        self.actions.show_compiler_options.setChecked(True)
        self.actions.show_compiler_output.setChecked(True)
        self.actions.run.triggered.connect(self.CompilerConnector.compile)
        self.actions.open_config.triggered.connect(self.open_config)

        self.FSExplorer.open_file.connect(self.editor.open_file)
        self.editor.text_changed.connect(self.CompilerConnector.source_changed)
        self.CompilerConnector.document_changed.connect(self.PDFWidget.reload)
        state.main_file.Signal.connect(lambda s: self.CompilerConnector.set_fin(s))
        state.main_file.Signal.connect(lambda s: self.CompilerOptions.main_changed(s))
        state.main_file.Signal.connect(lambda s: self.CompilerConnector.set_fout(util.pdf_path(s)))
        state.main_file.Signal.connect(lambda s: self.PDFWidget.open(util.pdf_path(s)))


        # For now only display errors
        self.CompilerConnector.compilation_started.connect(self.CompilerOutput.insert_block)
        self.CompilerConnector.new_stderr.connect(self.CompilerOutput.append_to_block)

        # if config.get("Editor", "saveatrun", typ="bool"):
            # self.actions.run.triggered.connect(self.editor.save())

        # Display
        self.showMaximized()
        self.actions.layout_typewriter.trigger()

        logger.info("Gui ready")

    def set_layout_typewriter(self):
        """Set Typstwriter Layout: PDF on top, Editor on bottom."""
        # Vertical orientation
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        # Reorder widgets
        self.splitter.addWidget(self.Widgetidget_31)
        self.splitter.addWidget(self.Widgetidget)

    def set_layout_editorR(self): # noqa: N802
        """Set Layout to Editor right, PDF left."""
        # Horizontal orientation
        self.splitter.setOrientation(QtCore.Qt.Horizontal)

        # Reorder widgets
        self.splitter.addWidget(self.Widgetidget_31)
        self.splitter.addWidget(self.Widgetidget)

    def set_layout_editorL(self): # noqa: N802
        """Set Layout to Editor left, PDF right."""
        # Horizontal orientation
        self.splitter.setOrientation(QtCore.Qt.Horizontal)

        # Reorder widgets
        self.splitter.addWidget(self.Widgetidget)
        self.splitter.addWidget(self.Widgetidget_31)

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
        util.open_with_external_program(config.writepath)

    def closeEvent(self, event):  # noqa: N802
        """Handle close event."""
        s = self.editor.tryclose()
        if s:
            event.accept()
        else:
            event.ignore()


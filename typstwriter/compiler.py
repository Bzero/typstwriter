import time
import enum

from qtpy import QtCore

import logging
import configuration
import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


cmode = enum.Enum("compilation_mode", ["on_demand", "live"])


#TODO: use abc
class CompilerConnector_FS(QtCore.QObject): # noqa: N801
    """
    Abstract Class to build the interface between typstwriter and the typst backend using the filesystem for input and output.

    Functions:
    set_fin(fin): Set input file path
    set_fout(fout): Set output file path

    Slots:
    compile(): Instructs the CompilerConnector to (re)compile. Live variants may ignore these signal.
    input_changed(): Notifies the CompilerConnector that the input files have changed.

    Signals:
    compilation_finished(exit_code): Emitted when compilation finishes(regardsless of success)
    new_output_available(): Emitted when the output document has changed
    """

    compilation_started = QtCore.Signal()
    compilation_finished = QtCore.Signal()
    document_changed = QtCore.Signal()
    new_stderr = QtCore.Signal(str)
    new_stdout = QtCore.Signal(str)

    def __init__(self):
        """Init."""
        super().__init__()

    def set_fin(self, fin):
        """Set input file path."""
        pass

    def set_fout(self, fout):
        """Set output file path."""
        pass

    @QtCore.Slot()
    def compile(self):
        """Compile."""
        pass

    @QtCore.Slot()
    def source_changed(self):
        """Update source."""
        pass


class CompilerConnector_FS_onDemand(CompilerConnector_FS): # noqa: N801
    """CompilerConnector using the filesystem and compiling on demand."""

    cmode = cmode.on_demand

    def __init__(self, fin=None, fout=None):
        """Initialize the connector."""
        super().__init__()

        self.compiler = config.get("Compiler", "Name")
        self.subcommand = "compile"
        self.fin = fin
        self.fout = fout

        self.current_stdout = None
        self.current_stderr = None

        self.process = None
        self.recompile_scheduled = False

        self.compilation_finished.connect(self.check_recompilation)

    @QtCore.Slot()
    def compile(self):
        """Compile. If compilation is already ongoing, schedule recompilation."""
        if self.process is None:
            self.process = QtCore.QProcess()
            self.process.setProgram(self.compiler)
            self.process.setArguments([self.subcommand, self.fin, self.fout])
            self.process.finished.connect(self.compile_finished)
            self.process.readyReadStandardOutput.connect(self.handle_ready_stdout)
            self.process.readyReadStandardError.connect(self.handle_ready_stderr)

            self.current_stdout = ""
            self.current_stderr = ""

            self.compilation_started.emit()
            self.start_time = time.time()
            self.process.start()
        else:
            self.recompile_scheduled = True

    @QtCore.Slot(int)
    def compile_finished(self, exitcode):
        """Finalize the compilation and trigger apropriate signals."""
        self.end_time = time.time()

        self.current_stdout = None
        self.current_stderr = None

        self.process = None

        if exitcode == 0:
            logger.debug(f"Compiled {self.fin} successfully in {(self.end_time - self.start_time)*1000:.2f}ms.")
            self.document_changed.emit()
        else:
            logger.debug(f"Compiled {self.fin} with error in {(self.end_time - self.start_time)*1000:.2f}ms.")

        self.compilation_finished.emit()

    @QtCore.Slot()
    def check_recompilation(self):
        """Check if recompilation is scheduled."""
        if self.recompile_scheduled is True:
            self.recompile_scheduled = False
            self.compile()

    def handle_ready_stdout(self):
        """Store and Emit stdout as plain text signal."""
        stdout = bytes(self.process.readAllStandardOutput()).decode("utf8")
        self.current_stdout += stdout
        self.new_stdout.emit(stdout)

    def handle_ready_stderr(self):
        """Store and Emit stderr as plain text signal."""
        stderr = bytes(self.process.readAllStandardError()).decode("utf8")
        self.current_stderr += stderr
        self.new_stderr.emit(stderr)

    @QtCore.Slot(str)
    def set_fin(self, fin):
        """Set input file path."""
        if isinstance(fin, str):
            self.fin = fin

    def set_fout(self, fout):
        """Set output file path."""
        if isinstance(fout, str):
            self.fout = fout


# class CompilerConnector_FS_live(CompilerConnector_FS):
#
#     cmode = cmode.live
#
#     def __init__(self, fin, fout):
#         super().__init__()

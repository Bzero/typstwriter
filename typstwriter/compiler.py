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

text_compiling = "compiling ..."
text_compiled_erroniously = "compiled with errors"
text_compiled_successfully = "compiled successfully"


#TODO: use abc
class CompilerConnector_FS(QtCore.QObject): # noqa: N801
    """
    Abstract Class to build the interface between typstwriter and the typst backend using the filesystem for input and output.

    Functions:
    set_fin(fin): Set input file path
    set_fout(fout): Set output file path

    Slots:
    start(): Instructs the CompilerConnector to start its process. On demand variants may ignore this signal.
    stop(): Instructs the CompilerConnector to stop its process.
    compile(): Instructs the CompilerConnector to (re)compile. Live variants may ignore this signal.
    input_changed(): Notifies the CompilerConnector that the input files have changed.

    Signals:
    compilation_started(): Emitted when the compilation starts
    compilation_finished(): Emitted when compilation finishes(regardsless of success).
    document_changed(): Emitted when the output document has changed.
    new_stderr(str): Emitted when new stderr is available.
    new_stdout(str): Emitted when new stdout is available.
    """

    compilation_started = QtCore.Signal()
    compilation_finished = QtCore.Signal()
    document_changed = QtCore.Signal()
    new_stderr = QtCore.Signal(str)
    new_stdout = QtCore.Signal(str)

    def __init__(self, fin=None, fout=None):
        """Init."""
        super().__init__()

        self.compiler = config.get("Compiler", "Name")

        self.fin = fin
        self.fout = fout

        self.current_stdout = None
        self.current_stderr = None

        self.process = None

    @QtCore.Slot(str)
    def set_fin(self, fin):
        """Set input file path."""
        if isinstance(fin, str):
            self.fin = fin

    @QtCore.Slot(str)
    def set_fout(self, fout):
        """Set output file path."""
        if isinstance(fout, str):
            self.fout = fout

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

    @QtCore.Slot()
    def compile(self):
        """Compile."""
        pass

    @QtCore.Slot()
    def start(self):
        """Start."""
        pass

    @QtCore.Slot()
    def stop(self):
        """Stop."""
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
        super().__init__(fin, fout)

        self.subcommand = "compile"
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

            logger.debug("Compilation started.")
            self.compilation_started.emit()
            self.start_time = time.time()
            self.process.start()
        else:
            self.recompile_scheduled = True

    @QtCore.Slot()
    def stop(self):
        """Stop the compiler."""
        if self.process is not None:
            # Disconnect streams
            self.process.readyReadStandardOutput.disconnect(self.handle_ready_stdout)
            self.process.readyReadStandardError.disconnect(self.handle_ready_stderr)

            # Attempt to terminate the process.
            self.process.terminate()

            #TODO: kill process if it did not terminate

            self.recompile_scheduled = False
            self.compilation_finished(-1)
        else:
            logging.warning("Attempted to stop the compiler but it is not running.")


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


class CompilerConnector_FS_live(CompilerConnector_FS): # noqa: N801
    # """CompilerConnector using the filesystem and compiling live."""

    cmode = cmode.live

    def __init__(self, fin=None, fout=None):
        """Initialize the connector."""
        super().__init__(fin, fout)

        self.subcommand = "watch"
        self.new_stderr.connect(self.process_stderr)

    def start(self):
        """Start the compiler."""
        if self.process is None:
            self.process = QtCore.QProcess()
            self.process.setProgram(self.compiler)
            self.process.setArguments([self.subcommand, self.fin, self.fout])
            self.process.finished.connect(self.compile_finished)
            self.process.readyReadStandardOutput.connect(self.handle_ready_stdout)
            self.process.readyReadStandardError.connect(self.handle_ready_stderr)

            self.current_stdout = ""
            self.current_stderr = ""

            logger.debug("Compilation started.")
            self.compilation_started.emit()
            self.start_time = time.time()
            self.process.start()
        else:
            logging.warning("Attempted to start the compiler but it is already running.")

    def stop(self):
        """Stop the compiler."""
        if self.process is not None:
            # Disconnect streams
            self.process.readyReadStandardOutput.disconnect(self.handle_ready_stdout)
            self.process.readyReadStandardError.disconnect(self.handle_ready_stderr)

            # Attempt to terminate the process.
            self.process.terminate()

            #TODO: kill process if it did not terminate

            # Reset state
            self.current_stdout = None
            self.current_stderr = None
            self.process = None
        else:
            logging.warning("Attempted to stop the compiler but it is not running.")

    @QtCore.Slot(int)
    def compile_finished(self, exitcode):
        """Cleanup if the compiler stops unexpectedly."""
        logger.debug(f"Compiler stopped with exit code {exitcode}.")

        self.current_stdout = None
        self.current_stderr = None
        self.process = None

    def process_stderr(self, stderr):
        """Trigger appropriate signals and log when stderr is available."""
        if text_compiling in stderr:
            self.start_time = time.time()
            logger.debug("Compilation started.")
            self.compilation_started.emit()

        if text_compiled_erroniously in stderr:
            self.end_time = time.time()
            logger.debug(f"Compiled {self.fin} with error in {(self.end_time - self.start_time)*1000:.2f}ms.")
            self.compilation_finished.emit()

        if text_compiled_successfully in stderr:
            self.end_time = time.time()
            # delta_t = parse.search("compiled successfully in {:f}ms", stderr)[0]
            # logger.debug(f"Compiled {self.fin} successfully in {(delta_t):.2f}ms.")
            logger.debug(f"Compiled {self.fin} successfully in {(self.end_time - self.start_time)*1000:.2f}ms.")
            self.document_changed.emit()
            self.compilation_finished.emit()

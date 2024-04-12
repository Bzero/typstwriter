import time

from qtpy import QtCore

import enums

import logging
import configuration
import globalstate

logger = logging.getLogger(__name__)
config = configuration.Config
state = globalstate.State


text_compiling = "compiling ..."
text_compiled_erroniously = "compiled with errors"
text_compiled_successfully = "compiled successfully"


class CompilerConnector_FS(QtCore.QObject): # noqa: N801
    """
    Abstract Class to build the interface between typstwriter and the typst backend using the filesystem for input and output.

    Functions:
    set_fin(fin): Set input file path.
    set_fout(fout): Set output file path.

    Slots:
    start(): Instructs the CompilerConnector to start its process.
    stop(): Instructs the CompilerConnector to stop its process.
    source_changed(): Notify the compiler that the source changed.

    Signals:
    compilation_started(): Emitted when the compilation starts.
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
    def start(self):
        """Start."""
        pass

    @QtCore.Slot()
    def stop(self):
        """Stop."""
        pass

    @QtCore.Slot()
    def source_changed(self):
        """Notify the compiler that the source changed."""
        pass



class CompilerConnector_FS_onDemand(CompilerConnector_FS): # noqa: N801
    """CompilerConnector using the filesystem and compiling on demand."""

    compiler_mode = enums.compiler_mode.on_demand

    def __init__(self, fin=None, fout=None):
        """Initialize the connector."""
        super().__init__(fin, fout)

        self.subcommand = "compile"
        self.recompile_scheduled = False
        self.compilation_finished.connect(self.check_recompilation)

    @QtCore.Slot()
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
    """CompilerConnector using the filesystem and compiling live."""

    compiler_mode = enums.compiler_mode.live

    def __init__(self, fin=None, fout=None):
        """Initialize the connector."""
        super().__init__(fin, fout)

        self.subcommand = "watch"
        self.new_stderr.connect(self.process_stderr)

    @QtCore.Slot()
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


#TODO: This implementation is not optimal as it has a lot of repetition with CompilerConnector.
# Attempts to make it more consise by overriding __getattr__ were not successful because of the signals
class WrappedCompilerConnector(QtCore.QObject):
    """
    A CompilerConnector Wrapper.

    This class provides the same interface as a CompilerConnector but makes the compiler exchangable using set_compiler.
    This allows to connect signals and slots to this class and to swap out the actual CompilerConnector instance
    (e.g. to switch modes) without the need to reconnect all signals and slots to the new instance.
    """

    compilation_started = QtCore.Signal()
    compilation_finished = QtCore.Signal()
    document_changed = QtCore.Signal()
    new_stderr = QtCore.Signal(str)
    new_stdout = QtCore.Signal(str)

    def __init__(self, compiler_mode, fin=None, fout=None):
        """Init."""
        super().__init__()

        self.set_compiler(compiler_mode, fin, fout)

    def set_compiler(self, compiler_mode, fin=None, fout=None):
        """Create new compiler."""
        match compiler_mode:
            case enums.compiler_mode.on_demand:
                self.CompilerConnector = CompilerConnector_FS_onDemand(fin, fout)
                self.connect_signals()
                logging.debug(f"Created a new compiler with compiler mode {compiler_mode}.")
            case enums.compiler_mode.live:
                self.CompilerConnector = CompilerConnector_FS_live(fin, fout)
                self.connect_signals()
                logging.debug(f"Created a new compiler with compiler mode {compiler_mode}.")
            case _:
                #Use CompilerConnector_FS as a dummy which just ignores all start or compile commands
                self.CompilerConnector = CompilerConnector_FS(fin, fout)
                self.connect_signals()
                logging.warn(f"Attempted to create a new compiler but {compiler_mode} is not a valid compiler mode.")

    def switch_compiler(self, compiler_mode):
        """Switch to a new compiler while keeping fin and fout."""
        self.CompilerConnector.stop()
        self.disconnect_signals()
        fin = self.CompilerConnector.fin
        fout = self.CompilerConnector.fout
        self.set_compiler(compiler_mode, fin, fout)

    def restart_compiler(self):
        """Restart the compiler."""
        compiler_mode = self.CompilerConnector.compiler_mode
        self.switch_compiler(compiler_mode)

    def connect_signals(self):
        """Connect wrapper signals to compiler signals."""
        self.CompilerConnector.compilation_started.connect(self.relay_compilation_started)
        self.CompilerConnector.compilation_finished.connect(self.relay_compilation_finished)
        self.CompilerConnector.document_changed.connect(self.relay_document_changed)
        self.CompilerConnector.new_stderr.connect(self.relay_new_stderr)
        self.CompilerConnector.new_stdout.connect(self.relay_new_stdout)

    def disconnect_signals(self):
        """Disconnect wrapper signals from compiler signals."""
        self.CompilerConnector.compilation_started.disconnect(self.relay_compilation_started)
        self.CompilerConnector.compilation_finished.disconnect(self.relay_compilation_finished)
        self.CompilerConnector.document_changed.disconnect(self.relay_document_changed)
        self.CompilerConnector.new_stderr.disconnect(self.relay_new_stderr)
        self.CompilerConnector.new_stdout.disconnect(self.relay_new_stdout)

    @QtCore.Slot(str)
    def set_fin(self, fin):
        """Relay set_fin to compiler."""
        self.CompilerConnector.set_fin(fin)

    @QtCore.Slot(str)
    def set_fout(self, fout):
        """Relay set_fout to compiler."""
        self.CompilerConnector.set_fout(fout)

    @QtCore.Slot()
    def start(self):
        """Relay start to compiler."""
        self.CompilerConnector.start()

    @QtCore.Slot()
    def stop(self):
        """Relay stop to compiler."""
        self.CompilerConnector.stop()

    @QtCore.Slot()
    def source_changed(self):
        """Relay source_changed to compiler."""
        self.CompilerConnector.source_changed()

    def relay_compilation_started(self):
        """Relay compilation_started to compiler."""
        self.compilation_started.emit()

    def relay_compilation_finished(self):
        """Relay compilation_finished to compiler."""
        self.compilation_finished.emit()

    def relay_document_changed(self):
        """Relay document_changed to compiler."""
        self.document_changed.emit()

    def relay_new_stderr(self, stderr):
        """Relay new_stderr to compiler."""
        self.new_stderr.emit(stderr)

    def relay_new_stdout(self, stderr):
        """Relay new_stdout to compiler."""
        self.new_stdout.emit(stderr)

    # def __getattr__(self, name):
    #     return getattr(self.CompilerConnector, name)

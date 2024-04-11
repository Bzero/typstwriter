import sys
import signal
import os
import logging


os.environ["QT_API"] = "pyside6"
import qtpy  # noqa: E402


def setup_logger(level):
    """Set the main logger up."""
    fmt = "{levelname:8} {asctime:30} {filename:20} {funcName:20} line {lineno:<4d}: {message}"
    formatter = logging.Formatter(fmt=fmt, style="{")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log = logging.root
    log.addHandler(handler)
    if level in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
        log.setLevel(level)
    else:
        log.setLevel("INFO")


def main():
    """Run Typstwriter."""
    setup_logger(os.environ.get('LOGLEVEL'))
    logger = logging.getLogger(__name__)

    logger.info("Typstwriter started")

    # Initialise Config
    logger.info("Reading Config")
    import configuration # noqa: F401

    # Initialise State
    logger.info("Initialising State")
    import globalstate  # noqa: F401

    # With logging, config and state set up, import the main GUI
    import mainwindow

    # Make sure the application can receive SIGINT
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Initialize the application
    logger.info("Initialize Application")
    app = qtpy.QtWidgets.QApplication(sys.argv)
    main = mainwindow.MainWindow()
    main.show()

    # Run he application
    logger.info("Run Application")
    app.exec_()


if __name__ == "__main__":
    main()

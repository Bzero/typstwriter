import sys
import signal
import os


os.environ["QT_API"] = "pyside6"
import qtpy  # noqa: E402 RUF100


def main():
    """Run Typstwriter."""
    # Initialise logging
    from typstwriter import logging

    logging.setup_logger(os.environ.get("LOGLEVEL"))
    logger = logging.getLogger(__name__)
    logger.debug("Logging initialized")

    # Parse Arguments
    logger.debug("Parse Arguments")
    from typstwriter import arguments  # noqa: F401

    # Start Typstwriter
    logger.info("Typstwriter started")

    # Initialise Config
    logger.info("Reading Config")
    from typstwriter import configuration  # noqa: F401

    # Initialise State
    logger.info("Initialising State")
    from typstwriter import globalstate  # noqa: F401

    # With logging, config and state set up, import the main GUI
    from typstwriter import mainwindow

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

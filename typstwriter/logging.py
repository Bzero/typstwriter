import logging
# See https://python.readthedocs.io/en/stable/howto/logging-cookbook.html#use-of-alternative-formatting-styles


class Message:
    """A logger message."""

    def __init__(self, fmt, args):
        """Init."""
        self.fmt = fmt
        self.args = args

    def __str__(self):
        """Format string."""
        return self.fmt.format(*self.args)


class StyleAdapter(logging.LoggerAdapter):
    """Curly brace style adapter."""

    def __init__(self, logger, extra=None):
        """Init."""
        super().__init__(logger, extra or {})

    def log(self, level, msg, *args, **kwargs):
        """Log if enabled."""
        if self.isEnabledFor(level):
            msg, kwargs = self.process(msg, kwargs)
            self.logger._log(level, Message(msg, args), (), stacklevel=2, **kwargs)


def setup_logger(level):
    """Set the main logger up."""
    fmt = "{levelname:8} {asctime:26} {filename:20} {funcName:26} line {lineno:<4d}: {message}"
    formatter = logging.Formatter(fmt=fmt, style="{")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log = logging.root
    log.addHandler(handler)
    if level in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
        log.setLevel(level)
    else:
        log.setLevel("INFO")


def getLogger(name):  # noqa N802
    """Get brace style logger."""
    return StyleAdapter(logging.getLogger(name))

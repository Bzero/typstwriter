from typstwriter import logging
from re import match


def test_Message():
    """Test logging.Message."""
    assert str(logging.Message("A string: {}", ["Test"])) == "A string: Test"
    assert str(logging.Message("A debug string: {!r}", ["Test"])) == "A debug string: 'Test'"
    assert str(logging.Message("{} + {} = {}", [2, 2, 4])) == "2 + 2 = 4"


def test_StyleAdapter(caplog):
    """Test logging.StyleAdapter."""
    sa = logging.getLogger("test")

    sa.log(100, "A test")
    assert "A test" in caplog.text
    caplog.clear()

    sa.log(100, "A test with arguments: {}, {}", [1, 2, 3], "0")
    assert "A test with arguments: [1, 2, 3], 0" in caplog.text
    caplog.clear()

    sa.log(0, "A test")
    assert not caplog.text
    caplog.clear()


# This function does not use the caplog fixture directly because caplog injects
# its own handler in the logging and overrides the custom formatting.
# Instead the whole output is captured.
def test_setup_logger(capsys):
    """Test logging.getLogger."""
    logging.setup_logger("WARNING")
    logger = logging.getLogger("test")

    logger.critical("A test")
    (out, err) = capsys.readouterr()
    assert match(r"CRITICAL\s+\S+ \S+\s+test_logging.py\s+test_setup_logger\s+line \d+\s+: A test", err)

    logger.info("A test")
    (out, err) = capsys.readouterr()
    assert not out
    assert not err

    logging.setup_logger(level="Invalid")
    logger = logging.getLogger("test")

    logger.info("A test")
    (out, err) = capsys.readouterr()
    assert match(r"INFO\s+\S+ \S+\s+test_logging.py\s+test_setup_logger\s+line \d+\s+: A test", err)

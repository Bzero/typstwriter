import pytest

from typstwriter import globalstate


class TestSingleState:
    """Test globalstate.SingleState."""

    def test_Value_assignment(self, qtbot):
        """Make sure Value can be assigned."""
        state = globalstate.SingleState("Test")
        assert state.Value == "Test"

    def test_Signal_emitted(self, qtbot):
        """Make sure Value assignment triggers Signal."""
        state = globalstate.SingleState("")
        with qtbot.waitSignal(state.Signal) as blocker:
            state.Value = "Test"
        assert blocker.args == ["Test"]

    def test_AttributeError(self, qtbot):
        """Make sure other fields trigger AttributeError."""
        state = globalstate.SingleState("")
        with pytest.raises(AttributeError, match="The only valid attributes are 'Value' and 'Signal'."):
            state.Test = "Test"


class TestGloalState:
    """Test globalstate.GlobalState."""

    def test_members(self, qtbot):
        """Test if all required members are present."""
        state = globalstate.GlobalState()

        assert hasattr(state, "working_directory")
        assert hasattr(state, "compiler_running")
        assert hasattr(state, "main_file")
        assert hasattr(state, "compiler_mode")

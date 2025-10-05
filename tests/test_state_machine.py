from eloGraf.state_machine import DictationStateMachine, IconState


def test_toggle_cycle():
    sm = DictationStateMachine()
    assert sm.toggle() == "begin"
    sm.set_ready()
    assert sm.toggle() == "suspend"
    sm.set_suspended()
    assert sm.toggle() == "resume"

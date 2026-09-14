import pytest

from pygame_toolkit import Cooldown, Timer


def test_timer_one_shot():
    calls = []
    t = Timer(1.0, lambda: calls.append(1))
    assert not t.update(0.5)
    assert t.progress == 0.5 and t.remaining == 0.5
    assert t.update(0.5)
    assert t.done and not t.running
    assert not t.update(10)  # doesn't fire again
    assert calls == [1]


def test_timer_repeat_catches_up_on_big_dt():
    calls = []
    t = Timer(0.5, lambda: calls.append(1), repeat=True)
    t.update(1.6)
    assert len(calls) == 3
    assert t.elapsed == pytest.approx(0.1)
    assert t.running and not t.done


def test_timer_callback_can_stop_repeat():
    t = Timer(0.1, repeat=True)
    t.on_done = t.stop
    t.update(1.0)
    assert not t.running


def test_timer_pause_resume_restart():
    t = Timer(1.0, autostart=False)
    assert not t.update(5)
    t.start()
    t.update(0.4)
    t.pause()
    t.update(5)
    assert t.elapsed == pytest.approx(0.4)
    t.resume()
    assert t.update(0.6)
    t.restart()
    assert t.elapsed == 0 and t.running and not t.done


def test_timer_bad_args():
    with pytest.raises(ValueError):
        Timer(-1)
    with pytest.raises(ValueError):
        Timer(0, repeat=True)


def test_cooldown_use_and_progress():
    cd = Cooldown(1.0)
    assert cd.ready() and cd.progress == 1.0
    assert cd.use()
    assert not cd.use()
    cd.update(0.25)
    assert cd.progress == pytest.approx(0.25)
    assert cd.remaining == pytest.approx(0.75)
    cd.update(1)
    assert cd.ready()


def test_cooldown_start_not_ready_and_reset():
    cd = Cooldown(3, start_ready=False)
    assert not cd.ready()
    cd.reset()
    assert cd.ready()
    with pytest.raises(ValueError):
        Cooldown(-0.1)

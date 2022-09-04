from sys import exc_info

from yieldfrom import yield_from


class _TestException(Exception):
    pass


def generator(state=None):
    yield 1
    try:
        yield 2
    except _TestException:
        yield -1
    try:
        yield 3
    except GeneratorExit:
        state.exiting = True
        raise
    yield (yield 4)


def delegating_generator(state=None):
    for v, s, t in yield_from(generator(state)):
        try:
            s((yield v))
        except:
            if not t(*exc_info()):
                raise

def test_yield():
    assert list(generator()) == list(delegating_generator())


def test_send():
    generator_instance = delegating_generator()
    assert next(generator_instance) == 1
    assert next(generator_instance) == 2
    assert next(generator_instance) == 3
    assert next(generator_instance) == 4
    assert generator_instance.send(0) == 0


def test_throw():
    generator_instance = delegating_generator()
    assert next(generator_instance) == 1
    assert next(generator_instance) == 2
    assert generator_instance.throw(_TestException, None, None) == -1
    exception = _TestException('hi')
    try:
        generator_instance.throw(type(exception), exception, None)
    except _TestException as error:
        assert error is exception
    try:
        next(generator_instance)
        assert False, 'next() after uncaught throw should have raised'
    except StopIteration:
        pass


def test_close():
    class State(object):
        def __init__(self):
            self.exiting = False
    state = State()
    generator_instance = delegating_generator(state)
    assert next(generator_instance) == 1
    assert next(generator_instance) == 2
    assert next(generator_instance) == 3
    generator_instance.close()
    assert state.exiting
    try:
        next(generator_instance)
        assert False, 'next() after un-suppressed close should have raised'
    except StopIteration:
        pass


if __name__ == '__main__':
    test_yield()
    test_send()
    test_throw()

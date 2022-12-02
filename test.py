from copy import copy
from itertools import count
from sys import exc_info, version_info

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
    for value, handle_send, handle_throw in yield_from(generator(state)):
        sent = None
        try:
            sent = yield value
        except:
            if not handle_throw(*exc_info()):
                raise
        handle_send(sent)


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


generator_return = 'return'
if version_info < (3, 3):
    generator_return = 'raise StopIteration'

exec('''
def returning_generator():
    yield 1
    yield 2
    yield 3
    '''+generator_return+'''(123)


def delegating_returning_generator():
    wrapper = yield_from(returning_generator())
    for v, s, t in wrapper:
        try:
            s((yield v))
        except:
            if not t(*exc_info()):
                raise
    '''+generator_return+'''(wrapper.result)
''')


def test_return():
    generator_instance = delegating_returning_generator()
    assert next(generator_instance) == 1
    assert next(generator_instance) == 2
    assert next(generator_instance) == 3
    try:
        next(generator_instance)
    except StopIteration as stop:
        assert stop.args[0] == 123


def test_no_result_until_done():
    instance = yield_from(range(1))
    try:
        instance.result
        assert False, '.result should not exist yet'
    except AttributeError:
        pass
    next(instance)
    try:
        instance.result
        assert False, '.result should not exist yet'
    except AttributeError:
        pass
    try:
        next(instance)
    except StopIteration:
        assert instance.result is None


def test_repr():
    def g():
        yield
    instance = yield_from(g())
    basic_repr = repr(instance)
    repr_set = {basic_repr}

    next(instance)
    assert repr(instance) == basic_repr
    instance.handle_send(None)
    assert repr(instance) == basic_repr

    instance.handle_send(0)
    send_pending_repr = repr(instance)
    assert send_pending_repr not in repr_set
    repr_set.add(send_pending_repr)

    instance.handle_send(1)
    different_send_pending_repr = repr(instance)
    assert different_send_pending_repr not in repr_set
    repr_set.add(different_send_pending_repr)

    instance.handle_throw(KeyError, None, None)
    throw_pending_repr = repr(instance)
    assert throw_pending_repr not in repr_set
    repr_set.add(throw_pending_repr)

    instance.handle_throw(ValueError, None, None)
    different_throw_pending_repr = repr(instance)
    assert different_throw_pending_repr not in repr_set
    repr_set.add(different_throw_pending_repr)

    instance._next = instance._default_next

    try:
        next(instance)
        assert False, 'next() should have raised'
    except StopIteration:
        pass
    basic_with_result = repr(instance)
    assert basic_with_result not in repr_set
    repr_set.add(basic_with_result)

    instance.handle_send(0)
    send_pending_with_result = repr(instance)
    assert send_pending_with_result not in repr_set
    repr_set.add(send_pending_with_result)

    instance.handle_send(1)
    different_send_pending_with_result = repr(instance)
    assert different_send_pending_with_result not in repr_set
    repr_set.add(different_send_pending_with_result)

    instance.handle_throw(KeyError, None, None)
    throw_pending_with_result = repr(instance)
    assert throw_pending_with_result not in repr_set
    repr_set.add(throw_pending_with_result)

    instance.handle_throw(ValueError, None, None)
    different_throw_pending_with_result = repr(instance)
    assert different_throw_pending_with_result not in repr_set
    repr_set.add(different_throw_pending_with_result)


def test_get_set_state_without_result():
    instance = yield_from(count(start=1))
    assert copy(instance)._next == instance._next
    assert copy(instance)._iterator == instance._iterator
    assert copy(instance)._default_next == instance._default_next


def test_get_set_state_with_result():
    class I(object):
        def __iter__(self):
            return self
        def __next__(self):
            raise StopIteration('boom')
        next = __next__  # for Python 2
    instance = yield_from(I())
    try:
        next(instance)
        assert False, 'next() should have raised StopIteration'
    except StopIteration:
        pass
    assert copy(instance)._next == instance._next
    assert copy(instance)._iterator == instance._iterator
    assert copy(instance)._default_next == instance._default_next
    assert copy(instance).result == instance.result


def test_get_set_state_preserves_send():
    class I(object):
        def __init__(self):
            self.state = 'initial'
        def __iter__(self):
            return self
        def __next__(self):
            return 'from next'
        next = __next__  # for Python 2
        def send(self, value):
            self.state = value
            return 'from send'
    iterator = I()
    instance = yield_from(iterator)
    instance.handle_send('sent')
    assert iterator.state == 'initial'
    assert next(copy(instance))[0] == 'from send'
    assert iterator.state == 'sent'


def test_get_set_state_preserves_throw():
    class I(object):
        def __init__(self):
            self.state = 'initial'
        def __iter__(self):
            return self
        def __next__(self):
            return 'from next'
        next = __next__  # for Python 2
        def throw(self, exception_type, exception=None, traceback=None):
            self.state = exception_type
            return 'from throw'
    iterator = I()
    instance = yield_from(iterator)
    instance.handle_throw(KeyError, None, None)
    assert iterator.state == 'initial'
    assert next(copy(instance))[0] == 'from throw'
    assert iterator.state == KeyError


if __name__ == '__main__':
    test_yield()
    test_send()
    test_throw()
    test_close()
    test_return()
    test_no_result_until_done()
    test_repr()
    test_get_set_state_without_result()
    test_get_set_state_with_result()
    test_get_set_state_preserves_send()
    test_get_set_state_preserves_throw()

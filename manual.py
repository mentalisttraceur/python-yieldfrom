# Copyright 2019 Alexander Kozhevnikov <mentalisttraceur@gmail.com>
# SPDX-License-Identifier: 0BSD

"""Use context managers with a function instead of a statement.

Provides a minimal and portable interface for using context
managers with all the advantages of functions over syntax.
"""

from sys import exc_info as _exc_info

from generatoremulator import Generator as _Generator
from raise_ import raise_ as _raise
from yieldfrom import yield_from as _yield_from


__all__ = ('with_',)
__version__ = '1.1.0'


class _OldStyleClass:
    pass


_OldStyleClassInstance = type(_OldStyleClass())
del _OldStyleClass


def _type(obj):
    if isinstance(obj, _OldStyleClassInstance):
        return obj.__class__
    return type(obj)


def with_(manager, action):
    """Execute an action within the scope of a context manager.

    Arguments:
        manager: The context manager instance to use.
        action: The callable to execute. Must accept the `as` value
            of the context manager as the only positional argument.

    Returns:
        Any: Return value of the executed action.
        None: If the manager suppresses an exception from the action.

    Raises:
        Any: If raised by calling the action and not suppressed by the
            manager, or if raised by the manager, or if the manager
            does not implement the context manager protocol correctly.
    """
    exit_ = _type(manager).__exit__
    value = _type(manager).__enter__(manager)
    try:
        result = action(value)
    except:
        if not exit_(manager, *_exc_info()):
            raise
        return None
    exit_(manager, None, None, None)
    return result


class iwith(_Generator):
    __slots__ = ()

    def __init__(self, manager, action):
        _Generator.__init__(self)
        self._locals = (manager, action)

    def _next(self, sent, exception_type, exception, traceback):
        if exception_type is not None:
            _raise(exception, traceback)
        if not self._yielded:
            self._enter_and_delegate()
        return self._yield_from.__next__()

    def _enter_and_delegate(self):
        manager, action = self._locals
        exit_ = type(manager).__exit__
        exitor = _Exitor(manager, exit_)
        error_exitor = _ErrorExitor(manager, exit_)
        def delegate(_):
            yield_from = _yield_from(action(value))
            self._yield_from = _YieldFromWith(yield_from, exitor, error_exitor)
        value = type(manager).__enter__(manager)
        with_(error_exitor, delegate)
        if self._yield_from is None:
            raise StopIteration


class _YieldFromWith(object):
    __slots__ = ('_yield_from', '_exitor', '_error_exitor')

    def __init__(self, yield_from, exitor, error_exitor):
        self._exitor = exitor
        self._error_exitor = error_exitor
        self._yield_from = yield_from

    def __next__(self):
        yield_from = self._yield_from
        return with_(self._exitor, lambda _: yield_from.__next__())

    def handle_send(self, value):
        yield_from = self._yield_from
        return with_(self._exitor, lambda _: yield_from.handle_send(value))

    def handle_throw(self, type, exception, traceback):
        yield_from = self._yield_from
        return with_(self._error_exitor,
            lambda _: yield_from.handle_throw(type, exception, traceback))

    def __reduce__(self):
        args = (self._yield_from, self._exitor, self._error_exitor)
        return (type(self), args)


class _Exitor(object):
    __slots__ = ('_manager', '_exit')

    def __init__(self, manager, exit_):
        self._manager = manager
        self._exit = exit_

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, traceback):
        if exception_type is None:
            return True
        if issubclass(exception_type, StopIteration):
            self._exit(self._manager, None, None, None)
            return False
        return self._exit(self._manager, exception_type, exception, traceback)

    def __reduce__(self):
        return (type(self), (self._manager, self._exit))


class _ErrorExitor(_Exitor):
    __slots__ = ()

    def __exit__(self, exception_type, exception, traceback):
        if exception_type is None:
            return True
        return self._exit(self._manager, exception_type, exception, traceback)

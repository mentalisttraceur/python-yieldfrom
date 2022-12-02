# SPDX-License-Identifier: 0BSD
# Copyright 2022 Alexander Kozhevnikov <mentalisttraceur@gmail.com>

"""A robust implementation of ``yield from`` behavior.

Allows transpilers, backpilers, and code that needs
to be portable to minimal or old Pythons to replace

    yield from ...

with

    for value, handle_send, handle_throw in yield_from(...):
        sent = None
        try:
            sent = yield value
        except:
            if not handle_throw(*sys.exc_info()):
                raise
        handle_send(sent)

and

    result = yield from ...

with

    wrapper = yield_from(...)
    for value, handle_send, handle_throw in wrapper:
        sent = None
        try:
            sent = yield value
        except:
            if not handle_throw(*sys.exc_info()):
                raise
        handle_send(sent)
    result = wrapper.result
"""


__version__ = '1.2.0'
__all__ = ('yield_from',)


class yield_from(object):
    """Implementation of the logic that ``yield from`` adds around ``yield``."""

    __slots__ = ('_iterator', '_next', '_default_next', 'result')

    def __init__(self, iterable):
        """Initializes the yield_from instance.

        Arguments:
            iterable: The iterable to yield from and forward to.
        """
        # Mutates:
        #     self._iterator: Holds the iterator from iter(iterable).
        #     self._next: Prepares to use built-in function next in __next__
        #         for the first iteration on the iterator.
        #     self._default_next: Saves initial self._next tuple for reuse.
        self._iterator = iter(iterable)
        self._next = self._default_next = next, (self._iterator,)

    def __repr__(self):
        """Represent the yield_from instance as an unambiguous string."""
        name = type(self).__name__
        iterator = repr(self._iterator)
        if self._next is not self._default_next:
            next_ = ' next=' + repr(self._next)
        else:
            next_ = ''
        try:
            result = self.result
            finished = True
        except AttributeError:
            finished = False
        if finished:
            result = ' result=' + repr(result)
        else:
            result = ''
        return '<' + name + ' ' + iterator + next_ + result + '>'

    def __iter__(self):
        """Return the yield_from instance, which is itself an iterator."""
        return self

    def __next__(self):
        """Do the next iteration of ``yield from`` on the wrapped iterator.

        Returns:
            Any: The next value from the iterator.

        Raises:
            StopIteration: If the iterator is exhausted.
            Any: If the iterator raises an error.

        Mutates:
            self.result: Set to the result of the ``yield from`` if
                the wrapped iterator is exhausted by this iteration.
        """
        # Mutates:
        #     self._next: Resets to default, in case handle_send
        #         or handle_throw changed it for this iteration.
        next_, arguments = self._next
        self._next = self._default_next
        try:
            value = next_(*arguments)
        except StopIteration, stop:
            self.result = _yield_from_value(stop)
            raise
        return value, self.handle_send, self.handle_throw

    next = __next__  # Python 2 used ``next`` instead of ``__next__``.

    def handle_send(self, value):
        """Handle a send method call for a yield.

        Arguments:
            value: The value sent through the yield.

        Raises:
            AttributeError: If the iterator has no send method.
        """
        # Mutates:
        #     self._next: If value is not None, prepares to use the
        #         iterator's send attribute instead of the built-in
        #         function next in the next iteration of __next__.
        if value is not None:
            self._next = self._iterator.send, (value,)

    def handle_throw(self, type, exception, traceback):
        """Handle a throw method call for a yield.

        Arguments:
            type: The type of the exception thrown through the yield.
                If this is GeneratorExit, the iterator will be closed
                by callings its close attribute if it has one.
            exception: The exception thrown through the yield.
            traceback: The traceback of the exception thrown through the yield.

        Returns:
            bool: Whether the exception will be forwarded to the iterator.
                If this is false, you should bubble up the exception.
                If this is true, the exception will be thrown into the
                iterator at the start of the next iteration, and will
                either be handled or bubble up at that time.

        Raises:
            TypeError: If type is not a class.
            Any: If raised by the close function on the iterator.
        """
        # Mutates:
        #     self._next: If type was not GeneratorExit and the iterator
        #         has a throw attribute, prepares to use that attribute
        #         instead of the built-in function next in the next
        #         iteration of __next__.
        iterator = self._iterator

        if issubclass(type, GeneratorExit):
            try:
                close = iterator.close
            except AttributeError:
                return False
            close()
            return False

        try:
            throw = iterator.throw
        except AttributeError:
            return False

        self._next = throw, (type, exception, traceback)
        return True

    def __getstate__(self):
        """Gets the state of this yield_from instance.

        Returns:
            A state object that makes it possible to pickle or copy
            this yield_from instance provided that the delegated-to
            iterator can be pickled or copied.
        """
        try:
            result = self.result
        except AttributeError:
            return (self._iterator, self._next, self._default_next)
        return (self._iterator, self._next, self._default_next, result)

    def __setstate__(self, state):
        """Sets the state of this yield_from instance.

        Arguments:
            state: A state object such as returned by __getstate__.

        Raises:
            ValueError: If the state tuple is the wrong size.
        """
        # Mutates:
        #     self._iterator: Restores from state.
        #     self._next: Restores from state.
        #     self._default_next: Restores from state.
        #     self.result: Restores from state.
        if len(state) > 3:
            self._iterator, self._next, self._default_next, self.result = state
            return
        self._iterator, self._next, self._default_next = state
        try:
            del self.result
        except AttributeError:
            pass


def _yield_from_value(exception):
    """Get the ``yield from`` return value from a StopIteration instance.

    Arguments:
        exception: An instance of StopIteration.

    Returns:
        Any: The value carried by the StopIteration instances. This is
             normally exception.value, but if that attribute is not
             available this function will return exception.args[0], or
             None if the exception also has no arguments.
    """
    try:
        return exception.value
    except AttributeError:
        try:
            return exception.args[0]
        except IndexError:
            return None


# Portability to some minimal Python implementations:
try:
    yield_from.__name__
except AttributeError:
    yield_from.__name__ = 'yield_from'

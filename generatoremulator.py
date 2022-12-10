from raise_ import raise_ as _raise


# These error messages were copied from CPython - where Python 3
# vs Python 2 error messages differ, Python 3's message was used:
_PREMATURE_SEND = "can't send non-None value to a just-started generator"
_REDUNDANT_THROW_VALUE = 'instance exception may not have a separate value'
_NOT_AN_EXCEPTION = 'exceptions must derive from BaseException'
_NOT_A_TRACEBACK = 'throw() third argument must be a traceback object'
_IGNORED_EXIT = 'generator ignored GeneratorExit'


class Generator(object):
    __slots__ = (
        '_yielded', '_closed', '_yield_from', '_locals', '__weakref__',
    )

    def __init__(self):
        self._yielded = False
        self._closed = False
        self._yield_from = None
        self._locals = None

    def __iter__(self):
        return self

    def __getstate__(self):
        return (self._yielded, self._closed, self._yield_from, self._locals)

    def __setstate__(self, state):
        self._yielded, self._closed, self._yield_from, self._locals = state

    def _next(self, sent, exception_type, exception, traceback):
        raise NotImplementedError

    def __next__(self):
        return self.send(None)

    next = __next__  # Python 2 used ``next`` instead of ``__next__``.

    def send(self, value):
        if self._closed:
            raise StopIteration
        if value is not None and not self._yielded:
            raise TypeError(_PREMATURE_SEND)
        try:
            if self._yield_from is not None:
                self._yield_from.handle_send(value)
            result = self._next(value, None, None, None)
        except:
            self._closed = True
            raise
        self._yielded = True
        return result

    def throw(self, type_, value=None, traceback=None):
        yield_from = self._yield_from
        if yield_from is not None and not self._closed:
            try:
                if yield_from.handle_throw(type_, value, traceback):
                    return self._next(None, None, None, None)
            except:
                self._closed = True
                raise
        if isinstance(type_, BaseException):
            if value is not None:
                raise TypeError(_REDUNDANT_THROW_VALUE)
            value = type_
            type_ = type(value)
        elif (not isinstance(type_, type)
        or    not issubclass(type_, BaseException)):
            raise TypeError(_NOT_AN_EXCEPTION)
        elif not isinstance(value, type_):
            if value is None:
                value = type_()
            elif isinstance(value, tuple):
                value = type_(*value)
            else:
                value = type_(value)
        if self._closed or not self._yielded:
            self._closed = True
            _raise(value, traceback)
        try:
            return self._next(None, type_, value, traceback)
        except:
            self._closed = True
            raise

    def close(self):
        if not self._yielded:
            self._closed = True
        if not self._closed:
            try:
                self.throw(GeneratorExit)
            except (GeneratorExit, StopIteration):
                return
            self._closed = True
            raise RuntimeError(_IGNORED_EXIT)

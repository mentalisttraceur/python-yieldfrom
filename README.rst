Python ``yield from`` as an Iterator
====================================

A robust implementation of ``yield from`` behavior. Good for transpilers,
backpilers, and code that needs to be portable to minimal or old Pythons.

This implementation avoids the complexity and overheads of typical
``yield from`` backports - the tradeoff is that it is less obvious
and does not resemble ``yield from`` syntax.


Versioning
----------

This library's version numbers follow the `SemVer 2.0.0
specification <https://semver.org/spec/v2.0.0.html>`_.


Installation
------------

::

    pip install yield-from-as-an-iterator


Usage
-----

Import ``yield_from``:

.. code:: python

    from yieldfrom import yield_from

Replace ``yield from ...`` with:

.. code:: python

    wrapper = yield_from(...)
    for value in wrapper:
        sent = None
        try:
            sent = yield value
        except:
            if not wrapper.handle_throw(*sys.exc_info()):
                raise
        wrapper.handle_send(sent)

To replace ``result = yield from ...``, just
add this right after the above loop:

.. code:: python

    result = wrapper.result


Portability
-----------

Portable to all releases of Python 3, and releases
of Python 2 starting with 2.2.

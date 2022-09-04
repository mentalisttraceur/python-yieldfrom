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

    for value, handle_send, handle_throw in yield_from(...):
        try:
            handle_send(yield value)
        except:
            if not handle_throw(*sys.exc_info()):
                raise


Portability
-----------

Portable to all releases of Python 3, and releases
of Python 2 starting with 2.5.

On Pythons older than 2.5, or on any other Python that
doesn't implement `PEP-342 <https://peps.python.org/pep-0342>`_:

1. This will still import without errors.
2. The functions will execute correctly
   if ``GeneratorExit`` is polyfilled.

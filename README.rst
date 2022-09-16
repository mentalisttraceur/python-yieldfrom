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

Replace ``result = yield from ...`` with:

.. code:: python

    wrapper = yield_from(...)
    for value, handle_send, handle_throw in wrapper:
        try:
            handle_send(yield value)
        except:
            if not handle_throw(*sys.exc_info()):
                raise
    result = wrapper.result


Portability
-----------

Portable to all releases of Python 3, and releases
of Python 2 starting with 2.6.

On older or more minimal Pythons, the code will still import, so
long as the right variant of the module file was chosen (because
Python below 2.6 did not have ``except ... as ...`` syntax), and
should work so long as the following are built-in or polyfilled:

1. The ``next`` function (just the one-argument form)
   (added in Python 2.6).
2. The ``GeneratorExit`` exception (added in Python 2.5).
3. The ``iter`` function (just the one-argument form)
   (added in Python 2.2).
4. The ``StopIteration`` exception (added in Python 2.2).

As you go lower, especially below 2.2, you will run into the problem
of the language itself not implementing the same interfaces that are
faithfully implemented in this module, because:

* generators only gained the ability to move data bidirectionally,
  and the ``.send`` and ``.throw`` methods to do so, in Python 2.5,
* generators and ``yield`` were only added in Python 2.2, and
* the iterator protocol was only added in Python 2.1.

But, so long as you have objects which implement those interfaces,
this module should help you get ``yield from`` behavior with them.

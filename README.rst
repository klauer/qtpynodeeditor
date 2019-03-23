===============================
qtpynodeeditor
===============================

A work-in-progress PyQt5/PySide port of [NodeEditor](https://github.com/paceholder/nodeeditor).

.. image:: https://img.shields.io/travis/klauer/qtpynodeeditor.svg
        :target: https://travis-ci.org/klauer/qtpynodeeditor

.. image:: https://img.shields.io/pypi/v/qtpynodeeditor.svg
        :target: https://pypi.python.org/pypi/qtpynodeeditor


Python Qt node editor

Documentation
-------------

Sphinx-generated documentation for this project can be found here:
https://klauer.github.io/qtpynodeeditor/


Requirements
------------

* Python 3.6+
* qtpy
* PyQt5 / PySide

Installation
------------

```bash
$ conda create -n node -c conda-forge python=3.6 pyqt5 qt qtpy
$ source activate node
$ git clone https://github.com/klauer/qtpynodeeditor
$ cd qtpynodeeditor
$ python setup.py install
```

Running the Tests
-----------------
::

  $ python run_tests.py

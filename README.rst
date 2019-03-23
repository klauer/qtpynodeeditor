.. image:: https://img.shields.io/travis/klauer/qtpynodeeditor.svg
        :target: https://travis-ci.org/klauer/qtpynodeeditor

.. image:: https://img.shields.io/pypi/v/qtpynodeeditor.svg
        :target: https://pypi.python.org/pypi/qtpynodeeditor

===============================
qtpynodeeditor
===============================

Python Qt node editor

Pure Python port of `NodeEditor <https://github.com/paceholder/nodeeditor>`_,
supporting PyQt5 and PySide through `qtpy <https://github.com/spyder-ide/qtpy>`_.

Requirements
------------

* Python 3.6+
* qtpy
* PyQt5 / PySide


Documentation
-------------

`Sphinx-generated documentation <https://klauer.github.io/qtpynodeeditor/>`_


Screenshots
-----------

`Style example <https://github.com/klauer/qtpynodeeditor/blob/master/qtpynodeeditor/examples/style.py>`_

.. image:: https://raw.githubusercontent.com/klauer/qtpynodeeditor/assets/screenshots/style.png

`Calculator example <https://github.com/klauer/qtpynodeeditor/blob/master/qtpynodeeditor/examples/calculator.py>`_

.. image:: https://raw.githubusercontent.com/klauer/qtpynodeeditor/assets/screenshots/calculator.png


Installation
------------
::

   $ conda create -n node -c conda-forge python=3.6 pyqt5 qt qtpy
   $ source activate node
   $ git clone https://github.com/klauer/qtpynodeeditor
   $ cd qtpynodeeditor
   $ python setup.py install

Running the Tests
-----------------
::

   $ python run_tests.py

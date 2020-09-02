=================
 Release History
=================

v0.2.0 (2020-09-02)
===================

Enhancements
------------
* Verify connection compatibility with :class:`~qtpynodeeditor.NodeDataType`
  (`#43 <https://github.com/klauer/qtpynodeeditor/pull/43>`_)

Fixes
-----
* Do not allow for cyclic connections in the scene (`#35 <https://github.com/klauer/qtpynodeeditor/issues/43>`_)
* :class:`~qtpynodeeditor.NodeDataModel` ``input_connection_created`` now only
  called once (`#27 <https://github.com/klauer/qtpynodeeditor/issues/43>`_)
* Incorrect connections in calculator example (`#38
  <https://github.com/klauer/qtpynodeeditor/issues/43>`_)
* Fix filename globbing in open/save file dialogs.

API Changes
-----------
* :class:`~qtpynodeeditor.Connection` property ``output_node`` should be used in favor of the
  now-deprecated ``node`` property.
* New connection failure exceptions: :class:`~qtpynodeeditor.ConnectionCycleFailure` and
  :class:`~qtpynodeeditor.ConnectionDataTypeFailure`.
* Fixed deprecated ``QFontMetrics.width``.

Contributors
------------

* @tfarago (`#43 <https://github.com/klauer/qtpynodeeditor/pull/43>`_, `#28 <https://github.com/klauer/qtpynodeeditor/pull/43>`_)

Thanks to those who reported issues and contributed to this release.


v0.1.0 (2020-03-29)
===================

Now available on conda-forge::

    conda install -c conda-forge qtpynodeeditor

Fixes
-----
* Packaging of style configuration

Development
-----------
* Testing and supporting pyqt5 / PySide2
* Miscellaneous cleaning and fixing, along with better continuous integration
  testing

API Changes
-----------
* New signature for ``node_context_menu`` signal: ``(node, scene_pos, screen_pos)``.


v0.0.1 (2020-03-29)
===================

Initial test release of qtpynodeeditor.

Now available on PyPI::

    pip install qtpynodeeditor

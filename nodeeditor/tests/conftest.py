import pytest
from pytestqt.qt_compat import qt_api

import tempfile
import logging

from qtpy.QtCore import QObject, Signal, Slot


logger = logging.getLogger(__name__)


@pytest.yield_fixture(scope='session')
def application(qapp_args):
    app = qt_api.QApplication.instance()
    if app is None:
        app = qt_api.QApplication(*qapp_args)
    yield app

import inspect
from collections import namedtuple
from typing import Optional

from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import QWidget

from . import style as style_module
from .base import Serializable
from .enums import ConnectionPolicy, NodeValidationState, PortType
from .port import Port

NodeDataType = namedtuple('NodeDataType', ('id', 'name'))


class NodeData:
    """
    Class represents data transferred between nodes.

    The actual data is stored in subtypes
    """

    data_type = NodeDataType(None, None)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.data_type is None:
            raise ValueError('Subclasses must set the `data_type` attribute')

    def same_type(self, other) -> bool:
        """
        Is another NodeData instance of the same type?

        Parameters
        ----------
        other : NodeData

        Returns
        -------
        value : bool
        """
        return self.data_type.id == other.data_type.id


class NodeDataModel(QObject, Serializable):
    name: Optional[str] = None
    caption: Optional[str] = None
    caption_visible = True
    num_ports = {PortType.input: 1,
                 PortType.output: 1,
                 }

    # data_updated and data_invalidated refer to the port index that has
    # changed:
    data_updated = Signal(int)
    data_invalidated = Signal(int)

    computing_started = Signal()
    computing_finished = Signal()
    embedded_widget_size_updated = Signal()

    def __init__(self, style=None, parent=None):
        super().__init__(parent=parent)
        if style is None:
            style = style_module.default_style
        self._style = style

    def __init_subclass__(cls, verify=True, **kwargs):
        super().__init_subclass__(**kwargs)
        # For all subclasses, if no name is defined, default to the class name
        if cls.name is None:
            cls.name = cls.__name__
        if cls.caption is None and cls.caption_visible:
            cls.caption = cls.name

        num_ports = cls.num_ports
        if isinstance(num_ports, property):
            # Dynamically defined - that's OK, but we can't verify it.
            return

        if verify:
            cls._verify()

    @classmethod
    def _verify(cls):
        '''
        Verify the data model won't crash in strange spots
        Ensure valid dictionaries:
            - num_ports
            - data_type
            - port_caption
            - port_caption_visible
        '''
        num_ports = cls.num_ports
        if isinstance(num_ports, property):
            # Dynamically defined - that's OK, but we can't verify it.
            return

        assert set(num_ports.keys()) == {'input', 'output'}

        # TODO while the end result is nicer, this is ugly; refactor away...

        def new_dict(value):
            return {
                PortType.input: {i: value
                                 for i in range(num_ports[PortType.input])
                                 },
                PortType.output: {i: value
                                  for i in range(num_ports[PortType.output])
                                  },
            }

        def get_default(attr, default, valid_type):
            current = getattr(cls, attr, None)
            if current is None:
                # Unset - use the default
                return default

            if valid_type is not None:
                if isinstance(current, valid_type):
                    # Fill in the dictionary with the user-provided value
                    return current

            if attr == 'data_type' and inspect.isclass(current):
                if issubclass(current, NodeData):
                    return current.data_type

            if inspect.ismethod(current) or inspect.isfunction(current):
                raise ValueError('{} should not be a function; saw: {}\n'
                                 'Did you forget a @property decorator?'
                                 ''.format(attr, current))

            try:
                type(default)(current)
            except TypeError:
                raise ValueError('{} is of an unexpected type: {}'
                                 ''.format(attr, current)) from None

            # Fill in the dictionary with the given value
            return current

        def fill_defaults(attr, default, valid_type=None):
            if isinstance(getattr(cls, attr, None), dict):
                return

            default = get_default(attr, default, valid_type)
            if default is None:
                raise ValueError(f'Cannot leave {attr} unspecified')

            setattr(cls, attr, new_dict(default))

        fill_defaults('port_caption', '')
        fill_defaults('port_caption_visible', False)
        fill_defaults('data_type', None, valid_type=NodeDataType)

        reasons = []
        for attr in ('data_type', 'port_caption', 'port_caption_visible'):
            try:
                dct = getattr(cls, attr)
            except AttributeError:
                reasons.append('{} is missing dictionary: {}'
                               ''.format(cls.__name__, attr))
                continue

            if isinstance(dct, property):
                continue

            for port_type in {'input', 'output'}:
                if port_type not in dct:
                    if num_ports[port_type] == 0:
                        dct[port_type] = {}
                    else:
                        reasons.append('Port type key {}[{!r}] missing'
                                       ''.format(attr, port_type))
                        continue

                for i in range(num_ports[port_type]):
                    if i not in dct[port_type]:
                        reasons.append('Port key {}[{!r}][{}] missing'
                                       ''.format(attr, port_type, i))

        if reasons:
            reason_text = '\n'.join(f'* {reason}'
                                    for reason in reasons)
            raise ValueError(
                'Verification of NodeDataModel class failed:\n{}'
                ''.format(reason_text)
            )

    @property
    def style(self):
        'Style collection for drawing this data model'
        return self._style

    def save(self) -> dict:
        """
        Subclasses may implement this to save additional state for
        pickling/saving to JSON.

        Returns
        -------
        value : dict
        """
        return {}

    def restore(self, doc: dict):
        """
        Subclasses may implement this to load additional state from
        pickled or saved-to-JSON data.

        Parameters
        ----------
        value : dict
        """
        return {}

    def __setstate__(self, doc: dict):
        """
        Set the state of the NodeDataModel

        Parameters
        ----------
        doc : dict
        """
        self.restore(doc)
        return doc

    def __getstate__(self) -> dict:
        """
        Get the state of the NodeDataModel for saving/pickling

        Returns
        -------
        value : QJsonObject
        """
        doc = {'name': self.name}
        doc.update(**self.save())
        return doc

    @property
    def data_type(self):
        """
        Data type placeholder - to be implemented by subclass.

        Parameters
        ----------
        port_type : PortType
        port_index : int

        Returns
        -------
        value : NodeDataType
        """
        raise NotImplementedError(f'Subclass {self.__class__.__name__} must '
                                  f'implement `data_type`')

    def port_out_connection_policy(self, port_index: int) -> ConnectionPolicy:
        """
        Port out connection policy

        Parameters
        ----------
        port_index : int

        Returns
        -------
        value : ConnectionPolicy
        """
        return ConnectionPolicy.many

    @property
    def node_style(self) -> style_module.NodeStyle:
        """
        Node style

        Returns
        -------
        value : NodeStyle
        """
        return self._style.node

    def set_in_data(self, node_data: NodeData, port: Port):
        """
        Triggers the algorithm; to be overridden by subclasses

        Parameters
        ----------
        node_data : NodeData
        port : Port
        """
        ...

    def out_data(self, port: int) -> NodeData:
        """
        Out data

        Parameters
        ----------
        port : int

        Returns
        -------
        value : NodeData
        """
        ...

    def embedded_widget(self) -> QWidget:
        """
        Embedded widget

        Returns
        -------
        value : QWidget
        """
        ...

    def resizable(self) -> bool:
        """
        Resizable

        Returns
        -------
        value : bool
        """
        return False

    def validation_state(self) -> NodeValidationState:
        """
        Validation state

        Returns
        -------
        value : NodeValidationState
        """
        return NodeValidationState.valid

    def validation_message(self) -> str:
        """
        Validation message

        Returns
        -------
        value : str
        """
        return ""

    def painter_delegate(self):
        """
        Painter delegate

        Returns
        -------
        value : NodePainterDelegate
        """
        return None

    def input_connection_created(self, connection):
        """
        Input connection created

        Parameters
        ----------
        connection : Connection
        """
        ...

    def input_connection_deleted(self, connection):
        """
        Input connection deleted

        Parameters
        ----------
        connection : Connection
        """
        ...

    def output_connection_created(self, connection):
        """
        Output connection created

        Parameters
        ----------
        connection : Connection
        """
        ...

    def output_connection_deleted(self, connection):
        """
        Output connection deleted

        Parameters
        ----------
        connection : Connection
        """
        ...

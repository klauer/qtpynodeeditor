import contextlib
import logging
import threading

from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import QApplication, QLabel, QLineEdit, QWidget

import qtpynodeeditor as nodeeditor
from qtpynodeeditor import (NodeData, NodeDataModel, NodeDataType,
                            NodeValidationState, Port, PortType)
from qtpynodeeditor.type_converter import TypeConverter


class DecimalData(NodeData):
    'Node data holding a decimal (floating point) number'
    data_type = NodeDataType("decimal", "Decimal")

    def __init__(self, number: float = 0.0):
        self._number = number
        self._lock = threading.RLock()

    @property
    def lock(self):
        return self._lock

    @property
    def number(self) -> float:
        'The number data'
        return self._number

    def number_as_text(self) -> str:
        'Number as a string'
        return '%g' % self._number


class IntegerData(NodeData):
    'Node data holding an integer value'
    data_type = NodeDataType("integer", "Integer")

    def __init__(self, number: int = 0):
        self._number = number
        self._lock = threading.RLock()

    @property
    def lock(self):
        return self._lock

    @property
    def number(self) -> int:
        'The number data'
        return self._number

    def number_as_text(self) -> str:
        'Number as a string'
        return str(self._number)


class MathOperationDataModel(NodeDataModel):
    caption_visible = True
    num_ports = {
        'input': 2,
        'output': 1,
    }
    port_caption_visible = True
    data_type = DecimalData.data_type

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number1 = None
        self._number2 = None
        self._result = None
        self._validation_state = NodeValidationState.warning
        self._validation_message = 'Uninitialized'

    @property
    def caption(self):
        return self.name

    def _check_inputs(self):
        number1_ok = (self._number1 is not None and
                      self._number1.data_type.id in ('decimal', 'integer'))
        number2_ok = (self._number2 is not None and
                      self._number2.data_type.id in ('decimal', 'integer'))

        if not number1_ok or not number2_ok:
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Missing or incorrect inputs"
            self._result = None
            self.data_updated.emit(0)
            return False

        self._validation_state = NodeValidationState.valid
        self._validation_message = ''
        return True

    @contextlib.contextmanager
    def _compute_lock(self):
        if not self._number1 or not self._number2:
            raise RuntimeError('inputs unset')

        with self._number1.lock:
            with self._number2.lock:
                yield

        self.data_updated.emit(0)

    def out_data(self, port: int) -> NodeData:
        '''
        The output data as a result of this calculation

        Parameters
        ----------
        port : int

        Returns
        -------
        value : NodeData
        '''
        return self._result

    def set_in_data(self, data: NodeData, port: Port):
        '''
        New data at the input of the node

        Parameters
        ----------
        data : NodeData
        port_index : int
        '''
        if port.index == 0:
            self._number1 = data
        elif port.index == 1:
            self._number2 = data

        if self._check_inputs():
            with self._compute_lock():
                self.compute()

    def validation_state(self) -> NodeValidationState:
        return self._validation_state

    def validation_message(self) -> str:
        return self._validation_message

    def compute(self):
        ...


class AdditionModel(MathOperationDataModel):
    name = "Addition"

    def compute(self):
        self._result = DecimalData(self._number1.number + self._number2.number)


class DivisionModel(MathOperationDataModel):
    name = "Division"
    port_caption = {'input': {0: 'Dividend',
                              1: 'Divisor',
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        if self._number2.number == 0.0:
            self._validation_state = NodeValidationState.error
            self._validation_message = "Division by zero error"
            self._result = None
        else:
            self._validation_state = NodeValidationState.valid
            self._validation_message = ''
            self._result = DecimalData(self._number1.number / self._number2.number)


class ModuloModel(MathOperationDataModel):
    name = 'Modulo'
    data_type = IntegerData.data_type
    port_caption = {'input': {0: 'Dividend',
                              1: 'Divisor',
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        if self._number2.number == 0.0:
            self._validation_state = NodeValidationState.error
            self._validation_message = "Division by zero error"
            self._result = None
        else:
            self._result = IntegerData(self._number1.number % self._number2.number)


class MultiplicationModel(MathOperationDataModel):
    name = 'Multiplication'
    port_caption = {'input': {0: 'A',
                              1: 'B',
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        self._result = DecimalData(self._number1.number * self._number2.number)


class NumberSourceDataModel(NodeDataModel):
    name = "NumberSource"
    caption_visible = False
    num_ports = {PortType.input: 0,
                 PortType.output: 1,
                 }
    port_caption = {'output': {0: 'Result'}}
    data_type = DecimalData.data_type

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number = None
        self._line_edit = QLineEdit()
        self._line_edit.setValidator(QDoubleValidator())
        self._line_edit.setMaximumSize(self._line_edit.sizeHint())
        self._line_edit.textChanged.connect(self.on_text_edited)
        self._line_edit.setText("0.0")

    @property
    def number(self):
        return self._number

    def save(self) -> dict:
        'Add to the JSON dictionary to save the state of the NumberSource'
        doc = super().save()
        if self._number:
            doc['number'] = self._number.number
        return doc

    def restore(self, state: dict):
        'Restore the number from the JSON dictionary'
        try:
            value = float(state["number"])
        except Exception:
            ...
        else:
            self._number = DecimalData(value)
            self._line_edit.setText(self._number.number_as_text())

    def out_data(self, port: int) -> NodeData:
        '''
        The data output from this node

        Parameters
        ----------
        port : int

        Returns
        -------
        value : NodeData
        '''
        return self._number

    def embedded_widget(self) -> QWidget:
        'The number source has a line edit widget for the user to type in'
        return self._line_edit

    def on_text_edited(self, string: str):
        '''
        Line edit text has changed

        Parameters
        ----------
        string : str
        '''
        try:
            number = float(self._line_edit.text())
        except ValueError:
            self._data_invalidated.emit(0)
        else:
            self._number = DecimalData(number)
            self.data_updated.emit(0)


class NumberDisplayModel(NodeDataModel):
    name = "NumberDisplay"
    data_type = DecimalData.data_type
    caption_visible = False
    num_ports = {PortType.input: 1,
                 PortType.output: 0,
                 }
    port_caption = {'input': {0: 'Number'}}

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number = None
        self._label = QLabel()
        self._label.setMargin(3)
        self._validation_state = NodeValidationState.warning
        self._validation_message = 'Uninitialized'

    def set_in_data(self, data: NodeData, port: Port):
        '''
        New data propagated to the input

        Parameters
        ----------
        data : NodeData
        int : int
        '''
        self._number = data
        number_ok = (self._number is not None and
                     self._number.data_type.id in ('decimal', 'integer'))

        if number_ok:
            self._validation_state = NodeValidationState.valid
            self._validation_message = ''
            self._label.setText(self._number.number_as_text())
        else:
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Missing or incorrect inputs"
            self._label.clear()

        self._label.adjustSize()

    def embedded_widget(self) -> QWidget:
        'The number display has a label'
        return self._label


class SubtractionModel(MathOperationDataModel):
    name = "Subtraction"
    port_caption = {'input': {0: 'Minuend',
                              1: 'Subtrahend'
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        self._result = DecimalData(self._number1.number - self._number2.number)


def integer_to_decimal_converter(data: IntegerData) -> DecimalData:
    '''
    integer_to_decimal_converter

    Parameters
    ----------
    data : NodeData

    Returns
    -------
    value : NodeData
    '''
    return DecimalData(float(data.number))


def decimal_to_integer_converter(data: DecimalData) -> IntegerData:
    '''
    Convert from DecimalDat to IntegerData

    Parameters
    ----------
    data : DecimalData

    Returns
    -------
    value : IntegerData
    '''
    return IntegerData(int(data.number))


def main(app):
    registry = nodeeditor.DataModelRegistry()

    models = (AdditionModel, DivisionModel, ModuloModel, MultiplicationModel,
              NumberSourceDataModel, SubtractionModel, NumberDisplayModel)
    for model in models:
        registry.register_model(model, category='Operations',
                                style=None)

    dec_converter = TypeConverter(DecimalData.data_type, IntegerData.data_type, decimal_to_integer_converter)
    int_converter = TypeConverter(IntegerData.data_type, DecimalData.data_type, integer_to_decimal_converter)
    registry.register_type_converter(DecimalData.data_type, IntegerData.data_type, dec_converter)
    registry.register_type_converter(IntegerData.data_type, DecimalData.data_type, int_converter)

    scene = nodeeditor.FlowScene(registry=registry)

    view = nodeeditor.FlowView(scene)
    view.setWindowTitle("Calculator example")
    view.resize(800, 600)
    view.show()

    inputs = []
    node_add = scene.create_node(AdditionModel)
    node_sub = scene.create_node(SubtractionModel)
    node_mul = scene.create_node(MultiplicationModel)
    node_div = scene.create_node(DivisionModel)
    node_mod = scene.create_node(ModuloModel)

    for node_operation in (node_add, node_sub, node_mul, node_div, node_mod):
        node_a = scene.create_node(NumberSourceDataModel)
        node_a.model.embedded_widget().setText('1.0')
        inputs.append(node_a)

        node_b = scene.create_node(NumberSourceDataModel)
        node_b.model.embedded_widget().setText('2.0')
        inputs.append(node_b)

        scene.create_connection(node_a[PortType.output][0],
                                node_operation[PortType.input][0],
                                )

        scene.create_connection(node_b[PortType.output][0],
                                node_operation[PortType.input][1],
                                )

        node_display = scene.create_node(NumberDisplayModel)

        scene.create_connection(node_operation[PortType.output][0],
                                node_display[PortType.input][0],
                                )

    try:
        scene.auto_arrange(nodes=inputs, layout='bipartite')
    except ImportError:
        ...

    return scene, view, [node_a, node_b]


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    app = QApplication([])
    scene, view, nodes = main(app)
    view.show()
    app.exec_()

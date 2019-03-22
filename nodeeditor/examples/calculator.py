import logging
import contextlib
import threading

from qtpy.QtWidgets import (QWidget, QLineEdit, QApplication, QLabel)
from qtpy.QtGui import QDoubleValidator

import nodeeditor
from nodeeditor import (NodeData, NodeDataModel, NodeDataType, PortType,
                        NodeValidationState, PortIndex
                        )


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
        '''
        The number

        Returns
        -------
        value : float
        '''
        return self._number

    def number_as_text(self) -> str:
        '''
        number_as_text

        Returns
        -------
        value : str
        '''
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

    def number(self) -> int:
        '''
        The number

        Returns
        -------
        value : int
        '''
        return self._number

    def number_as_text(self) -> str:
        '''
        number_as_text

        Returns
        -------
        value : str
        '''
        return str(self._number)


class MathOperationDataModel(NodeDataModel):
    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number1 = None
        self._number2 = None
        self._result = None
        self.model_validation_state = NodeValidationState.warning
        self.model_validation_error = 'Uninitialized'

    def caption(self) -> str:
        return self.name

    def caption_visible(self) -> bool:
        return True

    def n_ports(self, port_type: PortType) -> int:
        '''
        n_ports

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : int
        '''
        if port_type==PortType.input:
            return 2
        elif port_type == PortType.output:
            return 1

        raise ValueError('Unknown port type')

    def port_caption_visible(self, port_type: PortType, port_index: PortIndex) -> bool:
        '''
        port_caption_visible

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : bool
        '''
        return True

    def _check_inputs(self):
        if self._number1 is None or self._number2 is None:
            self.model_validation_state = NodeValidationState.warning
            self.model_validation_error = "Missing or incorrect inputs"
            self._result = None
            return False

        self.model_validation_state = NodeValidationState.valid
        self.model_validation_error = ''
        return True

    @contextlib.contextmanager
    def _compute_lock(self):
        if not self._number1 or not self._number2:
            raise RuntimeError('inputs unset')

        with self._number1.lock:
            with self._number2.lock:
                yield

    def data_type(self, port_type: PortType, port_index: PortIndex) -> NodeDataType:
        '''
        data_type

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : NodeDataType
        '''
        return DecimalData.data_type

    def out_data(self, port: PortIndex) -> NodeData:
        '''
        out_data

        Parameters
        ----------
        port : PortIndex

        Returns
        -------
        value : NodeData
        '''
        return self._result

    def set_in_data(self, data: NodeData, port_index: PortIndex):
        '''
        set_in_data

        Parameters
        ----------
        data : NodeData
        port_index : PortIndex
        '''
        if port_index == 0:
            self._number1 = data
        elif port_index == 1:
            self._number2 = data

        self.compute()

    def validation_state(self) -> NodeValidationState:
        '''
        validation_state

        Returns
        -------
        value : NodeValidationState
        '''
        return self.model_validation_state

    def validation_message(self) -> str:
        '''
        validation_message

        Returns
        -------
        value : str
        '''
        return self.model_validation_error

    def compute(self):
        ...


class AdditionModel(MathOperationDataModel):
    name = "Addition"

    def compute(self):
        if self._check_inputs():
            with self._compute_lock():
                self._result = DecimalData(self._number1.number +
                                           self._number2.number)

        self.data_updated.emit(0)


class DivisionModel(MathOperationDataModel):
    name = "Division"

    def port_caption(self, port_type: PortType, port_index: PortIndex) -> str:
        '''
        port_caption

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : str
        '''
        if port_type==PortType.input:
            if port_index == 0:
                return 'Dividend'
            elif port_index == 1:
                return 'Divisor'
        elif port_type == PortType.output:
            return 'Result'


    def compute(self):
        if self._check_inputs():
            with self._compute_lock():
                if self._number2.number == 0.0:
                    self.model_validation_state = NodeValidationState.error
                    self.model_validation_error = "Division by zero error"
                    self._result = None
                else:
                    self.model_validation_state = NodeValidationState.valid
                    self.model_validation_error = ''
                    self._result = DecimalData(self._number1.number/self._number2.number)

        self.data_updated.emit(0)


class ModuloModel(MathOperationDataModel):
    name = 'Modulo'

    def port_caption(self, port_type: PortType, port_index: PortIndex) -> str:
        '''
        port_caption

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : str
        '''
        if port_type==PortType.input:
            if port_index == 0:
                return 'Dividend'
            elif port_index == 1:
                return 'Divisor'
        elif port_type == PortType.output:
            return 'Result'

    def data_type(self, port_type: PortType, port_index: PortIndex) -> NodeDataType:
        '''
        data_type

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : NodeDataType
        '''
        return IntegerData.data_type

    def compute(self):
        if self._check_inputs():
            with self._compute_lock():
                if self._number2.number == 0.0:
                    self.model_validation_state = NodeValidationState.error
                    self.model_validation_error = "Division by zero error"
                    self._result = None
                else:
                    self._result = IntegerData(self._number1.number % self._number2.number)

        self.data_updated.emit(0)


class MultiplicationModel(MathOperationDataModel):
    name = 'Multiplication'

    def port_caption(self, port_type: PortType, port_index: PortIndex) -> str:
        '''
        port_caption

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : str
        '''
        if port_type==PortType.input:
            if port_index == 0:
                return 'A'
            elif port_index == 1:
                return 'B'
        elif port_type == PortType.output:
            return 'Result'

    def compute(self):
        if self._check_inputs():
            with self._compute_lock():
                self._result = DecimalData(self._number1.number * self._number2.number)

        self.data_updated.emit(0)


class NumberSourceDataModel(NodeDataModel):
    name = "NumberSource"

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number = None
        self._line_edit = QLineEdit()
        self._line_edit.setValidator(QDoubleValidator())
        self._line_edit.setMaximumSize(self._line_edit.sizeHint())
        self._line_edit.textChanged.connect(self.on_text_edited)
        self._line_edit.setText("0.0")

    def caption(self) -> str:
        return "Number Source"

    def caption_visible(self) -> bool:
        return False

    def save(self) -> dict:
        '''
        save

        Returns
        -------
        value : dict
        '''
        doc = super().save()
        if self._number:
            doc['number'] = self._number.number
        return doc

    def restore(self, p: dict):
        '''
        restore

        Parameters
        ----------
        p : dict
        '''
        try:
            value = float(p["number"])
        except Exception:
            ...
        else:
            self._number = DecimalData(value)
            self._line_edit.setText(self._number.number_as_text())

    def n_ports(self, port_type: PortType) -> int:
        '''
        n_ports

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : int
        '''
        if port_type == PortType.input:
            return 0
        elif port_type == PortType.output:
            return 1
        raise ValueError('Unknown port type')

    def data_type(self, port_type: PortType, port_index: PortIndex) -> NodeDataType:
        '''
        data_type

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : NodeDataType
        '''
        return DecimalData.data_type

    def out_data(self, port: PortIndex) -> NodeData:
        '''
        out_data

        Parameters
        ----------
        port : PortIndex

        Returns
        -------
        value : NodeData
        '''
        return self._number

    def set_in_data(self, data: NodeData, int: int):
        '''
        set_in_data

        Parameters
        ----------
        data : NodeData
        int : int
        '''
        ...

    def embedded_widget(self) -> QWidget:
        '''
        embedded_widget

        Returns
        -------
        value : QWidget
        '''
        return self._line_edit

    def on_text_edited(self, string: str):
        '''
        on_text_edited

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

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number = None
        self._label = QLabel()
        self._label.setMargin(3)

    def caption_visible(self) -> bool:
        return False

    def n_ports(self, port_type: PortType) -> int:
        '''
        n_ports

        Parameters
        ----------
        port_type : PortType

        Returns
        -------
        value : int
        '''
        if port_type == PortType.input:
            return 1
        elif port_type == PortType.output:
            return 0
        raise ValueError('Unknown port type')

    def data_type(self, port_type: PortType, port_index: PortIndex) -> NodeDataType:
        '''
        data_type

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : NodeDataType
        '''
        return DecimalData.data_type

    def set_in_data(self, data: NodeData, int: int):
        '''
        set_in_data

        Parameters
        ----------
        data : NodeData
        int : int
        '''
        self._number = data

        if self._number:
            self.model_validation_state = NodeValidationState.valid
            self.model_validation_error = ''
            self._label.setText(self._number.number_as_text())
        else:
            self.model_validation_state = NodeValidationState.warning
            self.model_validation_error = "Missing or incorrect inputs"
            self._label.clear()

        self._label.adjustSize()

    def embedded_widget(self) -> QWidget:
        '''
        embedded_widget

        Returns
        -------
        value : QWidget
        '''
        return self._label


class SubtractionModel(MathOperationDataModel):
    name = "Subtraction"

    def port_caption(self, port_type: PortType, port_index: PortIndex) -> str:
        '''
        port_caption

        Parameters
        ----------
        port_type : PortType
        port_index : PortIndex

        Returns
        -------
        value : str
        '''
        if port_type==PortType.input:
            if port_index == 0:
                return 'Minuend'
            elif port_index == 1:
                return 'Subtrahend'
        elif port_type == PortType.output:
            return 'Result'

    def compute(self):
        if self._check_inputs():
            with self._compute_lock():
                self.model_validation_state = NodeValidationState.valid
                self.model_validation_error = ''
                self._result = DecimalData(self._number1.number-self._number2.number)

        self.data_updated.emit(0)


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


def main():
    logging.basicConfig(level='DEBUG')
    app = QApplication([])

    registry = nodeeditor.DataModelRegistry()

    models = (AdditionModel, DivisionModel, ModuloModel, MultiplicationModel,
              NumberSourceDataModel, SubtractionModel, NumberDisplayModel)
    for model in models:
        registry.register_model(model, category='Operations',
                                style=None)

    registry.register_type_converter(DecimalData, IntegerData,
                                     decimal_to_integer_converter)
    registry.register_type_converter(IntegerData, DecimalData,
                                     decimal_to_integer_converter)

    scene = nodeeditor.FlowScene(registry=registry)

    view = nodeeditor.FlowView(scene)
    view.setWindowTitle("Calculator example")
    view.resize(800, 600)
    view.show()

    node_a = scene.create_node(NumberSourceDataModel)
    node_a.data.embedded_widget().setText('1.0')

    node_b = scene.create_node(NumberSourceDataModel)
    node_b.data.embedded_widget().setText('2.0')
    node_add = scene.create_node(AdditionModel)
    node_sub = scene.create_node(SubtractionModel)
    node_mul = scene.create_node(MultiplicationModel)
    node_div = scene.create_node(DivisionModel)
    node_mod = scene.create_node(ModuloModel)

    for node_operation in (node_add, node_sub, node_mul, node_div, node_mod):
        scene.create_connection(
            node_out=node_a, port_index_out=0,
            node_in=node_operation, port_index_in=0,
            converter=None
        )

        scene.create_connection(
            node_out=node_b, port_index_out=0,
            node_in=node_operation, port_index_in=1,
            converter=None
        )

        node_display = scene.create_node(NumberDisplayModel)

        scene.create_connection(
            node_out=node_operation, port_index_out=0,
            node_in=node_display, port_index_in=0,
            converter=None
        )


    app.exec_()


if __name__ == '__main__':
    main()

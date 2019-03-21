import logging
import contextlib
import threading

from qtpy.QtWidgets import QWidget, QLineEdit, QApplication
from qtpy.QtGui import QDoubleValidator

import nodeeditor
from nodeeditor import (NodeData, NodeDataModel, NodeDataType, PortType,
                        NodeValidationState, PortIndex
                        )


class DecimalData(NodeData):
    def __init__(self, number: float=0.0):
        '''
        decimal_data

        Parameters
        ----------
        number : float
        '''
        self._number = number
        self._lock = threading.RLock()

    @property
    def lock(self):
        return self._lock

    @staticmethod
    def type() -> NodeDataType:
        '''
        type

        Returns
        -------
        value : NodeDataType
        '''
        return NodeDataType("decimal", "Decimal")

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
    def __init__(self, number: int=0):
        '''
        integer_data

        Parameters
        ----------
        number : int
        '''
        self._number = number
        self._lock = threading.RLock()

    @property
    def lock(self):
        return self._lock

    @staticmethod
    def type() -> NodeDataType:
        '''
        type

        Returns
        -------
        value : NodeDataType
        '''
        return NodeDataType("integer", "Integer")

    def number(self) -> int:
        '''
        number

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
        self._result = None
        self.model_validation_state = NodeValidationState.Warning
        self.model_validation_error = 'Uninitialized'

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
        if port_type==PortType.In:
            return 2
        elif port_type == PortType.Out:
            return 1

        raise ValueError('Unknown port type')

    def _check_inputs(self):
        if self._number1 is None or self._number2 is None:
            self.model_validation_state = NodeValidationState.Warning
            self.model_validation_error = "Missing or incorrect inputs"
            self._result = None
            return False

        self.model_validation_state = NodeValidationState.Valid
        self.model_validation_error = ''
        return True

    @contextlib.contextmanager
    def _compute_lock(self):
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
        return DecimalData().type()

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
        if (port_index==0):
            self._number1 = data
        elif port_index == 1:
            self._number2 = data

        self.compute()

    def embedded_widget(self) -> QWidget:
        '''
        embedded_widget

        Returns
        -------
        value : QWidget
        '''
        return None

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
    def caption(self) -> str:
        return "Addition"

    @staticmethod
    def name() -> str:
        return "Addition"

    def compute(self):
        if self._check_inputs():
            with self._compute_lock():
                self._result = DecimalData(self._number1.number +
                                           self._number2.number)

        self.data_updated.emit(0)


class DivisionModel(MathOperationDataModel):
    def caption(self) -> str:
        '''
        caption

        Returns
        -------
        value : str
        '''
        return "Division"

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
        if port_type==PortType.In:
            if port_index == 0:
                return 'Dividend'
            elif port_index == 1:
                return 'Divisor'
        elif port_type == PortType.Out:
            return 'Result'

    @staticmethod
    def name() -> str:
        '''
        name

        Returns
        -------
        value : str
        '''
        return "Division"

    def compute(self):
        if self._check_inputs():
            with self._compute_lock():
                if self._number2.number == 0.0:
                    self.model_validation_state = NodeValidationState.Error
                    self.model_validation_error = "Division by zero error"
                    self._result = None
                else:
                    self.model_validation_state = NodeValidationState.Valid
                    self.model_validation_error = ''
                    self._result = DecimalData(self._number1.number/self._number2.number)

        self.data_updated.emit(0)


class ModuloModel(NodeDataModel):
    def caption(self) -> str:
        '''
        caption

        Returns
        -------
        value : str
        '''
        return "Modulo"

    def caption_visible(self) -> bool:
        '''
        caption_visible

        Returns
        -------
        value : bool
        '''
        return True

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
        if port_type==PortType.In:
            if port_index == 0:
                return 'Dividend'
            elif port_index == 1:
                return 'Divisor'
        elif port_type == PortType.Out:
            return 'Result'

    @staticmethod
    def name() -> str:
        '''
        name

        Returns
        -------
        value : str
        '''
        return "Modulo"

    def save(self) -> dict:
        '''
        save

        Returns
        -------
        value : dict
        '''
        doc = super().save()
        doc['name'] = self.name()
        return doc

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
        if port_type==PortType.In:
            return 2
        elif port_type == PortType.Out:
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
        return IntegerData().type()

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

    def set_in_data(self, data: NodeData, port_index: int):
        '''
        set_in_data

        Parameters
        ----------
        data : NodeData
        port_index : int
        '''
        if (port_index==0):
            self._number1 = data
        else:
            self._number2 = data

        if self._check_inputs():
            with self._compute_lock():
                if (self._number2.number==0.0):
                    self.model_validation_state = NodeValidationState.Error
                    self.model_validation_error = "Division by zero error"
                    self._result = None
                else:
                    self._result = IntegerData(self._number1.number % self._number2.number)

        self.data_updated.emit(0)

    def embedded_widget(self) -> QWidget:
        '''
        embedded_widget

        Returns
        -------
        value : QWidget
        '''
        return None

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


class MultiplicationModel(MathOperationDataModel):
    def caption(self) -> str:
        '''
        caption

        Returns
        -------
        value : str
        '''
        return "Multiplication"

    @staticmethod
    def name() -> str:
        '''
        name

        Returns
        -------
        value : str
        '''
        return "Result"

    def caption_visible(self) -> bool:
        '''
        caption_visible

        Returns
        -------
        value : bool
        '''
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
        if port_type==PortType.In:
            return 1
        elif port_type == PortType.Out:
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
        return DecimalData().type()

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

    def set_in_data(self, data: NodeData, int: int):
        '''
        set_in_data

        Parameters
        ----------
        data : NodeData
        int : int
        '''
        if data:
            self.model_validation_state = NodeValidationState.Valid
            self.model_validation_error = ''
            self._label.setText(data.numberAsText())
        else:
            self.model_validation_state = NodeValidationState.Warning
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


class NumberSourceDataModel(NodeDataModel):
    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number = None
        self._line_edit = QLineEdit()

    def number_source_data_model(self):
        self._line_edit.setValidator(QDoubleValidator())
        self._line_edit.setMaximumSize(self._line_edit.sizeHint())
        self._line_edit.textChanged.connect(self.on_text_edited)
        self._line_edit.setText("0.0")

    def caption(self) -> str:
        '''
        caption

        Returns
        -------
        value : str
        '''
        return "Number Source"

    def caption_visible(self) -> bool:
        '''
        caption_visible

        Returns
        -------
        value : bool
        '''
        return False

    @staticmethod
    def name() -> str:
        '''
        name

        Returns
        -------
        value : str
        '''
        return "NumberSource"

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
        if (port_type == PortType.In):
            return 0
        elif port_type == PortType.Out:
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
        return DecimalData().type()

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


class SubtractionModel(MathOperationDataModel):
    def caption(self) -> str:
        '''
        caption

        Returns
        -------
        value : str
        '''
        return "Subtraction"

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
        if port_type==PortType.In:
            if port_index == 0:
                return 'Minuend'
            elif port_index == 1:
                return 'Subtrahend'
        elif port_type == PortType.Out:
            return 'Result'

    @staticmethod
    def name() -> str:
        '''
        name

        Returns
        -------
        value : str
        '''
        return "Subtraction"

    def compute(self):
        if self._check_inputs:
            with self._compute_lock():
                self.model_validation_state = NodeValidationState.Valid
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


logging.basicConfig(level='DEBUG')
app = QApplication([])

registry = nodeeditor.DataModelRegistry()

models = (AdditionModel, DivisionModel, ModuloModel, MultiplicationModel,
          NumberSourceDataModel, SubtractionModel)
for model in models:
    registry.register_model(model, category='Operations',
                            style=None)

registry.register_type_converter(DecimalData.type(), IntegerData.type(),
                                 decimal_to_integer_converter)
registry.register_type_converter(IntegerData.type(), DecimalData.type(),
                                 decimal_to_integer_converter)

scene = nodeeditor.FlowScene(registry=registry)

view = nodeeditor.FlowView(scene)
view.setWindowTitle("Calculator example")
view.resize(800, 600)
view.show()

node = scene.create_node(models[4])

app.exec_()

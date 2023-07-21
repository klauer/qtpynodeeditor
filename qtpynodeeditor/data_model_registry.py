import logging
import typing

from .node_data import NodeData, NodeDataModel, NodeDataType
from .type_converter import TypeConverter

logger = logging.getLogger(__name__)


class DataModelRegistry:
    def __init__(self):
        self.type_converters = {}
        self._models_category = {}
        self._item_creators = {}
        self._categories = set()

    def register_model(self, creator, category='', *, style=None, **init_kwargs):
        name = creator.name
        self._item_creators[name] = (creator, {'style': style, **init_kwargs})
        self._categories.add(category)
        self._models_category[name] = category

    def register_type_converter(self,
                                type_in: NodeDataType,
                                type_out: NodeDataType,
                                type_converter: TypeConverter):
        """
        Register a type converter for a given data type.

        Parameters
        ----------
        type_in : NodeDataType or NodeData subclass
            The input type.

        type_out : NodeDataType or NodeData subclass
            The output type.

        type_converter : TypeConverter
            The type converter to use for the conversion.
        """
        # TODO typing annotation
        if hasattr(type_in, 'data_type'):
            type_in = typing.cast(NodeData, type_in).data_type
        if hasattr(type_out, 'data_type'):
            type_out = typing.cast(NodeData, type_out).data_type

        self.type_converters[(type_in, type_out)] = type_converter

    def create(self, model_name: str) -> NodeDataModel:
        """
        Create a :class:`NodeDataModel` given its user-friendly name.

        Parameters
        ----------
        model_name : str

        Returns
        -------
        data_model_instance : NodeDataModel
            The instance of the given data model.

        Raises
        ------
        ValueError
            If the model name is not registered.
        """
        cls, kwargs = self.get_model_by_name(model_name)
        return cls(**kwargs)

    def get_model_by_name(self, model_name: str
                          ) -> tuple[type[NodeDataModel], dict]:
        """
        Get information on how to create a specific :class:`NodeDataModel`
        node given its user-friendly name.

        Parameters
        ----------
        model_name : str

        Returns
        -------
        data_model : NodeDataModel
            The data model class.

        init_kwargs : dict
            Default init keyword arguments.

        Raises
        ------
        ValueError
            If the model name is not registered.
        """
        try:
            return self._item_creators[model_name]
        except KeyError:
            raise ValueError(f'Unknown model: {model_name}') from None

    def registered_model_creators(self) -> dict:
        """
        Registered model creators

        Returns
        -------
        value : dict
        """
        return dict(self._item_creators)

    def registered_models_category_association(self) -> dict:
        """
        Registered models category association

        Returns
        -------
        value : DataModelRegistry.RegisteredModelsCategoryMap
        """
        return self._models_category

    def categories(self) -> set:
        """
        Categories

        Returns
        -------
        value : DataModelRegistry.CategoriesSet
        """
        return self._categories

    def get_type_converter(self, d1: NodeDataType, d2: NodeDataType) -> TypeConverter:
        """
        Get type converter

        Parameters
        ----------
        d1 : NodeDataType
        d2 : NodeDataType

        Returns
        -------
        value : TypeConverter
        """
        return self.type_converters.get((d1, d2), None)

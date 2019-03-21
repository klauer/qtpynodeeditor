import logging

from .node_data import NodeDataModel, NodeDataType
from .type_converter import TypeConverter, TypeConverterId, DefaultTypeConverter


logger = logging.getLogger(__name__)


class DataModelRegistry:
    def __init__(self):
        self._type_converters = {}
        self._models_category = {}
        self._item_creators = {}
        self._categories = set()

    def register_model(self, creator, category='', *, style=None, **init_kwargs):
        name = creator.name()
        self._item_creators[name] = (creator, {'style': style, **init_kwargs})
        self._categories.add(category)
        self._models_category[name] = category

    def register_type_converter(self, type_in: NodeDataType, type_out:
                                NodeDataType, type_converter: TypeConverter):
        """
        Register type converter

        Parameters
        ----------
        id_ : TypeConverterId
        type_converter : TypeConverter
        """
        self._type_converters[(type_in, type_out)] = type_converter

    def create(self, model_name: str) -> NodeDataModel:
        """
        Create

        Parameters
        ----------
        model_name : str

        Returns
        -------
        value : (NodeDataModel, init_kwargs)
        """
        cls, kwargs = self._item_creators[model_name]
        return cls(**kwargs)

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
        try:
            return self._type_converters[(d1, d2)]
        except KeyError:
            if d1 != d2:
                logger.debug('No type converter available for %s -> %s',
                             d1, d2)
            return DefaultTypeConverter

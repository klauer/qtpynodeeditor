import logging

from .node_data import NodeDataModel, NodeDataType
from .type_converter import TypeConverter, TypeConverterId, DefaultTypeConverter


logger = logging.getLogger(__name__)


class DataModelRegistry:
    def __init__(self):
        self._registered_type_converters = {}
        self._registered_models_category = {}
        self._registered_item_creators = {}
        self._categories = set()

    def register_model(self, creator, category=''):
        name = creator.name()
        self._registered_item_creators[name] = creator
        self._categories.add(category)
        self._registered_models_category[name] = category

    def register_type_converter(self, id_: TypeConverterId,
                                type_converter: TypeConverter):
        """
        register_type_converter

        Parameters
        ----------
        id_ : TypeConverterId
        type_converter : TypeConverter
        """
        self._registered_type_converters[id_] = type_converter

    def create(self, model_name: str) -> NodeDataModel:
        """
        create

        Parameters
        ----------
        model_name : str

        Returns
        -------
        value : NodeDataModel
        """
        return self._registered_item_creators[model_name]

    def registered_model_creators(self) -> dict:
        """
        registered_model_creators

        Returns
        -------
        value : DataModelRegistry.RegisteredModelCreatorsMap
        """
        return self._registered_item_creators

    def registered_models_category_association(self) -> dict:
        """
        registered_models_category_association

        Returns
        -------
        value : DataModelRegistry.RegisteredModelsCategoryMap
        """
        return self._registered_models_category

    def categories(self) -> set:
        """
        categories

        Returns
        -------
        value : DataModelRegistry.CategoriesSet
        """
        return self._categories

    def get_type_converter(self, d1: NodeDataType, d2: NodeDataType) -> TypeConverter:
        """
        get_type_converter

        Parameters
        ----------
        d1 : NodeDataType
        d2 : NodeDataType

        Returns
        -------
        value : TypeConverter
        """
        try:
            return self._registered_type_converters[(d1, d2)]
        except KeyError:
            if d1 != d2:
                logger.debug('No type converter available for %s -> %s',
                             d1, d2)
            return DefaultTypeConverter

class TypeConverterId:
    def __init__(self, type_in, type_out):
        self.type_in = type_in
        self.type_out = type_out


class TypeConverter(TypeConverterId):
    def __init__(self, type_in, type_out, func):
        self.type_in = type_in
        self.type_out = type_out
        self.id = TypeConverterId(type_in, type_out)
        self.func = func

    def __call__(self, input):
        return self.func(input)


def _convert(arg):
    return arg


DefaultTypeConverter = TypeConverter(None, None, _convert)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Schema generation functions. """
from copy import deepcopy
import inspect
import collections.abc
import typing as tp
import dessia_common.utils.types as dc_types
from dessia_common.abstract import CoreDessiaObject
from dessia_common.files import BinaryFile, StringFile
from dessia_common.typings import MethodType, ClassMethodType, Any, InstanceOf, Subclass
from dessia_common.measures import Measure
from dessia_common.utils.docstrings import parse_docstring, FAILED_DOCSTRING_PARSING, FAILED_ATTRIBUTE_PARSING
from dessia_common.utils.helpers import prettyname
from dessia_common.schemas.interfaces import Annotations, T
from dessia_common.checks import CheckList, FailedCheck, PassedCheck, CheckWarning
from dessia_common.serialization import serialize

SCHEMA_HEADER = {"definitions": {}, "$schema": "http://json-schema.org/d_raft-07/schema#",
                 "type": "object", "required": [], "properties": {}}
RESERVED_ARGNAMES = ['self', 'cls', 'progress_callback', 'return']

_fullargsspec_cache = {}


class Schema:
    """
    Abstraction of a Schema.

    It reads the user-defined type hints and then writes into a dict the recursive structure of an object
    that can be handled by dessia_common.
    This dictionnary can then be translated as a json to be read by the frontend in order to compute edit forms,
    for example.

    Right now Schema doesn't inherit from any DessiaObject class (SerializableObject ?), but could, in the future.
    That is why it implements methods with the same name.
    """

    def __init__(self, annotations: Annotations, argspec: inspect.FullArgSpec, docstring: str):
        self.annotations = annotations
        self.attributes = [a for a in argspec.args if a not in RESERVED_ARGNAMES]

        try:  # Parse docstring
            self.parsed_docstring = parse_docstring(docstring=docstring, annotations=annotations)
        except Exception:  # Catching broad exception because we don't want it to break platform if a failure occurs
            self.parsed_docstring = FAILED_DOCSTRING_PARSING

        self.parsed_attributes = self.parsed_docstring['attributes']

        self.required_arguments, self.default_arguments = split_default_args(argspecs=argspec, merge=False)

        self.property_schemas = {}
        for attribute in self.attributes:
            default = self.default_arguments.get(attribute, None)
            annotation = self.annotations[attribute]
            schema = get_schema(annotation=annotation, attribute=attribute, definition_default=default)
            self.property_schemas[attribute] = schema

        self.check_list().raise_if_above_level("error")

    @property
    def editable_attributes(self):
        """ Attributes that are not in RESERVED_ARGNAMES. """
        return [a for a in self.attributes if a not in RESERVED_ARGNAMES]

    def chunk(self, attribute: str):
        """ Extract and compute a schema from one of the attributes. """
        schema = self.property_schemas[attribute]

        if self.parsed_attributes is not None and attribute in self.parsed_attributes:
            try:
                description = self.parsed_attributes[attribute]['desc']
            except Exception:  # Catching broad exception because we don't want it to break platform if a failure occurs
                description = FAILED_ATTRIBUTE_PARSING["desc"]
        else:
            description = ""

        editable = attribute in self.editable_attributes
        chunk = schema.to_dict(title=prettyname(attribute), editable=editable, description=description)

        # if attribute in self.default_arguments:
        #     # TODO Could use this and Optional proxy in order to inject real default values for mutables
        #     default = self.default_arguments.get(attribute, None)
        #     print("Default", default)
        #     chunk["default_value"] = schema.default_value(definition_default=default)
        return chunk

    @property
    def chunks(self):
        """ Concatenate schema chunks into a list. """
        return [self.chunk(a) for a in self.attributes]

    def to_dict(self):
        """ Write the whole schema. """
        schema = deepcopy(SCHEMA_HEADER)
        properties = {a: self.chunk(a) for a in self.attributes}
        schema.update({"required": self.required_arguments, "properties": properties,
                       "description": self.parsed_docstring["description"]})
        return schema

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_dict(self):
        """
        Compute global default dict.

        If a definition default have been set by user, most schemas will return this value (or serialized).
        if not, schemas will compute a default compatible with platform (None most of the time).
        """
        return {a: self.property_schemas[a].default_value() for a in self.attributes}

    def check_list(self) -> CheckList:
        """
        Browse all properties and list potential issues.

        Checks performed for each argument :
        - Is typed in method definition
        - Schema specific check
        """
        issues = CheckList([])

        for attribute in self.attributes:
            # Is typed
            check = self.attribute_is_annotated(attribute)
            issues += CheckList([check])

            # Specific check
            schema = self.property_schemas[attribute]
            issues += schema.check_list()
        return issues

    def is_valid(self) -> bool:
        """ Return whether the class definition is valid or not. """
        return self.check_list().checks_above_level("error")

    def attribute_is_annotated(self, attribute: str) -> PassedCheck:
        """ Check whether given attribute is annotated in function definition or not. """
        if attribute not in self.annotations:
            return FailedCheck(f"Attribute '{attribute}' : has no typing")
        return PassedCheck(f"Attribute '{attribute}' : is annotated")


class ClassSchema(Schema):
    """
    Schema of a class.

    Class must be a subclass of DessiaObject. It reads the __init__ annotations.
    """
    def __init__(self, class_: tp.Type[CoreDessiaObject]):
        self.class_ = class_
        self.standalone_in_db = class_._standalone_in_db
        self.python_typing = dc_types.full_classname(class_, compute_for="class")
        annotations = tp.get_type_hints(class_.__init__)

        members = inspect.getfullargspec(self.class_.__init__)
        docstring = class_.__doc__

        Schema.__init__(self, annotations=annotations, argspec=members, docstring=docstring)

    @property
    def editable_attributes(self):
        """ Attributes that are not in RESERVED_ARGNAMES nor defined as non editable by user. """
        attributes = super().editable_attributes
        return [a for a in attributes if a not in self.class_._non_editable_attributes]

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_dict(self):
        """ Compute class default dict. Add object_class to base one. """
        dict_ = super().default_dict()
        dict_["object_class"] = self.python_typing
        return dict_


class MethodSchema(Schema):
    """
    Schema of a method.

    Given method should be one of a DessiaObject. It reads its annotations.
    """
    def __init__(self, method: tp.Callable):
        self.method = method

        annotations = tp.get_type_hints(method)
        members = inspect.getfullargspec(method)
        docstring = method.__doc__
        Schema.__init__(self, annotations=annotations, argspec=members, docstring=docstring)

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")


class Property:
    """ Base class for a schema property. """
    def __init__(self, annotation: tp.Type[T], attribute: str, definition_default: T = None):
        self.annotation = annotation
        self.attribute = attribute
        self.definition_default = definition_default

    @property
    def schema(self):
        """ Return a reference to itself. Might be overwritten for proxy such as Optional or Annotated. """
        return self

    @property
    def serialized(self):
        return str(self.annotation)

    @property
    def check_prefix(self) -> str:
        """ Shortcut for Check message prefixes. """
        return f"Attribute '{self.attribute}' : "

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write base schema as a dict. """
        return {'title': title, 'editable': editable, 'description': description,
                'python_typing': self.serialized, "type": None}

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_value(self):
        """ Generic default. Yield user default if defined, else None. """
        return self.definition_default

    def check_list(self) -> CheckList:
        """
        Check validity of Property Type Hint.

        Checks performed : None. TODO ?
        """
        return CheckList([])


class TypingProperty(Property):
    """ Schema class for typing based annotations. """
    def __init__(self, annotation: tp.Type[T], attribute: str, definition_default: T = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    @property
    def args(self):
        """ Return Typing arguments. """
        return tp.get_args(self.annotation)

    @property
    def origin(self):
        """ Return Typing origin. """
        return tp.get_origin(self.annotation)

    @property
    def args_schemas(self) -> tp.List[Property]:
        """ Get schema for each arg. """
        return [get_schema(annotation=a, attribute=f"{self.attribute}/{i}") for i, a in enumerate(self.args)]

    @property
    def serialized(self):
        serialized = self.origin.__name__
        if self.args:
            serialized = f"{serialized}[{', '.join([s.serialized for s in self.args_schemas])}]"
        return serialized

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def has_one_arg(self) -> PassedCheck:
        """ Annotation should have exactly one argument. """
        if len(self.args) != 1:
            pretty_origin = prettyname(self.origin.__name__)
            msg = f"{self.check_prefix}is typed as a '{pretty_origin}' which requires exactly 1 argument. " \
                  f"Expected '{pretty_origin}[T]', got '{self.annotation}'."
            return FailedCheck(msg)
        return PassedCheck(f"{self.check_prefix}has exactly one arg in its definition.")


class ProxyProperty(TypingProperty):
    """
    Schema Class for Proxies.

    Proxies are just intermediate types which actual schemas if its args. For example OptionalProperty proxy.
    """
    def __init__(self, annotation: tp.Type[T], attribute: str, definition_default: T = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    @property
    def args(self):
        try:
            return self.schema.args
        except AttributeError:
            return None

    @property
    def schema(self):
        """ Return a reference to its only arg. """
        return get_schema(annotation=self.args[0], attribute=self.attribute, definition_default=self.definition_default)

    @property
    def serialized(self) -> str:
        return self.schema.serialized


class OptionalProperty(ProxyProperty):
    """
    Proxy Schema class for OptionalProperty properties.

    OptionalProperty is only a catch for arguments that default to None.
    Arguments with default values other than None are not considered Optionals
    """
    def __init__(self, annotation: tp.Type[T], attribute: str, definition_default: T = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write Optional as a dict. """
        default_value = self.schema.default_value()
        chunk = self.schema.to_dict(title=title, editable=editable, description=description)
        chunk["default_value"] = default_value
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")


class AnnotatedProperty(ProxyProperty):
    """
    Proxy Schema class for annotated type hints.

    AnnotatedProperty annotations are type hints with more arguments passed, such as value ranges, or probably enums,
    precision,...

    This could enable quite effective type checking on frontend form.

    Only available with python >= 3.11
    """
    _not_implemented_msg = "AnnotatedProperty type hints are not implemented yet. This needs python 3.11 at least. " \
                           "Dessia only supports python 3.9 at the moment."

    # TODO Whenever Dessia decides to upgrade to python 3.11
    def __init__(self, annotation: tp.Type[T], attribute: str, definition_default: T = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)
        raise NotImplementedError(self._not_implemented_msg)

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write Annotated as a dict. """
        raise NotImplementedError(self._not_implemented_msg)

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def check_list(self) -> CheckList:
        """
        Check validity of DynamicDict Type Hint.

        Checks performed : None. TODO : Arg validity
        """
        raise NotImplementedError(self._not_implemented_msg)


Builtin = tp.Union[str, bool, float, int]


class BuiltinProperty(Property):
    """ Schema class for Builtin type hints. """
    def __init__(self, annotation: tp.Type[Builtin], attribute: str, definition_default: Builtin = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    @property
    def serialized(self) -> str:
        return self.annotation.__name__

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write Builtin as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        chunk["type"] = dc_types.TYPING_EQUIVALENCES[self.annotation]
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")


class MeasureProperty(BuiltinProperty):
    """ Schema class for Measure type hints. """
    def __init__(self, annotation: tp.Type[Measure], attribute: str, definition_default: Measure = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    @property
    def serialized(self) -> str:
        return dc_types.full_classname(object_=self.annotation, compute_for="class")

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write Measure as a dict. """
        chunk = Property.to_dict(self, title=title, editable=editable, description=description)
        chunk.update({"si_unit": self.annotation.si_unit, "type": "number"})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")


File = tp.Union[StringFile, BinaryFile]


class FileProperty(Property):
    """ Schema class for File type hints. """
    def __init__(self, annotation: tp.Type[File], attribute: str, definition_default: File = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write File as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        chunk.update({'type': 'text', 'is_file': True})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def check_list(self) -> CheckList:
        """
        Check validity of File Type Hint.

        Checks performed :
        - Doesn't define any default value.
        """
        issues = super().check_list()
        issues += CheckList([self.has_no_default()])
        return issues

    def has_no_default(self) -> PassedCheck:
        """ Check if the user definition doesn't have any default value, as it is not supported for files. """
        if self.definition_default is not None:
            msg = f"{self.check_prefix}File input defines a default value, whereas it is not supported."
            return CheckWarning(msg)
        msg = f"{self.check_prefix}File input doesn't define a default value, as it should."
        return PassedCheck(msg)


class CustomClass(Property):
    """ Schema class for CustomClass type hints. """
    def __init__(self, annotation: tp.Type[CoreDessiaObject], attribute: str,
                 definition_default: CoreDessiaObject = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    @property
    def schema(self):
        """ Return a reference to the schema of the annotation. """
        return ClassSchema(self.annotation)

    @property
    def serialized(self) -> str:
        return dc_types.full_classname(object_=self.annotation, compute_for='class')

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write CustomClass as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        chunk.update({'type': 'object', 'standalone_in_db': self.annotation._standalone_in_db,
                      "classes": [self.serialized]})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_value(self):
        """ Default value for an object. """
        return object_default(definition_default=self.definition_default, class_schema=self.schema)

    def check_list(self) -> CheckList:
        """
        Check validity of user custom class Type Hint.

        Checks performed :
        - Is subclass of DessiaObject
        """
        issues = super().check_list()
        issues += CheckList([self.is_dessia_object_typed()])
        return issues

    def is_dessia_object_typed(self) -> PassedCheck:
        """ Check whether if typing for given attribute annotates a subclass of DessiaObject or not . """
        if not issubclass(self.annotation, CoreDessiaObject):
            return FailedCheck(f"{self.check_prefix}Class '{self.classname}' is not a subclass of DessiaObject.")
        msg = f"{self.check_prefix}Class '{self.classname}' is properly typed as a subclass of DessiaObject."
        return PassedCheck(msg)


class UnionProperty(TypingProperty):
    """ Schema class for Union type hints. """
    def __init__(self, annotation: tp.Type[tp.Union[T]], attribute: str, definition_default: tp.Union[T] = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

        standalone_args = [a._standalone_in_db for a in self.args]
        if all(standalone_args):
            self.standalone = True
        elif not any(standalone_args):
            self.standalone = False
        else:
            self.standalone = None

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write Union as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        chunk.update({'type': 'object', 'classes': [self.serialized], 'standalone_in_db': self.standalone})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_value(self):
        """ Default value for an object. """
        return object_default(self.definition_default)

    def check_list(self) -> CheckList:
        """
        Check validity of UnionProperty Type Hint.

        Checks performed :
        - Subobject are all standalone or none of them are. TODO : What happen if args are not DessiaObjects ?
        """
        issues = super().check_list()
        issues += CheckList([self.classes_are_standalone_consistent()])
        return issues

    def classes_are_standalone_consistent(self) -> PassedCheck:
        """ Check whether all class in Union are standalone or none of them are. """
        standalone_args = [a._standalone_in_db for a in self.args]
        if all(standalone_args):
            msg = f"{self.check_prefix}All arguments of Union type '{self.annotation}' are standalone in db."
            return PassedCheck(msg)
        if not any(standalone_args):
            msg = f"{self.check_prefix}No arguments of Union type '{self.annotation}' are standalone in db."
            return PassedCheck(msg)
        msg = f"{self.check_prefix}'standalone_in_db' values for arguments of Union type '{self.annotation}'" \
              f"are not consistent. They should be all standalone in db or none of them should."
        return FailedCheck(msg)


class HeterogeneousSequence(TypingProperty):
    """
    Schema class for Tuple type hints.

    Datatype that can be seen as a tuple. Have any amount of arguments but a limited length.
    """
    def __init__(self, annotation: tp.Type[tp.Tuple], attribute: str, definition_default: tp.Tuple = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

        self.item_schemas = [get_schema(annotation=a, attribute=f"{attribute}/{i}") for i, a in enumerate(self.args)]

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write HeterogeneousSequence as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        items = [sp.to_dict(title=f"{title}/{i}", editable=editable) for i, sp in enumerate(self.item_schemas)]
        chunk.update({'type': 'array', 'additionalItems': False, 'items': items})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_value(self):
        """
        Default value for a Tuple.

        Return serialized user default if defined, else a Tuple of Nones with the right size.
        """
        if self.definition_default is not None:
            return serialize(self.definition_default)
        return [s.default_value() for s in self.item_schemas]

    def check_list(self) -> CheckList:
        """ Check validity of Tuple Type Hint. """
        issues = super().check_list()
        issues += CheckList([self.has_enough_args()])
        return issues

    def has_enough_args(self) -> PassedCheck:
        """ Annotation should have at least one argument, one for each element of the tuple. """
        if len(self.args) == 0:
            msg = f"{self.check_prefix}is typed as a 'Tuple' which requires at least 1 argument. " \
                  f"Expected 'Tuple[T0, T1, ..., Tn]', got '{self.annotation}'."
            return FailedCheck(msg)
        return PassedCheck(f"{self.check_prefix}has at least one argument : '{self.annotation}'.")


class HomogeneousSequence(TypingProperty):
    """
    Schema class for List type hints.

    Datatype that can be seen as a list. Have only one argument but an unlimited length.
    """
    def __init__(self, annotation: tp.Type[tp.List[T]], attribute: str, definition_default: tp.List[T] = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

        self.item_schemas = [get_schema(annotation=a, attribute=f"{attribute}/{i}") for i, a in enumerate(self.args)]

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write HomogeneousSequence as a dict. """
        if not title:
            title = 'Items'
        chunk = super().to_dict(title=title, editable=editable, description=description)
        items = [sp.to_dict(title=f"{title}/{i}", editable=editable) for i, sp in enumerate(self.item_schemas)]
        chunk.update({'type': 'array', "items": items[0]})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_value(self):
        """ Default of a sequnce. Always return None as default mutable is prohibited. """
        return None

    def check_list(self) -> CheckList:
        """ Check validity of List Type Hint. """
        issues = super().check_list()
        issues += CheckList([self.has_one_arg(), self.has_no_default()])
        return issues

    def has_no_default(self) -> PassedCheck:
        """ Check if List doesn't define a default value that is other than None. """
        if self.definition_default is not None:
            msg = f"{self.check_prefix}Mutable List input defines a default value other than None," \
                  f"which will lead to unexpected behavior and therefore, is not supported."
            return FailedCheck(msg)
        msg = f"{self.check_prefix}Mutable List doesn't define a default value other than None."
        return PassedCheck(msg)


class DynamicDict(TypingProperty):
    """
    Schema class for Dict type hints.

    Datatype that can be seen as a dict. Have restricted amount of arguments (one for key, one for values),
    but an unlimited length.
    """
    def __init__(self, annotation: tp.Type[tp.Dict[str, Builtin]], attribute: str,
                 definition_default: tp.Dict[str, Builtin] = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write DynamicDict as a dict. """
        key_type, value_type = self.args
        if key_type != str:
            # !!! Should we support other types ? Numeric ?
            raise NotImplementedError('Non strings keys not supported')
        if value_type not in dc_types.TYPING_EQUIVALENCES:
            raise ValueError(f'Dicts should have only builtins keys and values, got {value_type}')
        chunk = super().to_dict(title=title, editable=editable, description=description)
        chunk.update({'type': 'object',
                      'patternProperties': {
                          '.*': {
                            'type': dc_types.TYPING_EQUIVALENCES[value_type]
                          }
                      }})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_value(self):
        """ Default of a dynamic dict. Always return None as default mutable is prohibited. """
        return None

    def check_list(self) -> CheckList:
        """ Check validity of DynamicDict Type Hint. """
        issues = super().check_list()
        checks = [self.has_two_args(), self.has_string_keys(), self.has_simple_values(), self.has_no_default()]
        issues += CheckList(checks)
        return issues

    def has_two_args(self) -> PassedCheck:
        """ Annotation should have exactly two arguments, first one for keys, second one for values. """
        if len(self.args) != 2:
            msg = f"{self.check_prefix}is typed as a 'Dict' which requires exactly 2 arguments. " \
                  f"Expected 'Dict[KeyType, ValueType]', got '{self.annotation}'."
            return FailedCheck(msg)
        return PassedCheck(f"{self.check_prefix}has two args in its definition : '{self.annotation}'.")

    def has_string_keys(self):
        """ Key Type should be str. """
        key_type, value_type = self.args
        if not issubclass(key_type, str):
            # Should we support other types ? Numeric ?
            msg = f"{self.check_prefix}is typed as a 'Dict[{key_type}, {value_type}]' " \
                  f"which requires str as its key type. Expected 'Dict[str, ValueType]', got '{self.annotation}'."
            return FailedCheck(msg)
        return PassedCheck(f"{self.check_prefix}has str keys : '{self.annotation}'.")

    def has_simple_values(self):
        """ Value Type should be simple. """
        key_type, value_type = self.args
        if value_type not in dc_types.TYPING_EQUIVALENCES:
            msg = f"{self.check_prefix}is typed as a 'Dict[{key_type}, {value_type}]' " \
                  f"which requires a builtin type as its value type. " \
                  f"Expected 'int', 'float', 'bool' or 'str', got '{value_type}'."
            return FailedCheck(msg)
        return PassedCheck(f"{self.check_prefix}has simple values : '{self.annotation}'.")

    def has_no_default(self) -> PassedCheck:
        """ Check if Dict doesn't define a default value that is other than None. """
        if self.definition_default is not None:
            msg = f"{self.check_prefix}Mutable Dict input defines a default value other than None," \
                  f"which will lead to unexpected behavior and therefore, is not supported."
            return FailedCheck(msg)
        msg = f"{self.check_prefix}Mutable Dict doesn't define a default value other than None."
        return PassedCheck(msg)


BaseClass = tp.TypeVar("BaseClass", bound=CoreDessiaObject)


class InstanceOfProperty(TypingProperty):
    """
    Schema class for InstanceOf type hints.

    Datatype that can be seen as a union of classes that inherits from the only arg given.
    Instances of these classes validate against this type.
    """
    def __init__(self, annotation: tp.Type[InstanceOf[BaseClass]], attribute: str,
                 definition_default: BaseClass = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    @property
    def schema(self):
        """ Get Schema of base class. """
        return ClassSchema(self.args[0])

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write InstanceOf as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        class_ = self.args[0]
        chunk.update({'type': 'object', 'instance_of': self.serialized, 'standalone_in_db': class_._standalone_in_db})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def default_value(self) -> BaseClass:
        """ Default value of an object. """
        return object_default(definition_default=self.definition_default, class_schema=self.schema)

    def check_list(self) -> CheckList:
        """ Check validity of InstanceOf Type Hint. """
        issues = super().check_list()
        issues += CheckList([self.has_one_arg()])
        return issues


class SubclassProperty(TypingProperty):
    """
    Schema class for Subclass type hints.

    Datatype that can be seen as a union of classes that inherits from the only arg given.
    Classes validate against this type.
    """
    def __init__(self, annotation: tp.Type[Subclass[BaseClass]], attribute: str,
                 definition_default: tp.Type[BaseClass] = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write Subclass as a dict. """
        raise NotImplementedError("Subclass is not implemented yet")

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def check_list(self) -> CheckList:
        """
        Check validity of Subclass Type Hint.

        Checks performed :
        - Annotation has exactly one argument, which is the type of the base class.
        """
        issues = super().check_list()
        issues += CheckList([self.has_one_arg()])
        return issues


class MethodTypeProperty(TypingProperty):
    """
    Schema class for MethodType and ClassMethodType type hints.

    A specifically instantiated MethodType validated against this type.
    """
    def __init__(self, annotation: tp.Type[MethodType], attribute: str, definition_default: MethodType = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

        self.class_ = self.args[0]
        self.class_schema = get_schema(annotation=self.class_, attribute=attribute,
                                       definition_default=definition_default)

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write MethodType as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        classmethod_ = self.origin is ClassMethodType
        chunk.update({
            'type': 'object', 'is_method': True, 'classmethod_': classmethod_,
            'properties': {
                'class_': self.class_schema.to_dict(title=title, editable=editable, description=description),
                'name': {
                    'type': 'string'
                }
            }
        })
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def check_list(self) -> CheckList:
        """
        Check validity of MethodType Type Hint.

        Checks performed :
        - Class has method TODO
        """
        return CheckList([])


Class = tp.TypeVar("Class", bound=type)


class ClassProperty(TypingProperty):
    """
    Schema class for 'Type' type hints.

    Non DessiaObject subclasses validated against this type.
    """
    def __init__(self, annotation: tp.Type[Class], attribute: str, definition_default: Class = None):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)

    def to_dict(self, title: str = "", editable: bool = False, description: str = ""):
        """ Write Class as a dict. """
        chunk = super().to_dict(title=title, editable=editable, description=description)
        chunk.update({'type': 'object', 'is_class': True, 'properties': {'name': {'type': 'string'}}})
        return chunk

    @classmethod
    def dict_to_object(cls, dict_):
        """
        Build a schema back from its dict representation.

        TODO  Useful for low_code features ?
        """
        raise NotImplementedError("Schema reconstruction is not implemented yet")

    def check_list(self) -> CheckList:
        """
        Check validity of Class Type Hint.

        Checks performed :
        - Annotation has exactly 1 argument
        """
        issues = super().check_list()
        issues += CheckList([self.has_one_arg()])
        return issues


class GenericTypeProperty(Property):
    def __init__(self, annotation: tp.Type[tp.TypeVar], attribute: str, definition_default: tp.TypeVar):
        super().__init__(annotation=annotation, attribute=attribute, definition_default=definition_default)


def inspect_arguments(method: tp.Callable, merge: bool = False):
    """ Wrapper around 'split_default_argument' method in order to call it from a method object. """
    method_full_name = f'{method.__module__}.{method.__qualname__}'
    if method_full_name in _fullargsspec_cache:
        argspecs = _fullargsspec_cache[method_full_name]
    else:
        argspecs = inspect.getfullargspec(method)
        _fullargsspec_cache[method_full_name] = argspecs
    return split_default_args(argspecs=argspecs, merge=merge)


def split_default_args(argspecs: inspect.FullArgSpec, merge: bool = False):
    """
    Find default value and required arguments of class construction.

    Get method arguments and default arguments as sequences while removing forbidden ones (self, cls...).
    """
    nargs, ndefault_args = split_argspecs(argspecs)

    default_arguments = {}
    arguments = []
    for iargument, argument in enumerate(argspecs.args[1:]):
        if argument not in RESERVED_ARGNAMES:
            if iargument >= nargs - ndefault_args:
                default_value = argspecs.defaults[ndefault_args - nargs + iargument]
                if merge:
                    arguments.append((argument, default_value))
                else:
                    default_arguments[argument] = default_value
            else:
                arguments.append(argument)
    return arguments, default_arguments


def split_argspecs(argspecs: inspect.FullArgSpec) -> tp.Tuple[int, int]:
    """ Get number of regular arguments as well as arguments with default values. """
    nargs = len(argspecs.args) - 1

    if argspecs.defaults is not None:
        ndefault_args = len(argspecs.defaults)
    else:
        ndefault_args = 0
    return nargs, ndefault_args


def get_schema(annotation: tp.Type[T], attribute: str, definition_default: tp.Optional[T] = None) -> Property:
    """ Get schema Property object from given annotation. """
    if annotation in dc_types.TYPING_EQUIVALENCES:
        return BuiltinProperty(annotation=annotation, attribute=attribute, definition_default=definition_default)
    if dc_types.is_typing(annotation):
        return typing_schema(typing_=annotation, attribute=attribute, definition_default=definition_default)
    if hasattr(annotation, '__origin__') and annotation.__origin__ is type:
        # TODO Is this deprecated ? Should be used in 3.8 and not 3.9 ?
        # return {'type': 'object', 'is_class': True, 'properties': {'name': {'type': 'string'}}}
        pass
    if annotation is Any:
        # TODO Do we still want to support Any ?
        # chunk = {'type': 'object', 'properties': {'.*': '.*'}}
        pass
    if inspect.isclass(annotation):
        return custom_class_schema(annotation=annotation, attribute=attribute, definition_default=definition_default)
    if isinstance(annotation, tp.TypeVar):
        return GenericTypeProperty(annotation=annotation, attribute=attribute, definition_default=definition_default)
    raise NotImplementedError(f"No schema defined for attribute '{attribute}' annotated '{annotation}'.")


ORIGIN_TO_SCHEMA_CLASS = {
    tuple: HeterogeneousSequence, list: HomogeneousSequence, collections.abc.Iterator: HomogeneousSequence,
    tp.Union: UnionProperty, dict: DynamicDict, InstanceOf: InstanceOfProperty,
    MethodType: MethodTypeProperty, ClassMethodType: MethodTypeProperty, type: ClassProperty
}


def typing_schema(typing_: tp.Type[T], attribute: str, definition_default: T = None) -> Property:
    """ Get schema Property for typing annotations. """
    origin = tp.get_origin(typing_)
    if origin is tp.Union and dc_types.union_is_default_value(typing_):
        # This is a false UnionProperty => Is a default value set to None
        return OptionalProperty(annotation=typing_, attribute=attribute, definition_default=definition_default)
    try:
        return ORIGIN_TO_SCHEMA_CLASS[origin](typing_, attribute, definition_default)
    except KeyError as exc:
        raise NotImplementedError(f"No Schema defined for typing '{typing_}'.") from exc


def custom_class_schema(annotation: tp.Type[T], attribute: str, definition_default: T = None) -> Property:
    """ Get schema Property object for non typing annotations. """
    if issubclass(annotation, Measure):
        return MeasureProperty(annotation=annotation, attribute=attribute, definition_default=definition_default)
    if issubclass(annotation, (BinaryFile, StringFile)):
        return FileProperty(annotation=annotation, attribute=attribute, definition_default=definition_default)
    if issubclass(annotation, CoreDessiaObject):
        # Dessia custom classes
        return CustomClass(annotation=annotation, attribute=attribute, definition_default=definition_default)
    raise NotImplementedError(f"No Schema defined for type '{annotation}'.")


def object_default(definition_default=None, class_schema: ClassSchema = None):
    """
    Default value of an object.

    Return serialized user default if definition, else None.
    """
    if definition_default is not None:
        return serialize(definition_default)
    if class_schema is not None:
        # TODO Should we implement this ? Right now, tests state that the result is None
        # return class_schema.default_dict()
        pass
    return None

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serialization Tools

"""

import warnings
import dessia_common.serialization as dcs


def serialize_dict(dict_):
    """
    Serialize a dict into a dict (values are serialized)
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.serialize_dict(dict_)


def serialize_sequence(seq):
    """
    Serialize a sequence (list or sequence) into a list of dicts
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.serialize_sequence(seq)


def serialize(value):
    """
    Main function for serialization without pointers
    Calls recursively itself serialize_sequence and serialize_dict
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.serialize(value)


def serialize_with_pointers(value, memo=None, path='#'):
    """
    Main function for serialization with pointers
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.serialize_with_pointers(value=value, memo=memo, path=path)


def serialize_dict_with_pointers(dict_, memo, path):
    """
    Serialize a dict recursively with jsonpointers using a memo dict at a given path of the top level object
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.serialize_dict_with_pointers(dict_=dict_, memo=memo, path=path)


def serialize_sequence_with_pointers(seq, memo, path):
    """
    Serialize a sequence (list or tuple) using jsonpointers
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.serialize_sequence_with_pointers(seq=seq, memo=memo, path=path)


def deserialize(serialized_element, sequence_annotation: str = 'List', global_dict=None,
                pointers_memo=None, path: str = '#'):
    """
    Main function for deserialization, handle pointers
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.deserialize(serialized_element=serialized_element, sequence_annotation=sequence_annotation,
                           global_dict=global_dict, pointers_memo=pointers_memo, path=path)


def deserialize_sequence(sequence, annotation=None, global_dict=None, pointers_memo=None, path='#'):
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.deserialize_sequence(sequence=sequence, annotation=annotation, global_dict=global_dict,
                                    pointers_memo=pointers_memo, path=path)


def dict_to_object(dict_, class_=None, force_generic: bool = False,
                   global_dict=None, pointers_memo=None, path='#'):
    """
    Transform a dict to an object
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.dict_to_object(dict_=dict_, class_=class_, force_generic=force_generic, global_dict=global_dict,
                              pointers_memo=pointers_memo, path=path)


def deserialize_with_type(type_, value):
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.deserialize_with_type(type_=type_, value=value)


def deserialize_with_typing(type_, argument, global_dict=None, pointers_memo=None, path='#'):
    """
    Deserialize an object with a typing info
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.deserialize_with_typing(type_=type_, argument=argument, global_dict=global_dict,
                                       pointers_memo=pointers_memo, path=path)


def deserialize_argument(type_, argument, global_dict=None, pointers_memo=None, path='#'):
    """
    Deserialize an argument of a function with the type
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.deserialize_argument(type_=type_, argument=argument, global_dict=global_dict,
                                    pointers_memo=pointers_memo, path=path)


def find_references(value, path='#'):
    """
    Traverse recursively the value to find reference (pointers) in it
    Calls recursively find_references_sequence and find_references_dict
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.find_references(value=value, path=path)


def find_references_sequence(seq, path):
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.find_references_sequence(seq=seq, path=path)


def find_references_dict(dict_, path):
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.find_references_dict(dict_=dict_, path=path)


def pointer_graph(value):
    """
    Create a graph of subattributes of an object with edge representing either:
     * the hierarchy of an subattribute to an attribute
     * the pointer link between the 2 elements
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.pointer_graph(value)


def update_pointers_data(global_dict, current_dict, pointers_memo):
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.update_pointers_data(global_dict=global_dict, current_dict=current_dict, pointers_memo=pointers_memo)


def deserialization_order(dict_):
    """
    Analyse a dict representing an object and give a deserialization order
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.deserialization_order(dict_)


def dereference_jsonpointers(dict_):
    """
    Analyse the given dict to:
    - find jsonpointers
    - deserialize them in the right order to respect pointers graph
    :returns: a dict with key the path of the item and the value is the python object
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.dereference_jsonpointers(dict_)


def pointer_graph_elements(value, path='#'):
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.pointer_graph_elements(value=value, path=path)


def pointer_graph_elements_sequence(seq, path='#'):
    """
    Compute
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.pointer_graph_elements_sequence(seq=seq, path=path)


def pointer_graph_elements_dict(dict_, path='#'):
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.pointer_graph_elements_dict(dict_=dict_, path=path)


def pointers_analysis(obj):
    """
    Analyse on object to output stats on pointer use in the object
    :returns: a tuple of 2 dicts: one giving the number of pointer use by class
    """
    warnings.warn("Module serialization.py have been moved outside utils. Please use it instead")
    return dcs.pointers_analysis(obj)

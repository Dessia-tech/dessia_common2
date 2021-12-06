#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 24 19:24:53 2021

@author: steven
"""

from dessia_common.utils.types import isinstance_base_types, is_sequence, full_classname

# def basic_dict_diff(dict1, dict2):
#     missing_keys_in_other_object = []
#     diff_values = []
    
#     for key, value in dict1.items():
#         if key not in dict2:
#             missing_keys_in_other_object.append(key)
#         else:                
#             other_value = dict2[key]
#             if value != other_value:
#                 diff_values.append(key, value, other_value)
            
#     return diff_values, missing_keys_in_other_object


def diff(value1, value2, path='#'):
    diff_values = []
    missing_keys_in_other_object = []
    invalid_types = []
    
    if type(value1) != type(value2):
        invalid_types.append(path)
        return diff_values, missing_keys_in_other_object, invalid_types
    
    if isinstance_base_types(value1):
        if value1 != value2:
            diff_values.append((path, value1, value2))
        return diff_values, missing_keys_in_other_object, invalid_types
    elif is_sequence(value1):
        return sequence_diff(value1, value2, path=path)
    elif isinstance(value1, dict):
        return dict_diff(value1, value2, path=path)
    # elif hasattr(value1, '_data_eq'):
    else:
        # return diff_values, missing_keys_in_other_object, invalid_types
        raise NotImplementedError('niy')


def dict_diff(dict1, dict2, path='#'):
    missing_keys_in_other_object = []
    diff_values = []
    invalid_types = []
    
    for key, value in dict1.items():
        path_key = '{}/{}'.format(path, key)
        if key not in dict2:
            missing_keys_in_other_object.append(key)
        else:                
            dk, mkk, itk = diff(value, dict2[key], path=path_key)
            diff_values.extend(dk)
            missing_keys_in_other_object.extend(mkk)
            invalid_types.extend(itk)
            
    return diff_values, missing_keys_in_other_object, invalid_types

    
def sequence_diff(seq1, seq2, path='#'):
    diff_values = []
    missing_keys_in_other_object = []
    invalid_types = []
    
    if len(seq1) != len(seq2):
        diff_values.append((path, seq1, seq2))
    else:
        for iv, (v1, v2) in enumerate(zip(seq1, seq2)):
            path_value = '{}/{}'.format(path, iv)
            dv, mkv, itv = diff(v1, v2, path=path_value)
            diff_values.extend(dv)
            missing_keys_in_other_object.extend(mkv)
            invalid_types.extend(itv)
    return diff_values, missing_keys_in_other_object, invalid_types


def data_eq(value1, value2):
    if type(value1) != type(value2):
        return False
    
    if isinstance_base_types(value1):
        return value1 == value2
        
    if isinstance(value1, dict):
        return dict_data_eq(value1, value2)

    if is_sequence(value1):
        return sequence_data_eq(value1, value2)
        
    # Else: its an object
    if full_classname(value1) != full_classname(value2):
        return False

    eq_dict = value1._serializable_dict()
    if 'name' in eq_dict:
        del eq_dict['name']
        
    other_eq_dict = value2._serializable_dict()

    return dict_data_eq(eq_dict, other_eq_dict)


def dict_data_eq(dict1, dict2):
    
    for key, value in dict1.items():
        if key not in dict2:
            return False
        else:                
            if not data_eq(value, dict2[key]):
                return False
    return True
                            
    
def sequence_data_eq(seq1, seq2):
    if len(seq1) != len(seq2):
        return False
    else:
        for iv, (v1, v2) in enumerate(zip(seq1, seq2)):
            if not data_eq(v1, v2):
                return False
        
    return True
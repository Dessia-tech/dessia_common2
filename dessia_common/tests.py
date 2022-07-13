#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test module for dessia_common

"""
from time import sleep
from typing import List, Tuple
import random
import numpy as npy
from dessia_common import DessiaObject
import dessia_common.typings as dct
import dessia_common.files as dcf


class Submodel(DessiaObject):
    _standalone_in_db = True

    def __init__(self, subvalue: int, name: str = ''):
        self.subvalue = subvalue
        self.name = name

        DessiaObject.__init__(self, name=name)


class Model(DessiaObject):
    _standalone_in_db = True

    def __init__(self, value: int, submodel: Submodel, name: str = ''):
        self.value = value
        self.submodel = submodel

        DessiaObject.__init__(self, name=name)


class Generator(DessiaObject):
    _standalone_in_db = True
    _allowed_methods = ['long_generation']

    def __init__(self, parameter: int, nb_solutions: int = 25, name: str = ''):
        self.parameter = parameter
        self.nb_solutions = nb_solutions
        self.models = None

        DessiaObject.__init__(self, name=name)

    def generate(self) -> None:
        submodels = [Submodel(self.parameter * i)
                     for i in range(self.nb_solutions)]
        self.models = [Model(self.parameter + i, submodels[i])
                       for i in range(self.nb_solutions)]

    def long_generation(self, progress_callback=lambda x: None) -> List[Model]:
        """
        This method aims to test:
            * lots of prints to be catched
            * progress update
            * long computation
        """
        submodels = [Submodel(self.parameter * i)
                     for i in range(self.nb_solutions)]
        models = [Model(self.parameter + i, submodels[i])
                  for i in range(self.nb_solutions)]
        # Delay to simulate long generateion
        print('Beginning a long generation...')
        for i in range(500):
            print(f'Loop n°{i+1} / 500')
            progress = i / 499.
            progress_callback(progress)
            sleep(0.3)
        print('Generation complete')
        return models


class Optimizer(DessiaObject):
    _standalone_in_db = True

    def __init__(self, model_to_optimize: Model, name: str = ''):
        self.model_to_optimize = model_to_optimize

        DessiaObject.__init__(self, name=name)

    def optimize(self, optimization_value: int = 3) -> None:
        self.model_to_optimize.value += optimization_value


class Component(DessiaObject):
    _standalone_in_db = True

    def __init__(self, efficiency, name: str = ''):
        self.efficiency = efficiency
        DessiaObject.__init__(self, name=name)

    def power_simulation(self, power_value: dct.Power):
        return power_value * self.efficiency


class ComponentConnection(DessiaObject):
    def __init__(self, input_component: Component,
                 output_component: Component, name: str = ''):
        self.input_component = input_component
        self.output_component = output_component
        DessiaObject.__init__(self, name=name)


class SystemUsage(DessiaObject):
    _standalone_in_db = True

    def __init__(self, time: List[dct.Time], power: List[dct.Power],
                 name: str = ''):
        self.time = time
        self.power = power
        DessiaObject.__init__(self, name=name)


class System(DessiaObject):
    _standalone_in_db = True
    _dessia_methods = ['power_simulation']

    def __init__(self, components: List[Component],
                 component_connections: List[ComponentConnection],
                 name: str = ''):
        self.components = components
        self.component_connections = component_connections
        DessiaObject.__init__(self, name=name)

    def output_power(self, input_power: dct.Power):
        return input_power * 0.8

    def power_simulation(self, usage: SystemUsage):
        output_power = []
        for _, input_power in zip(usage.time, usage.power):
            output_power.append(self.output_power(input_power))
        return SystemSimulationResult(self, usage, output_power)


class SystemSimulationResult(DessiaObject):
    _standalone_in_db = True

    def __init__(self, system: System, system_usage: SystemUsage,
                 output_power: List[dct.Power], name: str = ''):
        self.system = system
        self.system_usage = system_usage
        self.output_power = output_power
        DessiaObject.__init__(self, name=name)


class SystemSimulationList(DessiaObject):
    _standalone_in_db = True

    def __init__(self, simulations: List[SystemSimulationResult],
                 name: str = ''):
        self.simulations = simulations
        DessiaObject.__init__(self, name=name)


class Car(DessiaObject):
    """
    Defines a car
    """
    _standalone_in_db = True
    _non_data_hash_attributes = ['name']

    def __init__(self, name: str, mpg: float, cylinders: int,
                 displacement: dct.Distance, horsepower: float,
                 weight: dct.Mass, acceleration: dct.Time, model: int,
                 origin: str):
        DessiaObject.__init__(self, name=name)

        self.mpg = mpg
        self.cylinders = cylinders
        self.displacement = displacement
        self.horsepower = horsepower
        self.weight = weight
        self.acceleration = acceleration
        self.model = model
        self.origin = origin

    def to_vector(self):
        list_formated_car = []
        for feature in self.vector_features():
            list_formated_car.append(getattr(self, feature.lower()))
        return list_formated_car

    @classmethod
    def from_csv(cls, file: dcf.StringFile, end: int = None, remove_duplicates: bool = False):
        """
        Generates Cars from given .csv file.
        """
        array = npy.genfromtxt(
            file, dtype=None, delimiter=',', names=True, encoding=None)
        cars = []
        for i, line in enumerate(array):
            if end is not None and i >= end:
                break
            if not remove_duplicates or (remove_duplicates and line.tolist() not in cars):
                attr_list = list(line)
                attr_list[3] /= 1000

                for i in range(len(attr_list)):
                    if isinstance(attr_list[i], npy.int64):
                        attr_list[i] = int(attr_list[i])
                    elif isinstance(attr_list[i], npy.float64):
                        attr_list[i] = float(attr_list[i])

                cars.append(cls(*attr_list))
        return cars


class CarWithFeatures(Car):
    _vector_features = ['mpg', 'displacement', 'horsepower', 'acceleration', 'weight']
    def __init__(self, name: str, mpg: float, cylinders: int,
                 displacement: dct.Distance, horsepower: float,
                 weight: dct.Mass, acceleration: dct.Time, model: int,
                 origin: str):
        Car.__init__(self, name, mpg, cylinders, displacement, horsepower,
                     weight, acceleration, model, origin)

    @classmethod
    def vector_features(cls):
        return cls._vector_features


class ClusTester_d1(DessiaObject):
    """
    Creates a dataset from a number of clusters and dimensions
    """
    _standalone_in_db = True
    _non_data_hash_attributes = ['name']
    _nb_dims = 1
    _vector_features = [f'p{i+1}' for i in range(_nb_dims)]

    def __init__(self, p1: float, name: str = ''):
        DessiaObject.__init__(self, name=name)
        self.p1 = p1


    @classmethod
    def vector_features(cls):
        return cls._vector_features


    @classmethod
    def create_dataset(cls, nb_clusters: int = 10, nb_points: int = 2500,
                       mean_borns: Tuple[float, float] = (-50., 50), std_borns: Tuple[float, float] = (-2., 2.)):
        means_list = []
        std_list = []
        data_list = []
        cluster_sizes = cls.set_cluster_sizes(nb_points, nb_clusters)

        for cluster_size in cluster_sizes:
            means_list = [random.uniform(*mean_borns) for i in range(cls._nb_dims)]
            std_list = [random.uniform(*std_borns) for i in range(cls._nb_dims)]
            for idx_point in range(cluster_size):
                new_data = cls(
                    *[random.normalvariate(means_list[dim], std_list[dim]) for dim in range(cls._nb_dims)])
                data_list.append(new_data)

        return data_list


    @staticmethod
    def set_cluster_sizes(nb_points: int, nb_clusters: int):
        current_nb_points = nb_points
        cluster_sizes = []
        for i in range(nb_clusters - 1):
            points_in_cluster = random.randint(int(current_nb_points / nb_clusters / 2),
                                               int(current_nb_points / nb_clusters * 2))
            cluster_sizes.append(points_in_cluster)
            current_nb_points -= points_in_cluster

        cluster_sizes.append(int(nb_points - npy.sum(cluster_sizes)))
        return cluster_sizes

    # @staticmethod
    # def plot(x_label: str, y_label: str, clustester_list: List[List[float]], **kwargs):
    #     x_coords = [getattr(clustester, x_label)
    #                 for clustester in clustester_list]
    #     y_coords = [getattr(clustester, y_label)
    #                 for clustester in clustester_list]
    #     import matplotlib.pyplot as plt
    #     plt.plot(x_coords, y_coords, **kwargs)
    #     return


class ClusTester_d2(ClusTester_d1):
    _nb_dims = 2
    _vector_features = [f'p{i+1}' for i in range(2)]
    def __init__(self, p1: float, p2: float, name: str = ''):
        ClusTester_d1.__init__(self, p1, name=name)
        self.p2 = p2

class ClusTester_d3(ClusTester_d2):
    _nb_dims = 3
    _vector_features = [f'p{i+1}' for i in range(3)]
    def __init__(self, p1: float, p2: float, p3: float, name: str = ''):
        ClusTester_d2.__init__(self, p1, p2, name=name)
        self.p3 = p3

class ClusTester_d4(ClusTester_d3):
    _nb_dims = 4
    _vector_features = [f'p{i+1}' for i in range(4)]
    def __init__(self, p1: float, p2: float, p3: float, p4: float, name: str = ''):
        ClusTester_d3.__init__(self, p1, p2, p3, name=name)
        self.p4 = p4

class ClusTester_d5(ClusTester_d4):
    _nb_dims = 5
    _vector_features = [f'p{i+1}' for i in range(5)]
    def __init__(self, p1: float, p2: float, p3: float, p4: float, p5: float, name: str = ''):
        ClusTester_d4.__init__(self, p1, p2, p3, p4, name=name)
        self.p5 = p5

class ClusTester_d6(ClusTester_d5):
    _nb_dims = 6
    _vector_features = [f'p{i+1}' for i in range(6)]
    def __init__(self, p1: float, p2: float, p3: float, p4: float, p5: float,
                 p6: float, name: str = ''):
        ClusTester_d5.__init__(self, p1, p2, p3, p4, p5, name=name)
        self.p6 = p6

class ClusTester_d7(ClusTester_d6):
    _nb_dims = 7
    _vector_features = [f'p{i+1}' for i in range(7)]
    def __init__(self, p1: float, p2: float, p3: float, p4: float, p5: float,
                 p6: float, p7: float, name: str = ''):
        ClusTester_d6.__init__(self, p1, p2, p3, p4, p5, p6, name=name)
        self.p7 = p7

class ClusTester_d8(ClusTester_d7):
    _nb_dims = 8
    _vector_features = [f'p{i+1}' for i in range(8)]
    def __init__(self, p1: float, p2: float, p3: float, p4: float, p5: float,
                 p6: float, p7: float, p8: float, name: str = ''):
        ClusTester_d7.__init__(self, p1, p2, p3, p4, p5, p6, p7, name=name)
        self.p8 = p8

class ClusTester_d9(ClusTester_d8):
    _nb_dims = 9
    _vector_features = [f'p{i+1}' for i in range(9)]
    def __init__(self, p1: float, p2: float, p3: float, p4: float, p5: float,
                 p6: float, p7: float, p8: float, p9: float, name: str = ''):
        ClusTester_d8.__init__(self, p1, p2, p3, p4, p5, p6, p7, p8, name=name)
        self.p9 = p9

class ClusTester_d10(ClusTester_d9):
    _nb_dims = 10
    _vector_features = [f'p{i+1}' for i in range(10)]
    def __init__(self, p1: float, p2: float, p3: float, p4: float, p5: float,
                 p6: float, p7: float, p8: float, p9: float, p10: float, name: str = ''):
        ClusTester_d9.__init__(self, p1, p2, p3, p4, p5, p6, p7, p8, p9, name=name)
        self.p10 = p10

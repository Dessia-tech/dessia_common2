"""
Tests for dessia_common.HeterogeneousList class (loadings, check_platform and plots)
"""
import random
from dessia_common.core import DessiaObject
from dessia_common.models import all_cars_no_feat, all_cars_wi_feat, rand_data_middl
from dessia_common.datatools import covariance, manhattan_distance, euclidian_distance, minkowski_distance, inf_norm,\
    mahalanobis_distance
from dessia_common.datatools import HeterogeneousList

# Tests on common_attributes
class Bidon(DessiaObject):
    def __init__(self, attr1: float = 1.2):
        self.attr1 = attr1
        self.attr2 = attr1*2
    @property
    def prop1(self):
        return self.attr1 + self.attr2

bidon = Bidon()
bidon_hlist = HeterogeneousList([bidon]*3)
assert(bidon_hlist.common_attributes == ['attr1'])

# Tests on common_attributes
class Bidon(DessiaObject):
    _vector_features = ['attr1', 'attr2', 'prop1', 'in_to_vector']
    def __init__(self, attr1: float = 1.2):
        self.attr1 = attr1
        self.attr2 = attr1*2
    @property
    def prop1(self):
        return self.attr1 + self.attr2
    def to_vector(self):
        return [self.attr1, self.attr2, self.prop1, random.randint(0, 32)]

bidon = Bidon()
bidon_hlist = HeterogeneousList([bidon]*3)
assert(bidon_hlist.common_attributes == ['attr1', 'attr2', 'prop1', 'in_to_vector'])

# When attribute _features is not specified in class Car
all_cars_without_features = HeterogeneousList(all_cars_no_feat)

# When attribute _features is specified in class CarWithFeatures
all_cars_with_features = HeterogeneousList(all_cars_wi_feat)
# Auto-generated heterogeneous dataset with nb_clusters clusters of points in nb_dims dimensions
RandData_heterogeneous = HeterogeneousList(rand_data_middl)

# Compute one common_attributes
all_cars_without_features.common_attributes

# Check platform for datasets
all_cars_with_features._check_platform()
all_cars_without_features._check_platform()
RandData_heterogeneous._check_platform()

# Test __getitem__
picked_list = (all_cars_with_features[250:] +
               RandData_heterogeneous[:50][[1, 4, 6, 10, 25]][[True, False, True, True, False]])
assert(picked_list._common_attributes is None)
assert(picked_list._matrix is None)
assert(picked_list[-1] == rand_data_middl[10])
try:
    all_cars_without_features[[True, False, True]]
    raise ValueError("boolean indexes of len 3 should not be able to index HeterogeneousLists of len 406")
except Exception as e:
    assert(e.args[0] == "Cannot index HeterogeneousList object of len 406 with a list of boolean of len 3")

# Test on matrice
idx = random.randint(0, len(all_cars_without_features) - 1)
assert(all(item in all_cars_without_features.matrix[idx]
            for item in [getattr(all_cars_without_features.dessia_objects[idx], attr)
                        for attr in all_cars_without_features.common_attributes]))

# Tests for displays
hlist_cars_plot_data = all_cars_without_features.plot_data()
# all_cars_without_features.plot()
# all_cars_with_features.plot()
# RandData_heterogeneous.plot()
# assert(json.dumps(hlist_cars_plot_data[0].to_dict())[150:200] == 'acceleration": 12.0, "model": 70.0}, {"mpg": 15.0,')
# assert(json.dumps(hlist_cars_plot_data[1].to_dict())[10500:10548] == 'celeration": 12.5, "model": 72.0},
#        {"mpg": 13.0,')
# assert(json.dumps(hlist_cars_plot_data[2].to_dict())[50:100] == 'te_names": ["Index of reduced basis vector", "Sing')
print(all_cars_with_features)

# Tests for metrics
assert(int(all_cars_with_features.distance_matrix('minkowski')[25][151]) == 186)
assert(int(all_cars_with_features.mean()[3]) == 15)
assert(int(all_cars_with_features.standard_deviation()[4]) == 845)
assert(int(all_cars_with_features.variances()[2]) == 1637)
assert(int(manhattan_distance(all_cars_with_features.matrix[3], all_cars_with_features.matrix[125])) == 1361)
assert(int(minkowski_distance(all_cars_with_features.matrix[3], all_cars_with_features.matrix[125], mink_power=7.2)) == 1275)
assert(int(euclidian_distance(all_cars_with_features.matrix[3], all_cars_with_features.matrix[125])) == 1277)
assert(int(covariance(all_cars_with_features.matrix[3], all_cars_with_features.matrix[125])) == 1155762)
assert(int(inf_norm([1,2,3,45,4.,4.21515,-12,-0,0,-25214.1511])) == 25214)
assert(int(mahalanobis_distance(all_cars_with_features.matrix[3],
                                all_cars_with_features.matrix[125],
                                all_cars_with_features.covariance_matrix())) == 2)

# Tests for empty HeterogeneousList
empty_list = HeterogeneousList()
print(empty_list)
assert(empty_list[0] == [])
assert(empty_list[:] == [])
assert(empty_list[[False, True]] == [])
assert(empty_list + empty_list == HeterogeneousList())
assert(empty_list + all_cars_without_features == all_cars_without_features)
assert(all_cars_without_features + empty_list == all_cars_without_features)
assert(len(empty_list) == 0)
assert(empty_list.matrix == [])
assert(empty_list.common_attributes == [])
empty_list.sort(0)
assert(empty_list == HeterogeneousList())
empty_list.sort("weight")
assert(empty_list == HeterogeneousList())

try:
    empty_list.plot_data()
    raise ValueError("plot_data should not work on empty HeterogeneousLists")
except Exception as e:
    assert(e.__class__.__name__ == "ValueError")
try:
    empty_list.singular_values()
    raise ValueError("singular_values should not work on empty HeterogeneousLists")
except Exception as e:
    assert(e.__class__.__name__ == "ValueError")

# Tests sort
all_cars_with_features.sort('weight', ascend=False)
assert(all_cars_with_features[0].weight == max(all_cars_with_features.get_attribute_values('weight')))

idx_dpl = all_cars_without_features.common_attributes.index('displacement')
all_cars_without_features.sort(idx_dpl)
assert(all(attr in ['displacement', 'cylinders', 'mpg', 'horsepower', 'weight', 'acceleration', 'model']
           for attr in all_cars_without_features.common_attributes))
assert(all_cars_without_features[0].displacement == min(all_cars_without_features.get_column_values(idx_dpl)))

# Missing tests after coverage report
assert(all_cars_without_features[[]] == empty_list)
all_cars_without_features.extend(all_cars_without_features)
assert(len(all_cars_without_features._matrix) == 812)
try:
    all_cars_without_features[float]
    raise ValueError("float should not work as __getitem__ object for HeterogeneousList")
except Exception as e:
    assert(e.args[0] == "key of type <class 'type'> not implemented for indexing HeterogeneousLists")

try:
    all_cars_without_features[[float]]
    raise ValueError("float should not work as __getitem__ object for HeterogeneousList")
except Exception as e:
    assert(e.args[0] == "key of type <class 'list'> with <class 'type'> elements not implemented for indexing " +
           "HeterogeneousLists")

try:
    covariance([1,2], [1])
    raise ValueError("covariance should be able to compute on lists of different lengths")
except Exception as e:
    assert(e.args[0] == "vector_x and vector_y must be the same length to compute covariance.")


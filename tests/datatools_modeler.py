"""
Tests for dessia_common.datatools.modeler file.
"""
from dessia_common.models import all_cars_no_feat
from dessia_common.datatools.dataset import Dataset
import dessia_common.datatools.models as models
from dessia_common.datatools.modeler import Modeler, ModelValidation, CrossValidation, ValidationData

# TODO review the way data are generated
# Load Data and put it in a Dataset (matrix is automatically computed)
dataset_example = Dataset(all_cars_no_feat)
input_names = ['displacement', 'horsepower', 'model', 'acceleration', 'cylinders']
output_names = ['mpg', 'weight']
# inputs = dataset_example.sub_matrix(input_names)
# double_outputs = dataset_example.sub_matrix(output_names)
# inputs_train, inputs_test, outputs_train, outputs_test = models.train_test_split(inputs, double_outputs, ratio=0.7)

# Tests for matrix
models_class, hyperparameters = models.RandomForestRegressor.init_for_modeler(n_estimators=2, max_depth=None)
# models_class, hyperparameters = models.Ridge.init_for_modeler(alpha=10, fit_intercept=True, tol=0.1)
# models_class, hyperparameters = models.MLPRegressor.init_for_modeler(hidden_layer_sizes=(1000,500,500), activation='relu')
modeler, cross_validation = Modeler.cross_validation(dataset_example, input_names, output_names, models_class,
                                                     hyperparameters, True, True, 3, 0.8, "test_modeler")
cross_validation.plot()



modeler = Modeler.fit_dataset(dataset_example, input_names, output_names, models_class, hyperparameters, True, True,
                              "test_modeler")

# validation_data = ValidationData.from_dataset(dataset_example, input_names, output_names)
test = CrossValidation.from_dataset(modeler, dataset_example, input_names, output_names, 5, 0.8, "validation_test")
test.plot()

# pp=modeler._plot_data_list(inputs_train, outputs_train, modeler.predict_matrix(inputs_train), input_names, output_names)

# modeler.plot(ref_inputs=inputs_train, ref_outputs=outputs_train, val_inputs=inputs_test, val_outputs=outputs_test,
#              input_names=input_names, output_names=output_names)
# modeler.score(inputs_train, outputs_train)

# test_mdlr = Modeler.from_dataset_fit_validate(dataset_example, input_names, output_names, models_class, hyperparameters,
#                                               True, True, 0.8, True, 'pouet')

# test = Modeler.cross_validation(dataset=dataset_example, input_names=input_names, output_names=output_names, class_=models_class,
#                                 hyperparameters=hyperparameters, input_is_scaled=True, output_is_scaled=True, nb_tests=5,
#                                 ratio=0.8, name='')

# test = Modeler(None,None,None).plot(dataset=dataset_example, input_names=input_names, output_names=output_names, class_=models_class,
#                                 hyperparameters=hyperparameters, input_is_scaled=True, output_is_scaled=True, nb_tests=5,
#                                 ratio=0.8, name='')


# print(test_mdlr[1])

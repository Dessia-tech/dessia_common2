"""
Tests for dessia_common.datatools.modeler file.
"""
from dessia_common.models import all_cars_no_feat
from dessia_common.datatools.dataset import Dataset
import dessia_common.datatools.models as models
from dessia_common.datatools.modeler import Modeler, CrossValidation #, ValidationData, ModelValidation

# ======================================================================================================================
#                                            F R O M   D A T A S E T
# ======================================================================================================================

# Load data and put it in a Dataset (matrix is automatically computed)
dataset_for_fit = Dataset(all_cars_no_feat)[:-10]
dataset_to_pred = Dataset(all_cars_no_feat)[-10:]
input_names_reg = ['displacement', 'horsepower', 'model', 'acceleration', 'cylinders']
output_names_reg = ['mpg', 'weight']
output_names_reg_solo = ['weight']
input_names_clf = ['displacement', 'horsepower', 'model', 'acceleration', 'mpg', 'weight']
output_names_clf = ['cylinders']

# Load class of models with their hyperparameters
Ri_class, Ri_hyperparams = models.Ridge.init_for_modeler(alpha=0.01, fit_intercept=True, tol=0.01)
LR_class, LR_hyperparams = models.LinearRegression.init_for_modeler(fit_intercept=True, positive=False)
DR_class, DR_hyperparams = models.DecisionTreeRegressor.init_for_modeler(criterion='squared_error', max_depth=None)
DC_class, DC_hyperparams = models.DecisionTreeClassifier.init_for_modeler(criterion='gini', max_depth=None)
RR_class, RR_hyperparams = models.RandomForestRegressor.init_for_modeler(n_estimators=10, criterion='squared_error',
                                                                         max_depth=None)
RC_class, RC_hyperparams = models.RandomForestClassifier.init_for_modeler(n_estimators=10, criterion='gini',
                                                                          max_depth=None)
MR_class, MR_hyperparams = models.MLPRegressor.init_for_modeler(hidden_layer_sizes=(50, 50, 50), activation='relu',
                                                                max_iter=500)
MC_class, MC_hyperparams = models.MLPClassifier.init_for_modeler(hidden_layer_sizes=(50, 50, 50), activation='relu',
                                                                 max_iter=500)

# Train models and predict data
Ri_mdlr, Ri_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_reg, output_names_reg_solo,
                                               Ri_class, Ri_hyperparams, True, True, "ridge_modeler")
LR_mdlr, LR_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_reg, output_names_reg_solo,
                                               LR_class, LR_hyperparams, True, True, "linear_regression_modeler")
DR_mdlr, DR_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_reg, output_names_reg_solo,
                                               DR_class, DR_hyperparams, True, True, "DTRegressor_modeler")
DC_mdlr, DC_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_clf, output_names_clf,
                                               DC_class, DC_hyperparams, True, False, "DTClassifier_modeler")
RR_mdlr, RR_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_reg, output_names_reg_solo,
                                               RR_class, RR_hyperparams, True, True, "RFRegressor_modeler")
RC_mdlr, RC_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_clf, output_names_clf,
                                               RC_class, RC_hyperparams, True, False, "RFClassifier_modeler")
MR_mdlr, MR_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_reg, output_names_reg_solo,
                                               MR_class, MR_hyperparams, True, True, "MLPRegressor_modeler")
MC_mdlr, MC_pred = Modeler.fit_predict_dataset(dataset_for_fit, dataset_to_pred, input_names_clf, output_names_clf,
                                               MC_class, MC_hyperparams, True, False, "MLPClassifier_modeler")
# TODO: make impossible scaling for classifier (set to False in any case)

# Run cross_validation for all models instantiated in a Modeler
CV_Ri = CrossValidation.from_dataset(Ri_mdlr, dataset_for_fit, input_names_reg, output_names_reg_solo, 3, 0.8)
CV_LR = CrossValidation.from_dataset(LR_mdlr, dataset_for_fit, input_names_reg, output_names_reg_solo, 3, 0.8)
CV_DR = CrossValidation.from_dataset(DR_mdlr, dataset_for_fit, input_names_reg, output_names_reg_solo, 3, 0.8)
CV_DC = CrossValidation.from_dataset(DC_mdlr, dataset_for_fit, input_names_clf, output_names_clf, 3, 0.8)
CV_RR = CrossValidation.from_dataset(RR_mdlr, dataset_for_fit, input_names_reg, output_names_reg_solo, 3, 0.8)
CV_RC = CrossValidation.from_dataset(RC_mdlr, dataset_for_fit, input_names_clf, output_names_clf, 3, 0.8)
CV_MR = CrossValidation.from_dataset(MR_mdlr, dataset_for_fit, input_names_reg, output_names_reg_solo, 3, 0.8)
CV_MC = CrossValidation.from_dataset(MC_mdlr, dataset_for_fit, input_names_clf, output_names_clf, 3, 0.8)

# Plot cross validations
CV_Ri.plot()
CV_LR.plot()
CV_DR.plot()
CV_DC.plot()
CV_RR.plot()
CV_RC.plot()
CV_MR.plot()
CV_MC.plot()

# ======================================================================================================================
#                                            F R O M   M A T R I X
# ======================================================================================================================
# inputs = dataset_example.sub_matrix(input_names)
# double_outputs = dataset_example.sub_matrix(output_names)
# inputs_train, inputs_test, outputs_train, outputs_test = models.train_test_split(inputs, double_outputs, ratio=0.7)

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

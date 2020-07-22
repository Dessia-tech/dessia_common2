from dessia_common.vectored_objects import Catalog, ParetoSettings
import dessia_common.workflow as wf

choice_args = ['MPG', 'Cylinders', 'Displacement', 'Horsepower',
               'Weight', 'Acceleration', 'Model']  # Ordered

minimized_attributes = {'MPG': False, 'Horsepower': True,
                        'Weight': True, 'Acceleration': False}

aimpoint = {'MPG': 4, 'Weight': 1000}

# Blocks
import_csv = wf.Import(type_='csv')
instantiate_pareto = wf.InstanciateModel(model_class=ParetoSettings,
                                         name='Pareto Settings')
instantiate_catalog = wf.InstanciateModel(model_class=Catalog,
                                          name='Cars Instantiation')
objectives_method = wf.ModelMethod(model_class=Catalog,
                                   method_name='find_best_objective',
                                   name="Find best objectives")
objectives_attributes = wf.ModelAttribute(attribute_name='objectives',
                                          name='Objectives')
array_attributes = wf.ModelAttribute(attribute_name='array',
                                     name='Array')

indices_method = wf.ModelMethod(model_class=Catalog,
                                method_name='get_variable_index',
                                name='Indices')
subblocks = [indices_method]
subworkflow = wf.Workflow(blocks=subblocks, pipes=[],
                          output=indices_method.outputs[0],
                          name='ForEach workflow')
workflow_block = wf.WorkflowBlock(workflow=subworkflow,
                                  name='ForEach workflow_block')
for_each_variable = wf.ForEach(workflow_block=workflow_block,
                               workflow_iterable_input=workflow_block.inputs[0],
                               name='ForEach variable')

blocks = [import_csv, instantiate_pareto, instantiate_catalog,
          objectives_method, objectives_attributes, array_attributes,
          for_each_variable]

# Pipes
pipe0 = wf.Pipe(import_csv.outputs[0], instantiate_catalog.inputs[0])
pipe1 = wf.Pipe(import_csv.outputs[1], instantiate_catalog.inputs[1])
pipe2 = wf.Pipe(instantiate_pareto.outputs[0], instantiate_catalog.inputs[2])
pipe3 = wf.Pipe(instantiate_catalog.outputs[0], objectives_method.inputs[0])
# pipe4 = wf.Pipe(instantiate_catalog.outputs[0], for_each_variable.inputs[0])
pipe5 = wf.Pipe(objectives_method.outputs[1], objectives_attributes.inputs[0])
pipe6 = wf.Pipe(instantiate_catalog.outputs[0], array_attributes.inputs[0])
pipes = [pipe0, pipe1, pipe2, pipe3, pipe5, pipe6]

# Workflow
workflow = wf.Workflow(blocks=blocks, pipes=pipes,
                       output=array_attributes.outputs[0],
                       name='Cars workflow')
workflow.plot_jointjs()

# # Input values
input_values = {workflow.index(import_csv.inputs[0]): 'cars.csv',
                workflow.index(instantiate_pareto.inputs[0]): minimized_attributes,
                workflow.index(instantiate_pareto.inputs[1]): True,
                workflow.index(instantiate_catalog.inputs[4]): choice_args,
                workflow.index(instantiate_catalog.inputs[3]): [],
                workflow.index(instantiate_catalog.inputs[5]): 'Cars',
                workflow.index(objectives_method.inputs[1]): aimpoint,
                workflow.index(objectives_method.inputs[2]): minimized_attributes,
                workflow.index(for_each_variable.inputs[0]): choice_args}
workflow_run = workflow.run(input_variables_values=input_values)

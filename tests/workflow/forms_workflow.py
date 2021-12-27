from dessia_common.workflow import InstantiateModel, ModelMethod,\
    TypedVariable, ModelAttribute, Pipe, Workflow, WorkflowBlock,\
    ForEach, MultiPlot, WorkflowRun
from dessia_common.forms import Generator, Optimizer
from dessia_common import MethodType
import json

instanciate_generator = InstantiateModel(model_class=Generator,
                                         name='Instantiate Generator')

generate_method = MethodType(class_=Generator, name='generate')
generator_generate = ModelMethod(method_type=generate_method,
                                 name='Generator Generate')
attribute_selection = ModelAttribute(attribute_name='models',
                                     name='Attribute Selection')

# Subworkflow of model optimization
instanciate_optimizer = InstantiateModel(model_class=Optimizer,
                                         name='Instantiate Optimizer')


generate_method = MethodType(class_=Optimizer, name='optimize')
optimization = ModelMethod(method_type=generate_method, name='Optimization')

model_fetcher = ModelAttribute(attribute_name='model_to_optimize',
                               name='Model Fetcher')

pipe1_opt = Pipe(input_variable=instanciate_optimizer.outputs[0],
                 output_variable=optimization.inputs[0])
pipe2_opt = Pipe(input_variable=optimization.outputs[1],
                 output_variable=model_fetcher.inputs[0])
optimization_blocks = [instanciate_optimizer, optimization, model_fetcher]
optimization_pipes = [pipe1_opt, pipe2_opt]
optimization_workflow = Workflow(blocks=optimization_blocks,
                                 pipes=optimization_pipes,
                                 output=model_fetcher.outputs[0],
                                 name='Optimization Workflow')

optimization_workflow_block = WorkflowBlock(workflow=optimization_workflow,
                                            name='Workflow Block')

parallel_optimization = ForEach(workflow_block=optimization_workflow_block,
                                iter_input_index=0, name='ForEach')

display_attributes = ['intarg', 'strarg', 'standalone_subobject/floatarg']
display = MultiPlot(attributes=display_attributes, name='Display')

int_variable = TypedVariable(type_=int, name="Some Integer")
name_variable = TypedVariable(type_=str, name="Shared Name")

pipe_int_1 = Pipe(input_variable=int_variable,
                  output_variable=instanciate_generator.inputs[1])
pipe_name_1 = Pipe(input_variable=name_variable,
                   output_variable=instanciate_generator.inputs[2])
pipe_name_2 = Pipe(input_variable=name_variable,
                   output_variable=parallel_optimization.inputs[1])
pipe_1 = Pipe(input_variable=instanciate_generator.outputs[0],
              output_variable=generator_generate.inputs[0])
pipe_2 = Pipe(input_variable=generator_generate.outputs[1],
              output_variable=attribute_selection.inputs[0])
pipe_3 = Pipe(input_variable=attribute_selection.outputs[0],
              output_variable=parallel_optimization.inputs[0])
pipe_4 = Pipe(input_variable=parallel_optimization.outputs[0],
              output_variable=display.inputs[0])

blocks = [instanciate_generator, generator_generate,
          attribute_selection, parallel_optimization, display]
pipes = [pipe_int_1, pipe_name_1, pipe_name_2, pipe_1, pipe_2, pipe_3, pipe_4]
workflow_ = Workflow(blocks=blocks, pipes=pipes,
                     output=parallel_optimization.outputs[0])

# Check Workflow
serialized_workflow = workflow_.to_dict()
deserialized_workflow = Workflow.dict_to_object(dict_=serialized_workflow)

assert hash(workflow_) == hash(deserialized_workflow)

input_values = {0: 5}
workflow_run = workflow_.run(input_values=input_values,
                             verbose=True, name='Dev Objects')

# Check WorkflowRun
# Assert to_dict, dict_to_object, hashes, eqs
dict_ = workflow_run.to_dict()
object_ = WorkflowRun.dict_to_object(dict_=dict_)

assert hash(workflow_run) == hash(object_)

# Assert deserialization
demo_workflow_dict = workflow_.to_dict()
demo_workflow_json = json.dumps(demo_workflow_dict)
dict_from_json = json.loads(demo_workflow_json)
deserialized_demo_workflow = Workflow.dict_to_object(dict_from_json)
assert workflow_ == deserialized_demo_workflow


# Check WorkflowState
workflow_state = workflow_.start_run({})
input_values = {0: 5, 3: "Test", 2: 2}
workflow_state.add_block_input_values(0, input_values)


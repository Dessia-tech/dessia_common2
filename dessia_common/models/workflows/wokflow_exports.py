"""
Script for workflow with exports creationZ
"""

from dessia_common.workflow import InstantiateModel, ModelMethod, TypedVariable,\
    ModelAttribute, Pipe, Workflow, WorkflowBlock, ForEach, ExportJson, ExportExcel, Export, \
    Unpacker, Archive, MultiPlot
from dessia_common.forms import Generator, Optimizer, StandaloneObject
from dessia_common.typings import MethodType
from dessia_common import DessiaObject

inst = InstantiateModel(model_class=Generator, name='Instantiate Generator')

generate_method = MethodType(class_=Generator, name='generate')
gene = ModelMethod(method_type=generate_method, name='Generator Generate')
attr = ModelAttribute(attribute_name='models', name='Attribute Selection')

# Subworkflow of model optimization
opti = InstantiateModel(model_class=Optimizer, name='Instantiate Optimizer')


optimize_method = MethodType(class_=Optimizer, name='optimize')
optimization = ModelMethod(method_type=optimize_method, name='Optimization')

model_fetcher = ModelAttribute(attribute_name='model_to_optimize', name='Model Fetcher')

pipe1_opt = Pipe(input_variable=opti.outputs[0], output_variable=optimization.inputs[0])
pipe2_opt = Pipe(input_variable=optimization.outputs[1], output_variable=model_fetcher.inputs[0])
opti_blocks = [opti, optimization, model_fetcher]
opti_pipes = [pipe1_opt, pipe2_opt]
opti_workflow = Workflow(blocks=opti_blocks, pipes=opti_pipes,
                         output=model_fetcher.outputs[0], name='Optimization Workflow')

optimization_workflow_block = WorkflowBlock(workflow=opti_workflow, name='Workflow Block')

parallel_optimization = ForEach(workflow_block=optimization_workflow_block, iter_input_index=0, name='ForEach')

display_attributes = ['intarg', 'strarg', 'standalone_subobject/floatarg']
display_ = MultiPlot(attributes=display_attributes, name='Display')

unpack_results = Unpacker(indices=[0], name="Unpack Results")

# export_txt = ExportJson(model_class=Generator, name="Export JSON")
# export_xlsx = ExportExcel(model_class=StandaloneObject, name="Export XLSX")

xlsx_method_type = MethodType(class_=DessiaObject, name="to_xlsx_stream")

export_txt = Export(export_name="Export txt", name="Export Json")
export_xlsx = Export(method_type=xlsx_method_type, text=False, extension="xlsx",
                     export_name="Export excel", name="Export Xlsx")

zip_export = Archive(number_exports=2, name="Zip")

int_variable = TypedVariable(type_=int, name="Some Integer")

pipe_int_1 = Pipe(input_variable=int_variable, output_variable=inst.inputs[1])
pipe_1 = Pipe(input_variable=inst.outputs[0], output_variable=gene.inputs[0])
pipe_2 = Pipe(input_variable=gene.outputs[1], output_variable=attr.inputs[0])
pipe_3 = Pipe(input_variable=attr.outputs[0], output_variable=parallel_optimization.inputs[0])
pipe_4 = Pipe(input_variable=parallel_optimization.outputs[0], output_variable=unpack_results.inputs[0])
pipe_5 = Pipe(input_variable=inst.outputs[0], output_variable=export_txt.inputs[0])
pipe_6 = Pipe(input_variable=unpack_results.outputs[0], output_variable=export_xlsx.inputs[0])

pipe_display = Pipe(input_variable=parallel_optimization.outputs[0], output_variable=display_.inputs[0])

pipe_export_1 = Pipe(input_variable=export_txt.outputs[0], output_variable=zip_export.inputs[0])
pipe_export_2 = Pipe(input_variable=export_xlsx.outputs[0], output_variable=zip_export.inputs[1])

blocks = [inst, gene, attr, parallel_optimization,
          display_, unpack_results, export_txt, zip_export, export_xlsx]
pipes = [pipe_int_1, pipe_1, pipe_2, pipe_3, pipe_4, pipe_5, pipe_6, pipe_display, pipe_export_1, pipe_export_2]
workflow_export = Workflow(blocks=blocks, pipes=pipes, output=parallel_optimization.outputs[0],
                           name="Workflow Test Export")

# workflow_export.save_script_to_file('workflow_export')

workflow_export_state = workflow_export.start_run()
workflow_export_state.name = "WorkflowState Test Export"

input_values = {workflow_export.input_index(inst.inputs[0]): 0,
                workflow_export.input_index(inst.inputs[1]): 5}

workflow_export_run = workflow_export.run(input_values)

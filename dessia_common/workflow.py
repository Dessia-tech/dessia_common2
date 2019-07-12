#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import inspect
import networkx as nx


class Variable:
    def __init__(self, name):
        self.name = name

class Block:
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs
        

class InstanciateModel:
    def __init__(self, object_class):
        self.object_class = object_class
        
        inputs = []
        for arg_name, parameter in inspect.signature(self.object_class.__init__).parameters.items():
            if arg_name != 'self':
                inputs.append(Variable(arg_name))
        outputs = [Variable('Instanciated object')]
        Block.__init__(self, inputs, outputs)
        
    def evaluate(self, values):
        return [self.object_class(*values)]


class ModelMethod(Block):
    def __init__(self, model_class, method_name):
        self.model_class = model_class
        self.method_name = method_name
        inputs = [Variable('model at input')]
        for arg_name, parameter in inspect.signature(getattr(self.model_class, self.method_name)).parameters.items():
            if arg_name != 'self':
                inputs.append(Variable(arg_name))
        outputs = [Variable('method result of {}'.format(self.method_name)),
                   Variable('model at output {}'.format(self.method_name))]
        Block.__init__(self, inputs, outputs)
        
    def evaluate(self, values):
        return [getattr(values[0], self.method_name)(*values[1:]), values[0]]
        
class Function(Block):
    def __init__(self, function):
        self.function = function
        inputs = []
        for arg_name, parameter in inspect.signature(function).parameters.items():
            inputs.append(Variable(arg_name))
        outputs = [Variable('Output function')]
        
        Block.__init__(self, inputs, outputs)
        
    def evaluate(self, values):
        return self.function(*values)

        
class ForEach(Block):
    def __init__(self, workflow):
        self.workflow = workflow
        input_variable = Variable('Foreach input')
        output_variable = Variable('Foreach output')
        
        Block.__init__(self, [input_variable], [output_variable])

    def evaluate(self, values):
        output_values = []
        for value in values[0]:
            workflow_run = self.workflow.run([value])
            output_values.append(workflow_run.output_value)
        return [output_values]
            

class ModelAttribute:
    def __init__(self, attribute_name):
        self.attribute_name = attribute_name
        
        Block.__init__(self, [Variable('Model')], [Variable('Model attribute')])

    def evaluate(self, values):
        return [getattr(values[0], self.attribute_name)]

class Pipe:
    def __init__(self,
                 input_variable,
                 output_variable):
        self.input_variable = input_variable
        self.output_variable = output_variable



class WorkFlow(Block):
    def __init__(self, blocks, pipes, output):
        self.blocks = blocks
        self.pipes = pipes
        
        self.variables = []
        for block in self.blocks:
            self.variables.extend(block.inputs)
            self.variables.extend(block.outputs)
            
        self._utd_graph = False

        input_variables = []
        
        for variable in self.variables:
            if len(nx.ancestors(self.graph, variable)) == 0:
                input_variables.append(variable)

        Block.__init__(self, input_variables, [output])
                
    def _get_graph(self):
        if not self._utd_graph:        
            self._cached_graph = self._graph()
            self._utd_graph = True
        return self._cached_graph
            
    graph = property(_get_graph)
    
    def _graph(self):
        graph = nx.DiGraph()
        graph.add_nodes_from(self.variables)
        graph.add_nodes_from(self.blocks)
        for block in self.blocks:
            for input_parameter in block.inputs:
                graph.add_edge(input_parameter, block)
            for output_parameter in block.outputs:
                graph.add_edge(block, output_parameter)
                
        for pipe in self.pipes:
            graph.add_edge(pipe.input_variable, pipe.output_variable)
        return graph
        
    
    def plot_graph(self):
        
        pos = nx.kamada_kawai_layout(self.graph)
        nx.draw_networkx_nodes(self.graph, pos, self.blocks,
                               node_shape='s', node_color='grey')
        nx.draw_networkx_nodes(self.graph, pos, self.variables, node_color='b')
        nx.draw_networkx_nodes(self.graph, pos, self.inputs, node_color='g')
        nx.draw_networkx_nodes(self.graph, pos, self.outputs, node_color='r')
        nx.draw_networkx_edges(self.graph, pos)
        

        labels = {}#b: b.function.__name__ for b in self.block}
        for block in self.blocks:
            labels[block] = block.__class__.__name__
            for variable in self.variables:
                labels[variable] = variable.name
#            labels[function.output] = 'Output function'
        nx.draw_networkx_labels(self.graph, pos, labels)


    def run(self, input_variables_values):
        activated_items = {p: False for p in self.pipes}
        activated_items.update({v: False for v in self.variables})
        activated_items.update({b: False for b in self.blocks})
        print(input_variables_values, self.inputs)
        if len(input_variables_values) != len(self.inputs):
            raise ValueError
            
        values = {}
        
        for input_value, variable in zip(input_variables_values,
                                         self.inputs):
            values[variable] = input_value
            activated_items[variable] = True
        
        something_activated = True
        
        while something_activated:
            something_activated = False
            
            for pipe in self.pipes:
                if not activated_items[pipe]:
                    if activated_items[pipe.input_variable]:
                        activated_items[pipe] = True
                        values[pipe.output_variable] = values[pipe.input_variable]
                        activated_items[pipe.output_variable] = True
                        something_activated = True
            
            for block in self.blocks:
                if not activated_items[block]:
                    all_inputs_activated = True
                    for function_input in block.inputs:
                        
                        if not activated_items[function_input]:
                            all_inputs_activated = False
                            break
                        
                    if all_inputs_activated:
                        output_values = block.evaluate([values[i]\
                                                          for i in block.inputs])
                        for output, output_value in zip(block.outputs, output_values):                            
                            values[output] = output_value
                            activated_items[output] = True
                        
                        activated_items[block] = True
                        something_activated = True
                        
        return WorkflowRun(self, values)
            
                            
class WorkflowRun:
    def __init__(self, workflow, values):
        self.workflow = workflow
        self.values = values
        
        self.output_value = self.values[self.workflow.outputs[0]]

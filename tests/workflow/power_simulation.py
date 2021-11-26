#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

from dessia_common import DessiaObject

from dessia_common.models.workflows import simulation_workflow
from dessia_common.models.power_test import components1, component_connections1, usage1


workflow_run = simulation_workflow.run({0: components1, 1:component_connections1, 3:usage1})
print(workflow_run.log)

workflow_run2 = DessiaObject.dict_to_object(workflow_run.to_dict())
workflow_run._check_platform()

manual_run = simulation_workflow.start_run({0: components1, 1:component_connections1})

print(manual_run)

manual_run.evaluate_next_block()

manual_run.block_evaluation(1)

manual_run.continue_run()
print(manual_run.progress)

print(manual_run._displays())
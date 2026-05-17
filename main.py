# -*- coding: utf-8 -*-
"""
Updated on Sat May 16 15:06:22 2026

@author: ilayda tosun
@description: Clean orchestration execution script for the V-n Diagram generation tool.
"""

import os
import vn_utils

if __name__ == '__main__':
    # 1. Define Paths and Load Configuration Inputs via utils
    yaml_file   = 'Input_Parameters.yaml'
    file_path   = os.path.join(os.getcwd(), 'Inputs', yaml_file)
    inp         = vn_utils.read_input_file(file_path)

    # 2. Run the modular calculation block hidden inside utils
    results, n_max_final, n_min_final = vn_utils.generate_vn_data(inp)

    # 3. Trigger the visualization engine loop inside utils
    vn_utils.plot_individual_vn_diagrams(results, n_max_final, n_min_final)

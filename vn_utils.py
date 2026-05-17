# -*- coding: utf-8 -*-
"""
Updated on Sat May 16 15:06:22 2026

@author: ilayda tosun
@description: Core utility library for CS-25 V-n envelope computations and visualization.
"""

import os
import yaml
import numpy as np
from ambiance import Atmosphere
import matplotlib.pyplot as plt

def read_input_file(file_yml):
    """
    Read the input of the tool as dictionary format.
    """    
    with open(file_yml, 'r') as file:
        inputs = yaml.safe_load(file)
    return inputs    


def extract_core_parameters(inp):
    """
    Extracts basic constants, conversion factors, and computes global dynamic limits.
    """
    # 1. Unit Conversion Constants
    conv = {
        'KTS_2_MS': inp['Unit_Conversion_Constants']['kts_2_ms'],
        'MS_2_KTS': 1.0 / inp['Unit_Conversion_Constants']['kts_2_ms'],
        'FT_2_M': inp['Unit_Conversion_Constants']['ft_2_m']
    }
    
    # 2. Aircraft Physical Properties
    g       = inp['General_Parameters']['g']
    mtow_kg = inp['AC_Design_Properties']['MTOW']
    
    ac_props = {
        'W_N': mtow_kg * g, # Aircraft Weight in Newtons [N]
        'S_wing': inp['AC_Design_Properties']['Wing_Area'],
        'CL_max': inp['AC_Design_Properties']['Aerodynamic_Parameters']['CL_max'],
        'CL_min': inp['AC_Design_Properties']['Aerodynamic_Parameters']['CL_min']
    }
    
    # 3. Structural Limits Formulation
    mtow_lbs = mtow_kg * inp['Unit_Conversion_Constants']['kg_2_lbs']
    n_max   = 2.1 + (24000 / (mtow_lbs + 10000))
    n_min   = inp['Load_Factor_Limits']['n_negative']
    
    limits  = {'n_max': n_max, 'n_min': n_min}
    
    # 4. Standard Atmosphere Constants
    atm_base = {'rho_SL': float(Atmosphere(0).density[0])}
    
    return conv, ac_props, limits, atm_base


def compute_single_altitude(alt_ft, inp, conv, ac_props, limits, atm_base):
    """
    Calculates atmospheric traits, airspeeds, and structural curves for a single target flight level.
    """
    # Fetch local atmospheric profiles
    alt_m   = alt_ft * conv['FT_2_M']
    atm     = Atmosphere(alt_m)
    rho     = float(atm.density[0])
    a_speed = float(atm.speed_of_sound[0])
    
    # Speed configuration tags from YAML
    v_c_cfg = inp['Design_Velocities']['Cruise_Speed']
    v_d_cfg = inp['Design_Velocities']['Dive_Speed']
    
    # Cruise Speed Boundary Computation (EAS vs Mach Limitation)
    if alt_ft <= v_c_cfg['VC2MC_alt']:
        V_C_EAS = v_c_cfg['V_C'] * conv['KTS_2_MS']
    else:
        V_C_TAS = v_c_cfg['M_C'] * a_speed
        V_C_EAS = V_C_TAS * np.sqrt(rho / atm_base['rho_SL'])
        
    # Dive Speed Boundary Computation (EAS vs Mach Limitation)
    if alt_ft <= v_d_cfg['VD2MD_alt']:
        V_D_EAS = v_d_cfg['V_D'] * conv['KTS_2_MS']
    else:
        V_D_TAS = v_d_cfg['M_D'] * a_speed
        V_D_EAS = V_D_TAS * np.sqrt(rho / atm_base['rho_SL'])
        
    # Compute critical aerodynamic flight speeds [m/s]
    V_S = np.sqrt((2 * ac_props['W_N']) / (atm_base['rho_SL'] * ac_props['S_wing'] * ac_props['CL_max']))
    V_A = np.sqrt((2 * ac_props['W_N'] * limits['n_max']) / (atm_base['rho_SL'] * ac_props['S_wing'] * ac_props['CL_max']))
    V_G = np.sqrt((2 * ac_props['W_N'] * abs(limits['n_min'])) / (atm_base['rho_SL'] * ac_props['S_wing'] * abs(ac_props['CL_min'])))
    
    # Calculate coordinate curves for structural boundaries
    v_pos_curve = np.linspace(0, V_A, 100)
    n_pos_curve = (atm_base['rho_SL'] * (v_pos_curve**2) * ac_props['S_wing'] * ac_props['CL_max']) / (2 * ac_props['W_N'])
    
    v_neg_curve = np.linspace(0, V_G, 100)
    n_neg_curve = -(atm_base['rho_SL'] * (v_neg_curve**2) * ac_props['S_wing'] * abs(ac_props['CL_min'])) / (2 * ac_props['W_N'])
    
    return {
        'V_S_kts': V_S * conv['MS_2_KTS'],
        'V_A_kts': V_A * conv['MS_2_KTS'],
        'V_G_kts': V_G * conv['MS_2_KTS'],
        'V_C_kts': V_C_EAS * conv['MS_2_KTS'],
        'V_D_kts': V_D_EAS * conv['MS_2_KTS'],
        'curve_pos_kts': (v_pos_curve * conv['MS_2_KTS'], n_pos_curve),
        'curve_neg_kts': (v_neg_curve * conv['MS_2_KTS'], n_neg_curve)
    }


def generate_vn_data(inp):
    """
    Loops through all configurations to compile the entire structural data tree.
    """
    conv, ac_props, limits, atm_base = extract_core_parameters(inp)
    results_per_altitude = {}
    
    for alt_ft in inp['Flight_Conditions']['Altitude_ft']:
        results_per_altitude[alt_ft] = compute_single_altitude(
            alt_ft, inp, conv, ac_props, limits, atm_base
        )
        
    return results_per_altitude, limits['n_max'], limits['n_min']


def plot_individual_vn_diagrams(results, n_max_lim, n_min_lim):
    """
    Plots and saves a separate V-n diagram for each altitude in the results dictionary
    according to CS-25 maneuver envelope standards.
    """
    output_dir = 'Outputs'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for alt_ft, data in results.items():
        plt.figure(figsize=(10, 6.5))
        
        # --- BACKGROUND STRUCTURAL HORIZONTAL LIMIT LINES ---
        plt.axhline(y=n_max_lim, color='#7f7f7f', linestyle='--', linewidth=1.2, alpha=0.8)
        plt.axhline(y=n_min_lim, color='#d62728', linestyle='--', linewidth=1.2, alpha=0.6)
        
        
        # 1. Plot Positive and Negative Stall Curves
        v_pos, n_pos = data['curve_pos_kts']
        v_neg, n_neg = data['curve_neg_kts']
        
        plt.plot(v_pos, n_pos, color='#1f77b4', linestyle='-', linewidth=2.5)
        plt.plot(v_neg, n_neg, color='#1f77b4', linestyle='-', linewidth=2.5)
        
        # 2. Extract Key Corner Points
        v_s = data['V_S_kts']
        v_a = data['V_A_kts']
        v_g = data['V_G_kts']
        v_c = data['V_C_kts']
        v_d = data['V_D_kts']
        
        # 3. Connect the Corner Points (CS-25 Compliant)
        plt.plot([v_a, v_c], [n_max_lim, n_max_lim], color='#1f77b4', linestyle='-', linewidth=2.5)
        plt.plot([v_c, v_d], [n_max_lim, n_max_lim], color='#1f77b4', linestyle='-', linewidth=2.5)
        plt.plot([v_g, v_c], [n_min_lim, n_min_lim], color='#1f77b4', linestyle='-', linewidth=2.5)
        plt.plot([v_c, v_d], [n_min_lim, 0.0], color='#1f77b4', linestyle='-', linewidth=2.5)
        
        # --- ENVELOPE BOUNDED VERTICAL LINES ---
        plt.plot([v_c, v_c], [n_min_lim, n_max_lim], color='#2ca02c', linestyle='--', linewidth=1.5)
        plt.plot([v_d, v_d], [0.0, n_max_lim], color='#d62728', linestyle='--', linewidth=2)
        
        # Corner markers
        plt.scatter([v_a, v_c, v_d], [n_max_lim, n_max_lim, n_max_lim], color='#1f77b4', s=50, zorder=5)
        plt.scatter([v_g, v_c, v_d], [n_min_lim, n_min_lim, 0.0], color='#1f77b4', s=50, zorder=5)
        
        # Highlighted V_S stall point
        plt.scatter([v_s], [1.0], color='#d62728', edgecolors='black', s=80, linewidths=1.5, zorder=6)
        
        # 4. Add Text Annotations
        pad = 2 
        mid_n = (n_max_lim + n_min_lim) / 2
        
        plt.text(445, n_max_lim + 0.05, f'$n_{{max}}$ = {n_max_lim:.2f}', fontsize=9, fontweight='bold', color='#555555', verticalalignment='bottom', horizontalalignment='right')
        plt.text(445, n_min_lim + 0.05, f'$n_{{min}}$ = {n_min_lim:.2f}', fontsize=9, fontweight='bold', color='#d62728', verticalalignment='bottom', horizontalalignment='right')
        plt.text(v_s + pad, 1.08, f'$V_S$: {v_s:.1f} Kts', fontsize=10, fontweight='bold', color='#d62728', verticalalignment='bottom')
        
        plt.text(v_c - pad, mid_n, f'$V_C$: {v_c:.1f} Kts', fontsize=9, fontweight='bold', color='#2ca02c', rotation=90, verticalalignment='center', horizontalalignment='right')
        plt.text(v_d + pad, mid_n, f'$V_D$: {v_d:.1f} Kts', fontsize=9, fontweight='bold', color='#d62728', rotation=90, verticalalignment='center', horizontalalignment='left')
        
        plt.text(v_a, n_max_lim + 0.05, f'$V_A$: {v_a:.1f} Kts', fontsize=9, fontweight='bold', horizontalalignment='center')
        plt.text(v_g, n_min_lim - 0.15, f'$V_G$: {v_g:.1f} Kts', fontsize=9, fontweight='bold', horizontalalignment='center')
        
        # --- Chart Styling ---
        plt.title(f'CS-25 V-n Maneuver Envelope at {alt_ft:,} ft', fontsize=13, fontweight='bold', pad=15)
        plt.xlabel('Equivalent Airspeed, EAS [Kts]', fontsize=11, labelpad=8)
        plt.ylabel('Load Factor, n [-]', fontsize=11, labelpad=8)
        plt.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        
        plt.grid(visible=True, which='major', color='#dddddd', linestyle='-', linewidth=0.8)
        plt.minorticks_on()
        plt.xlim(0, 450) 
        plt.ylim(n_min_lim - 0.6, n_max_lim + 0.6)
        plt.legend(loc='lower left', fontsize=10)
        plt.tight_layout()
        
        filename = f'V_n_Diagram_{alt_ft}ft.png'
        plt.savefig(os.path.join(output_dir, filename), dpi=300)
        print(f"Saved: {os.path.join(output_dir, filename)}")
        plt.show()

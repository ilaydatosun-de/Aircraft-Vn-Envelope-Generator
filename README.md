# CS-25 Compliant Aircraft V-n Flight Envelope Generator

A highly modular Python tool designed to compute, parse, and generate structural flight envelopes (**V-n Diagrams**) for transport category aircraft according to **CS-25 / FAR-25** certification specifications.

## ?? Features
- **Atmospheric Modeling:** Leverages the International Standard Atmosphere (ISA) via the `ambiance` library.
- **Altitude-Dependent Limits:** Computes structural boundary contraction automatically as air velocity transitions from constant EAS limits to compressibility-driven Mach ceilings.
- **CS-25 Load Factoring:** Dynamically scales $n_{max}$ limits based on structural aircraft mass relationships and applies compliant sloped negative boundaries up to $V_D$.
- **High-Quality Output Plots:** Exports annotated high-fidelity `.png` diagrams mapped cleanly across multi-flight level arrays.

## ??? Installation & Setup
1. Clone the repository:
   ```bash
   git clone https://github.com
   cd Aircraft-Vn-Envelope-Generator
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the generator:
   ```bash
   python main.py
   ```

## ?? Configuration Input
Aircraft parameters and target flight levels are read seamlessly from `Inputs/Input_Parameters.yaml`. Modify weights, structural speeds, or surface spaces directly inside the configuration tree to evaluate different aircraft specifications.

## ?? Future Roadmap & Extensions
The foundational loose-coupling architecture of this software makes it highly adaptable for progressive academic or industrial modules:
- **Flap-Open Subsets:** Integrating discrete high-lift deployment stages (e.g., Flaps 15�, Flaps 35�) to overlay secondary restricted boundaries under CS-25.345.
- **Compressibility Effects on Lift ($M$ vs. $C_L$):** Appending a Mach-dependent degradation function to dynamically bend stall curves inward at higher subsonic cruise levels.
- **Dynamic Gust Envelopes:** Implementing continuous gust factor equations to overlay vertical and lateral wind sharp edges over the maneuvering boundaries (CS-25.341).

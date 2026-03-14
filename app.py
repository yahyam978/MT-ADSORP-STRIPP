import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mass Transfer Designer", layout="wide")

st.title("🏗️ Absorption & Stripping Column Designer")
st.sidebar.header("Input Parameters")

# 1. Process Selection
process = st.sidebar.selectbox("Process Type", ["Stripping", "Absorption"])

# 2. Feed Conditions
col1, col2 = st.sidebar.columns(2)
with col1:
    L = st.number_input("Liquid Rate (L) [kmol/hr]", value=500.0)
    x_in = st.number_input("Inlet Liq fraction (x_in)", value=0.10, format="%.4f")
with col2:
    V_input = st.number_input("Gas Rate (V) [kmol/hr]", value=188.0)
    y_in = st.number_input("Inlet Gas fraction (y_in)", value=0.0, format="%.4f")

# 3. Equilibrium Data
st.sidebar.subheader("Equilibrium (Raoult's Law)")
p_sat = st.sidebar.number_input("Vapor Pressure [mmHg]", value=2400.0)
p_total = st.sidebar.number_input("Total Pressure [mmHg]", value=760.0)
m = p_sat / p_total

# 4. Target Specification
target_x = st.sidebar.number_input("Target Outlet Liq (x_out)", value=0.005, format="%.4f")

# --- CALCULATIONS ---
# Mass Balance: L(x_in - x_out) = V(y_out - y_in)
# For stripping, we usually solve for y_out (gas leaving top)
y_out = (L / V_input) * (x_in - target_x) + y_in

# Factor Calculation
if process == "Stripping":
    S = (m * V_input) / L
    # Kremser for Stripping
    if S != 1:
        term = ((x_in - y_in/m)/(target_x - y_in/m)) * (1 - 1/S) + (1/S)
        N = np.log(term) / np.log(S)
    else:
        N = (x_in - target_x) / (target_x - y_in/m)
else:
    A = L / (m * V_input)
    # Kremser for Absorption (Assuming y_out is target)
    # Note: Logic would be adjusted based on which 'given' you choose
    N = 0 # Placeholder for expanded absorption logic

# --- UI DISPLAY ---
res1, res2 = st.columns(2)
res1.metric("Equilibrium Slope (m)", f"{m:.3f}")
res1.metric("Stripping Factor (S)", f"{S:.3f}")
res2.metric("Ideal Trays (N)", f"{N:.2f}")
res2.metric("Outlet Gas (y_out)", f"{y_out:.4f}")

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(8, 6))
x_plot = np.linspace(0, x_in * 1.2, 100)
ax.plot(x_plot, m * x_plot, 'r-', label='Equilibrium Line')
ax.plot([target_x, x_in], [y_in, y_out], 'b--', label='Operating Line')

# Simple Staircase Visualization
curr_x, curr_y = x_in, y_out
for _ in range(int(np.ceil(N))):
    next_x = curr_y / m
    ax.hlines(curr_y, curr_x, next_x, colors='green', linestyles=':')
    next_y = (L / V_input) * (next_x - target_x) + y_in
    ax.vlines(next_x, curr_y, next_y, colors='green', linestyles=':')
    curr_x, curr_y = next_x, next_y

ax.set_xlabel("Liquid Mole Fraction (x)")
ax.set_ylabel("Vapor Mole Fraction (y)")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

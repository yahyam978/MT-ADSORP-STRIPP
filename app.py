import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

st.set_page_config(page_title="Universal Column Designer", layout="wide")

st.title("🚀 Universal Absorption & Stripping Designer")

# --- SIDEBAR: CONFIGURATION ---
st.sidebar.header("1. Global Settings")
calc_basis = st.sidebar.radio("Calculation Basis", ["Mole Fraction (x,y)", "Mole Ratio (X,Y)"])
process = st.sidebar.selectbox("Process Type", ["Stripping", "Absorption"])

st.sidebar.header("2. Equilibrium Data")
eq_type = st.sidebar.selectbox("Equilibrium Source", ["Linear (y=mx)", "Experimental Data"])

if eq_type == "Experimental Data":
    x_raw = st.sidebar.text_input("x data", "0.0, 0.05, 0.1, 0.15")
    y_raw = st.sidebar.text_input("y data", "0.0, 0.15, 0.31, 0.45")
    x_exp = np.fromstring(x_raw, sep=',')
    y_exp = np.fromstring(y_raw, sep=',')
    # Create interpolation for mole fractions
    f_eq = interp1d(x_exp, y_exp, kind='cubic', fill_value="extrapolate")
else:
    m = st.sidebar.number_input("Slope (m)", value=3.158)
    f_eq = lambda x: m * x

# --- INPUT SECTION ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Process Inputs")
    # L' and V' are the solute-free flow rates (kmol solvent/hr)
    L_prime = st.number_input("Solvent Flow (L') [kmol/hr]", value=450.0)
    V_prime = st.number_input("Carrier Gas (V') [kmol/hr]", value=188.0)
    
    label_in = "Inlet" if calc_basis == "Mole Fraction (x,y)" else "Inlet Ratio (X)"
    in_val = st.number_input(f"{label_in}", value=0.10, format="%.4f")
    target_val = st.number_input("Target Outlet", value=0.005, format="%.4f")

# --- DATA PROCESSING ---
# We convert everything to Mole Ratios (X, Y) for the internal math 
# because the operating line is ALWAYS straight in Ratio coordinates.
if calc_basis == "Mole Fraction (x,y)":
    X1 = in_val / (1 - in_val)
    X2 = target_val / (1 - target_val)
else:
    X1 = in_val
    X2 = target_val

# Mass Balance on Solute-Free Basis: V'(Y1 - Y2) = L'(X1 - X2)
Y2 = 0.0 # Pure steam/solvent inlet
Y1 = (L_prime / V_prime) * (X1 - X2) + Y2

# --- STAIRCASE & PLOTTING ---
fig, ax = plt.subplots(figsize=(10, 7))

# Generate Equilibrium Curve in Ratio Basis
X_plot = np.linspace(0, max(X1, X2)*1.2, 200)
# Convert X to x to get y from eq_func, then convert y to Y
x_plot = X_plot / (1 + X_plot)
y_plot = f_eq(x_plot)
Y_plot = y_plot / (1 - y_plot)

ax.plot(X_plot, Y_plot, 'r-', label='Equilibrium Curve (Ratios)')
ax.plot([X2, X1], [Y2, Y1], 'b-o', label='Operating Line (Ratios)')

# Staircase Logic in Ratio space
curr_X, curr_Y = X1, Y1
steps = 0
while curr_X > X2 and steps < 50:
    # 1. Horizontal to Equilibrium: Find X such that Y_eq(X) = curr_Y
    # Find root where f_eq(x)/(1-f_eq(x)) - curr_Y = 0
    temp_X = np.linspace(0, X1*1.5, 2000)
    temp_x = temp_X / (1 + temp_X)
    temp_y = f_eq(temp_x)
    temp_Y = temp_y / (1 - temp_y)
    next_X = temp_X[np.argmin(np.abs(temp_Y - curr_Y))]
    
    ax.hlines(curr_Y, curr_X, next_X, colors='green', alpha=0.5)
    
    # 2. Vertical to Operating Line
    if next_X > X2:
        next_Y = (L_prime / V_prime) * (next_X - X2) + Y2
        ax.vlines(next_X, curr_Y, next_Y, colors='green', alpha=0.5)
        curr_X, curr_Y = next_X, next_Y
    else:
        ax.vlines(next_X, curr_Y, Y2, colors='green', alpha=0.5)
        curr_X = next_X
    steps += 1

with col2:
    st.subheader("Design Analysis")
    st.metric("Total Ideal Stages", steps)
    
    ax.set_xlabel("Liquid Mole Ratio (X)")
    ax.set_ylabel("Vapor Mole Ratio (Y)")
    ax.legend()
    ax.grid(True, which='both', linestyle='--', alpha=0.5)
    st.pyplot(fig)

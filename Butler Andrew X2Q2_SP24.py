# ChatGPT helped with formatting and debugging code

# region imports
from math import sin
import math
import numpy as np
from scipy.integrate import solve_ivp
from matplotlib import pyplot as plt
# endregion


# region function definitions

def odeSystem(t, X, *args):
    """
    Callback for solve_ivp().

    State variables:
        X[0] = i1, current through the resistor branch
        X[1] = i2, current through the capacitor branch

    Circuit relations:
        v_c = v_R = R*i1
        i2 = C * dv_c/dt = C*R*di1/dt
        i_L = i1 + i2
        v(t) = L*d(i_L)/dt + v_c

    :param t: current time
    :param X: current state vector [i1, i2]
    :param args: (fn, L, R, C) where fn is the driving-voltage callback
    :return: [di1/dt, di2/dt]
    """
    fn, L, R, C = args

    i1 = X[0]
    i2 = X[1]
    vt = fn(t)

    i1dot = i2 / (C * R)
    i2dot = (vt - R * i1) / L - i1dot

    return [i1dot, i2dot]



def simulate(L=20, R=10, C=0.05, A=20, f=20, p=0, t=10, pts=500):
    """
    Simulate the transient response of the circuit.

    :param L: inductance in H
    :param R: resistance in ohm
    :param C: capacitance in F
    :param A: driving voltage amplitude in V
    :param f: driving frequency in Hz
    :param p: phase in degrees
    :param t: simulation end time in s
    :param pts: number of simulation points
    :return: solve_ivp result object
    """
    w = f * 2.0 * math.pi
    phi = p * math.pi / 180.0
    vin = lambda tau: A * sin(w * tau + phi)

    myargs = (vin, L, R, C)
    x0 = [0.0, 0.0]
    tList = np.linspace(0.0, t, int(pts))

    I = solve_ivp(odeSystem, t_span=[0.0, t], y0=x0, t_eval=tList, args=myargs)
    return I



def doPlot(*args, ax=None):
    """
    Plot i1, i2, and capacitor voltage Vc.

    :param args: tuple containing (R, time_list, solve_ivp_result)
    :param ax: optional matplotlib axes for GUI plotting
    :return: nothing
    """
    if ax is None:
        ax = plt.subplot()
        qt_plotting = False
    else:
        qt_plotting = True

    R, tList, I = args[0]
    ax.clear()
    ax.plot(tList, I.y[0], linestyle='solid', color='k', label=r'$i_1(t)$')
    ax.plot(tList, I.y[1], linestyle='dashed', color='k', label=r'$i_2(t)$')
    ax.set_xlim(0, max(tList))

    minI = min(min(I.y[0]), min(I.y[1]))
    maxI = max(max(I.y[0]), max(I.y[1]))
    rangeI = abs(maxI - minI) if maxI != minI else 1.0
    ax.set_ylim(minI - 0.01 * rangeI, maxI + 0.01 * rangeI)
    ax.tick_params(axis='both', which='both', direction='in', top=True, labelsize=12)
    ax.tick_params(axis='both', grid_linewidth=1, grid_linestyle='solid', grid_alpha=0.5)
    ax.tick_params(axis='both', which='minor')
    ax.grid(True)
    ax.set_xlabel('t (s)', fontsize=12)
    ax.set_ylabel(r'$i_1, i_2$ (A)', fontsize=12)

    ax1 = ax.twinx()
    yvals = R * I.y[0]
    yrange = abs(max(yvals) - min(yvals)) if max(yvals) != min(yvals) else 1.0
    ax1.plot(tList, yvals, linestyle='dotted', color='k', label=r'$v_c(t)$')
    ax1.set_ylim(min(yvals) - yrange * 0.01, max(yvals) + yrange * 0.01)
    ax1.tick_params(axis='y', which='both', direction='in', top=True, right=True, labelsize=12)
    ax.legend(fontsize=12)
    ax1.legend(loc='lower right', fontsize=12)
    ax1.set_ylabel(r'$V_c(t)$ (V)', fontsize=12)

    if not qt_plotting:
        plt.show()



def main():
    """Run a default simulation and display the plot."""
    I = simulate(L=20, R=10, C=0.05, A=20, f=20, p=0, t=10, pts=500)
    doPlot((10, I.t, I))


# endregion


# region function calls
if __name__ == "__main__":
    main()
# endregion

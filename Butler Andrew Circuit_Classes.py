# ChatGPT helped with formatting and debugging code

#region imports
import os
import sys
import importlib.util

# Prefer PyQt5 for class compatibility, then fall back to PySide6.
QT_LIB = None
try:
    from PyQt5 import QtWidgets as qtw
    from PyQt5 import QtGui as qtg
    from PyQt5 import QtCore as qtc
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
    QT_LIB = 'PyQt5'
except Exception:
    from PySide6 import QtWidgets as qtw
    from PySide6 import QtGui as qtg
    from PySide6 import QtCore as qtc
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
    QT_LIB = 'PySide6'

from matplotlib.figure import Figure
#endregion


def _load_module_from_same_folder(filename, module_name):
    """Load a sibling .py file even when the filename contains spaces."""
    full_path = os.path.join(os.path.dirname(__file__), filename)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_q2_module = _load_module_from_same_folder("Butler Andrew X2Q2_SP24.py", "butler_andrew_x2q2_sp24")
doPlot = _q2_module.doPlot
simulate = _q2_module.simulate


#region RLC circuit classes (MVC)
class circuitModel():
    def __init__(self):
        """Simple data container for circuit objects."""
        self.nodes = []
        self.resistors = []
        self.capacitors = []
        self.inductors = []
        self.voltageSources = []
        self.wires = []


class circuitView():
    def __init__(self, dw=None):
        if dw is not None:
            self.setDisplayWidgets(dw)
            self.setupImageLabel()
            self.setupPlot()

    def setDisplayWidgets(self, dw=None):
        """Unpack the widgets used by the view."""
        if dw is not None:
            self.layout_VertMain, self.layout_VertInput, self.form = dw

    def setupImageLabel(self):
        """
        Display the circuit picture in the input group box.
        :return: nothing
        """
        #region setup a label to display the image of the circuit
        image_path = os.path.join(os.path.dirname(__file__), "Circuit1.png")
        self.pixMap = qtg.QPixmap(image_path)
        self.image_label = qtw.QLabel(self.form)
        self.image_label.setPixmap(self.pixMap)
        self.image_label.setScaledContents(False)
        self.image_label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter if QT_LIB == 'PySide6' else qtc.Qt.AlignCenter)
        self.layout_VertInput.addWidget(self.image_label)
        #endregion

    def setupPlot(self):
        """Create the matplotlib figure, canvas, axes, and toolbar."""
        self.figure = Figure(figsize=(8, 8), tight_layout=True, frameon=True, facecolor='none')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot()
        self.toolbar = NavigationToolbar2QT(self.canvas, self.form)
        self.layout_VertMain.addWidget(self.toolbar)
        self.layout_VertMain.addWidget(self.canvas)

    def doPlot(self, args):
        """Redraw the plot on the canvas."""
        self.canvas.figure.clear()
        self.ax = self.figure.add_subplot()
        doPlot(args, ax=self.ax)
        self.canvas.draw()


class circuitController():
    def __init__(self, args):
        """
        Controller for the RLC circuit GUI.

        :param args: tuple containing (inputWidgets, displayWidgets)
        """
        self.inputWidgets, self.displayWidgets = args

        (
            self.le_Inductance,
            self.le_Resistance,
            self.le_Capacitence,
            self.le_Amplitude,
            self.le_Freq,
            self.le_Phase,
            self.le_simTime,
            self.le_simPts,
        ) = self.inputWidgets

        self.Model = circuitModel()
        self.View = circuitView(dw=self.displayWidgets)

    def calculate(self):
        """
        Simulate the circuit and update the plot.
        :return: nothing
        """
        L = float(self.le_Inductance.text())
        R = float(self.le_Resistance.text())
        C = float(self.le_Capacitence.text())
        A = float(self.le_Amplitude.text())
        f = float(self.le_Freq.text())
        p = float(self.le_Phase.text())
        t = float(self.le_simTime.text())
        pts = float(self.le_simPts.text())

        I = simulate(L=L, R=R, C=C, A=A, f=f, p=p, t=t, pts=pts)
        self.View.doPlot((R, I.t, I))

#endregion

# ChatGPT helped with formatting and debugging code
#region imports
import sys
import importlib.util
from pathlib import Path

try:
    from PyQt5 import QtWidgets as qtw
    from PyQt5 import QtCore as qtc
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
except ImportError:
    from PySide6 import QtWidgets as qtw
    from PySide6 import QtCore as qtc
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT

from matplotlib.figure import Figure
#endregion

#region ui helper constants
BASE_FONT_PT = 10
HEADER_FONT_PT = 11
#endregion

#region helper functions
def _load_module_from_same_folder(filename, module_name):
    folder = Path(__file__).resolve().parent
    module_path = folder / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_gui_module = _load_module_from_same_folder("Butler Andrew Rankine_GUI.py", "butler_andrew_rankine_gui")
_classes_module = _load_module_from_same_folder("Butler Andrew Rankine_Classes_MVC.py", "butler_andrew_rankine_classes")
Ui_Form = _gui_module.Ui_Form
rankineController = _classes_module.rankineController
#endregion

#region class definitions
class MainWindow(qtw.QWidget, Ui_Form):
    def __init__(self):
        """
        MainWindow constructor
        """
        super().__init__()
        self.setupUi(self)
        self.polishUi()
        self.AssignSlots()
        self.MakeCanvas()

        self.input_widgets = [self.rb_SI, self.le_PHigh, self.le_PLow, self.le_TurbineInletCondition,
                              self.rdo_Quality, self.le_TurbineEff, self.cmb_XAxis, self.cmb_YAxis,
                              self.chk_logX, self.chk_logY]
        self.display_widgets = [self.lbl_PHigh, self.lbl_PLow, self.lbl_SatPropLow, self.lbl_SatPropHigh,
                                self.lbl_TurbineInletCondition, self.lbl_H1, self.lbl_H1Units, self.lbl_H2,
                                self.lbl_H2Units, self.lbl_H3, self.lbl_H3Units, self.lbl_H4,
                                self.lbl_H4Units, self.lbl_TurbineWork, self.lbl_TurbineWorkUnits,
                                self.lbl_PumpWork, self.lbl_PumpWorkUnits, self.lbl_HeatAdded,
                                self.lbl_HeatAddedUnits, self.lbl_ThermalEfficiency, self.canvas,
                                self.figure, self.ax]
        self.RC = rankineController(self.input_widgets, self.display_widgets)

        self.setNewPHigh()
        self.setNewPLow()
        self.Calculate()

        self.oldXData = 0.0
        self.oldYData = 0.0
        self.show()

    def polishUi(self):
        """
        Make the GUI a little cleaner without changing any of the program logic.
        """
        self.setWindowTitle('Rankine Cycle Calculator')
        self.resize(1600, 980)
        self.setMinimumSize(1350, 860)

        # main window spacing
        self.verticalLayout.setContentsMargins(16, 14, 16, 14)
        self.verticalLayout.setSpacing(14)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setSpacing(14)
        self.HorisontalLayout.setContentsMargins(0, 0, 0, 0)
        self.HorisontalLayout.setSpacing(0)

        # group sizing for a cleaner left-to-right balance
        self.gb_Input.setMinimumWidth(525)
        self.gb_Input.setMaximumWidth(620)
        self.gb_Output.setMinimumWidth(720)

        # improve layout spacing inside groups
        self.gb_InputVerticalLayout.setContentsMargins(14, 14, 14, 14)
        self.gb_InputVerticalLayout.setSpacing(12)
        self.gb_OutputVerticalLayout.setContentsMargins(14, 14, 14, 14)
        self.gb_OutputVerticalLayout.setSpacing(12)
        self.gridLayoutInput.setHorizontalSpacing(10)
        self.gridLayoutInput.setVerticalSpacing(10)
        self.gridLayoutOutput.setHorizontalSpacing(12)
        self.gridLayoutOutput.setVerticalSpacing(10)
        self.gridLayout.setHorizontalSpacing(10)
        self.gridLayout.setVerticalSpacing(8)

        # input widgets
        line_edits = [self.le_PHigh, self.le_PLow, self.le_TurbineInletCondition, self.le_TurbineEff]
        for widget in line_edits:
            widget.setMinimumHeight(34)
            widget.setMinimumWidth(140)

        self.btn_Calculate.setMinimumHeight(38)
        self.btn_Calculate.setMinimumWidth(120)
        self.cmb_XAxis.setMinimumWidth(90)
        self.cmb_YAxis.setMinimumWidth(90)

        # saturated property boxes and output values look less cramped with top alignment
        self.lbl_SatPropHigh.setMinimumHeight(118)
        self.lbl_SatPropLow.setMinimumHeight(118)
        try:
            align_left_top = qtc.Qt.AlignLeft | qtc.Qt.AlignTop
        except AttributeError:
            align_left_top = qtc.Qt.AlignmentFlag.AlignLeft | qtc.Qt.AlignmentFlag.AlignTop
        self.lbl_SatPropHigh.setAlignment(align_left_top)
        self.lbl_SatPropLow.setAlignment(align_left_top)

        for widget in [self.lbl_H1, self.lbl_H2, self.lbl_H3, self.lbl_H4,
                       self.lbl_TurbineWork, self.lbl_PumpWork, self.lbl_HeatAdded,
                       self.lbl_ThermalEfficiency]:
            widget.setMinimumWidth(92)

        # make the main plot area grow with the window
        self.verticalLayout.setStretch(0, 0)
        self.verticalLayout.setStretch(1, 1)

    def AssignSlots(self):
        self.btn_Calculate.clicked.connect(self.Calculate)
        self.rdo_Quality.clicked.connect(self.SelectQualityOrTHigh)
        self.rdo_THigh.clicked.connect(self.SelectQualityOrTHigh)
        self.le_PHigh.editingFinished.connect(self.setNewPHigh)
        self.le_PLow.editingFinished.connect(self.setNewPLow)
        self.rb_SI.clicked.connect(self.SetUnits)
        self.rb_English.clicked.connect(self.SetUnits)
        self.cmb_XAxis.currentIndexChanged.connect(self.SetPlotVariables)
        self.cmb_YAxis.currentIndexChanged.connect(self.SetPlotVariables)
        self.chk_logX.toggled.connect(self.SetPlotVariables)
        self.chk_logY.toggled.connect(self.SetPlotVariables)

    def MakeCanvas(self):
        self.figure = Figure(figsize=(8.5, 6.0), tight_layout=False, frameon=True, constrained_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(460)
        self.ax = self.figure.add_subplot()
        self.Layout_Plot.addWidget(NavigationToolbar2QT(self.canvas, self))
        self.Layout_Plot.addWidget(self.canvas)
        self.canvas.mpl_connect("motion_notify_event", self.mouseMoveEvent_Canvas)

    def mouseMoveEvent_Canvas(self, event):
        self.oldXData = event.xdata if event.xdata is not None else self.oldXData
        self.oldYData = event.ydata if event.ydata is not None else self.oldYData
        sUnit = 'kJ/(kg*K)' if self.rb_SI.isChecked() else 'BTU/(lb*R)'
        TUnit = 'C' if self.rb_SI.isChecked() else 'F'
        self.setWindowTitle('s:{:0.2f} {}, T:{:0.2f} {}'.format(self.oldXData, sUnit, self.oldYData, TUnit))

    def Calculate(self):
        self.RC.updateModel()

    def SelectQualityOrTHigh(self):
        self.RC.selectQualityOrTHigh()

    def SetPlotVariables(self):
        self.RC.updatePlot()

    def SetUnits(self):
        self.RC.updateUnits()

    def setNewPHigh(self):
        self.RC.setNewPHigh()

    def setNewPLow(self):
        self.RC.setNewPLow()
#endregion

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle('Rankine calculator')
    try:
        sys.exit(app.exec())
    except AttributeError:
        sys.exit(app.exec_())

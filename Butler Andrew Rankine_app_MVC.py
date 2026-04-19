# ChatGPT helped with formatting and debugging code
#region imports
import sys
import os
import importlib.util
from PySide6 import QtWidgets as qtw
from PySide6 import QtCore as qtc
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure


def _load_module_from_same_folder(filename, module_name):
    """Load a Python module from the same folder as this file."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_gui_module = _load_module_from_same_folder("Butler Andrew Rankine_GUI.py", "butler_andrew_rankine_gui")
Ui_Form = _gui_module.Ui_Form
_classes_module = _load_module_from_same_folder("Butler Andrew Rankine_Classes_MVC.py", "butler_andrew_rankine_classes_mvc")
rankineController = _classes_module.rankineController
_uc_module = _load_module_from_same_folder("Butler Andrew UnitConversions.py", "butler_andrew_unit_conversions")
UC = _uc_module.UnitConverter
#endregion

#region class definitions
class MainWindow(qtw.QWidget, Ui_Form):
    def __init__(self):
        """
        MainWindow constructor
        """
        super().__init__()  #if you inherit, you generally should run the parent constructor first.
        # Main UI code goes here
        self.setupUi(self)
        self.AssignSlots()
        self.MakeCanvas()

        #create lists of input and display widgets
        self.input_widgets = [self.rb_SI,self.le_PHigh, self.le_PLow, self.le_TurbineInletCondition, self.rdo_Quality, self.le_TurbineEff, self.cmb_XAxis, self.cmb_YAxis, self.chk_logX, self.chk_logY]
        self.display_widgets=[self.lbl_PHigh, self.lbl_PLow, self.lbl_SatPropLow,self.lbl_SatPropHigh, self.lbl_TurbineInletCondition, self.lbl_H1, self.lbl_H1Units, self.lbl_H2, self.lbl_H2Units, self.lbl_H3, self.lbl_H3Units, self.lbl_H4, self.lbl_H4Units, self.lbl_TurbineWork, self.lbl_TurbineWorkUnits, self.lbl_PumpWork, self.lbl_PumpWorkUnits, self.lbl_HeatAdded, self.lbl_HeatAddedUnits, self.lbl_ThermalEfficiency, self.canvas, self.figure, self.ax]
        self.RC=rankineController(self.input_widgets, self.display_widgets)  # instantiate a rankineController object

        self.setNewPHigh()
        self.setNewPLow()

        self.Calculate()  #calculate using initial values

        # a place to store coordinates from last position on graph
        self.oldXData=0.0
        self.oldYData=0.0
        # End main ui code
        self.show()

    def AssignSlots(self):
        """
        Setup signals and slots for my program
        :return:
        """
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
        """
        Create a place to make graph of Rankine cycle
        Step 1:  create a Figure object called self.figure
        Step 2:  create a FigureCanvasQTAgg object called self.canvas
        Step 3:  create an axes object for making plot
        Step 4:  add self.canvas to self.widgetsVerticalLayout which is a Vertical box layout
        :return:
        """
        #Step 1.
        self.figure=Figure(figsize=(1,1),tight_layout=True, frameon=True)
        #Step 2.
        self.canvas=FigureCanvasQTAgg(self.figure)
        #Step 3.
        self.ax = self.figure.add_subplot()
        #Step 4.
        self.Layout_Plot.addWidget(NavigationToolbar2QT(self.canvas,self))
        self.Layout_Plot.addWidget(self.canvas)
        #Step 5. attach an event handler for mouse movement on graph
        self.canvas.mpl_connect("motion_notify_event", self.mouseMoveEvent_Canvas)

    #since my main window is a widget, I can customize its events by overriding the default event
    def mouseMoveEvent_Canvas(self, event):
        self.oldXData=event.xdata if event.xdata is not None else self.oldXData
        self.oldYData=event.ydata if event.ydata is not None else self.oldYData
        sUnit='kJ/(kg*K)' if self.rb_SI.isChecked() else 'BTU/(lb*R)'
        TUnit='C' if self.rb_SI.isChecked() else 'F'
        self.setWindowTitle('s:{:0.2f} {}, T:{:0.2f} {}'.format(self.oldXData,sUnit, self.oldYData,TUnit))

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

#if this module is being imported, this won't run. If it is the main module, it will run.
if __name__== '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle('Rankine calculator')
    sys.exit(app.exec())
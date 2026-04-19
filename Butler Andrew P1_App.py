# ChatGPT helped with formatting and debugging code

#region imports
import sys
import os
import importlib.util
from PySide6.QtWidgets import QApplication, QWidget


def _load_module_from_same_folder(filename, module_name):
    """Load a Python module from the same folder as this file."""
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_gui_module = _load_module_from_same_folder("Butler Andrew P1_GUI.py", "butler_andrew_p1_gui")
Ui_MainForm = _gui_module.Ui_MainForm
_circuit_module = _load_module_from_same_folder("Butler Andrew Circuit_Classes.py", "butler_andrew_circuit_classes")
circuitController = _circuit_module.circuitController
#endregion


#region class definitions
class main_window(Ui_MainForm, QWidget):
    def __init__(self):
        """Constructor for the circuit simulator main window."""
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Exam 2 Question 2 - RLC Circuit Simulator")

        self.inputWidgets = (
            self.le_Inductance,
            self.le_Resistance,
            self.le_Capacitence,
            self.le_Amplitude,
            self.le_Freq,
            self.le_Phase,
            self.le_simTime,
            self.le_simPts,
        )
        self.displayWidgets = (self.layout_VertMain, self.layout_VertInput, self)
        self.controller = circuitController((self.inputWidgets, self.displayWidgets))
        self.setupSignalsAndSlots()
        self.show()

    def setupSignalsAndSlots(self):
        """Connect the Calculate button to the controller action."""
        self.pb_Calculate.clicked.connect(self.calculate)

    def calculate(self):
        """Delegate the calculation to the controller."""
        self.controller.calculate()

#endregion


if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    main_win = main_window()
    sys.exit(app.exec())

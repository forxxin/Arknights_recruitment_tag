
from PyQt6 import QtWidgets, QtGui, QtCore

def set_space(layout):
    if hasattr(layout,'setHorizontalSpacing'):
        layout.setHorizontalSpacing(0)
    if hasattr(layout,'setVerticalSpacing'):
        layout.setVerticalSpacing(0)
class MyGridLayout(QtWidgets.QGridLayout):
    def __init__(self,parent=None):
        super().__init__(parent)
        set_space(self)
class MyVBoxLayout(QtWidgets.QVBoxLayout):
    def __init__(self,parent=None):
        super().__init__(parent)
        set_space(self)
class MyHBoxLayout(QtWidgets.QHBoxLayout):
    def __init__(self,parent=None):
        super().__init__(parent)
        set_space(self)

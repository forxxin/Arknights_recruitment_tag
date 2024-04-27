
from PyQt6 import QtWidgets, QtGui, QtCore

def set_space(layout):
    if hasattr(layout,'setHorizontalSpacing'):
        layout.setHorizontalSpacing(0)
    if hasattr(layout,'setVerticalSpacing'):
        layout.setVerticalSpacing(0)
class MyGridLayout(QtWidgets.QGridLayout):
    def __init__(self):
        super(MyGridLayout, self).__init__()
        set_space(self)
class MyVBoxLayout(QtWidgets.QVBoxLayout):
    def __init__(self):
        super(MyVBoxLayout, self).__init__()
        set_space(self)
class MyHBoxLayout(QtWidgets.QHBoxLayout):
    def __init__(self):
        super(MyHBoxLayout, self).__init__()
        set_space(self)

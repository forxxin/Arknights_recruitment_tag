
import os
import re

from PyQt6 import QtWidgets, QtGui, QtCore

from ui_farm_stages import UiFarmStage
from ui_stores import UiStores
from ui_char import UiChars
from ui_rec_tags import UiRecTag
from qtlayout import MyGridLayout,MyVBoxLayout,MyHBoxLayout
try:
    import saveobj
except:
    import mods.saveobj

try:
    from test import dump
except:
    def dump(**a):
        pass

app_path = os.path.dirname(__file__)
os.chdir(app_path)

class EditableTabBar(QtWidgets.QTabBar):
    def __init__(self, parent):
        super().__init__(parent)
        self._lineedit = QtWidgets.QLineEdit(self)
        self._lineedit.setWindowFlags(QtCore.Qt.WindowType.Popup)
        self._lineedit.setFocusProxy(self)
        self._lineedit.editingFinished.connect(self.edit_finished)
        self._lineedit.installEventFilter(self)
    def eventFilter(self, widget, event):
        if event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if not self._lineedit.geometry().contains(event.globalPosition().toPoint()):
                self.edit_finished()
                self._lineedit.hide()
                return True
        elif event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Escape:
                self._lineedit.hide()
                return True
        return super().eventFilter(widget, event)
    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        if index >= 0:
            self.editTab(index)
    def editTab(self, index):
        rect = self.tabRect(index)
        self._lineedit.setFixedSize(rect.size())
        self._lineedit.move(self.parent().mapToGlobal(rect.topLeft()))
        self._lineedit.setText(self.tabText(index))
        if not self._lineedit.isVisible():
            self._lineedit.show()
    def edit_finished(self):
        index = self.currentIndex()
        if index >= 0:
            self._lineedit.hide()
            self.setTabText(index, self._lineedit.text())

class UiPlan(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.config='./config/UiPlan.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
        
        widget_layout = MyVBoxLayout()
        self.tabs = QtWidgets.QTabWidget()
        tab0=QtWidgets.QWidget()
        
        self.tabs.setTabBar(EditableTabBar(self))
        
        self.setLayout(widget_layout)
        widget_layout.addWidget(self.tabs)
        self.tabs.addTab(tab0,'Best Stages')
        
        self.load_pos()
        
    def closeEvent(self,event):
        self.save_pos()
    def save_pos(self):
        g=self.geometry()
        d={'geometry':[g.x(),g.y(),g.width(),g.height()],'currentIndex':self.tabs.currentIndex()}
        saveobj.save_json(self.config,d)
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if isinstance(d,dict):
            if (geometry:=d.get('geometry')):
                self.setGeometry(*geometry)
            if (currentIndex:=d.get('currentIndex')) in [0,1,2]:
                self.tabs.setCurrentIndex(currentIndex)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    root = UiPlan()
    root.show()
    ret = app.exec()
    exit(ret)

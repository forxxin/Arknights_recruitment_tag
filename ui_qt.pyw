
import os
import re

from PyQt6 import QtWidgets, QtGui, QtCore

from ui_farm_stages import UiFarmStage
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

class UiRoot(QtWidgets.QMainWindow):
    def __init__(self):
        super(UiRoot, self).__init__()
        self.config='./config/UiRoot.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
        self.setWindowTitle(f"ToolsArknights")
        self.tabs = QtWidgets.QTabWidget()
        tab0=QtWidgets.QWidget()
        vlayout = MyVBoxLayout()
        self.ui_args = UiArgs()
        self.ui_farm = UiFarmStage(self.ui_args.args_farm())
        self.ui_recr_key,args = self.key_ui_recr()
        ui_recr = UiRecTag(args)
        self.load_pos()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(tab0,'Best Stages')
        tab0.setLayout(vlayout)
        vlayout.addWidget(self.ui_args)
        vlayout.addWidget(self.ui_farm)
        self.tabs.addTab(ui_recr,'Recruit Tag')
        self.ui_args.combs['server'].currentTextChanged.connect(self.update_ui)
        self.ui_args.combs['minimize_stage_key'].currentTextChanged.connect(self.update_ui)
        self.ui_args.combs['lang'].currentTextChanged.connect(self.update_ui)
        self.ui_args.combs['show'].currentTextChanged.connect(self.ui_farm.UiItemImg_n)
        self.ui_args.btn_ok.clicked.connect(self.update_ui)
        self.ui_recrs={}
        self.ui_recrs[self.ui_recr_key]=ui_recr
        self.tabs.currentChanged.connect(self.set_tab1)
    def update_ui(self,event):
        print('update_ui')
        self.ui_farm.set_view(self.ui_args.args_farm())
    def closeEvent(self,event):
        self.save_pos()
        self.ui_args.close()
        self.ui_farm.close()
        for ui_recr in self.ui_recrs.values():
            ui_recr.close()
    def save_pos(self):
        g=self.geometry()
        d={'geometry':[g.x(),g.y(),g.width(),g.height()],'currentIndex':self.tabs.currentIndex()}
        saveobj.save_json(self.config,d)
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if isinstance(d,dict):
            if (geometry:=d.get('geometry')):
                self.setGeometry(*geometry)
            if (currentIndex:=d.get('currentIndex')) in [0,1]:
                self.tabs.setCurrentIndex(currentIndex)
    @QtCore.pyqtSlot(int)
    def set_tab1(self,index):
        if index==1:
            key,args=self.key_ui_recr()
            if self.ui_recr_key==key:
                return
            self.ui_recr_key=key
            if self.tabs.count()==2:
                self.tabs.removeTab(1)
            if key in self.ui_recrs:
                ui_recr=self.ui_recrs[key]
            else:
                ui_recr = UiRecTag(args)
                self.ui_recrs[key]=ui_recr
            self.tabs.addTab(ui_recr,'Recruit Tag')
            self.tabs.setCurrentIndex(1)
    def key_ui_recr(self):
        args=self.ui_args.args_recr()
        key='{server} {lang}'.format(**args)
        return key,args

class UiTest(QtWidgets.QWidget):
    def __init__(self):
        super(UiTest, self).__init__()
        self.widget_layout = MyVBoxLayout()
        self.setLayout(self.widget_layout)
        def test():
            names=[]
            for attr in dir(QtWidgets):
                name = f'QtWidgets.{attr}'
                v = getattr(QtWidgets, attr)
                type_str = str(type(v))
                if (m := re.match(r'''<class '(?P<typa>[\w\.\-<>]*?)'>''',type_str)):
                    if m.group('typa') =='PyQt6.sip.wrappertype':
                        try:
                            ui_v = v(self)
                            l=QtWidgets.QLineEdit(name)
                            self.widget_layout.addWidget(l)
                            self.widget_layout.addWidget(ui_v)
                            names.append(name)
                        except:
                            pass
            print(names)

        def test1():
            self.view = QtWidgets.QGraphicsView()
            self.scene = QtWidgets.QGraphicsScene()
            self.view.setScene(self.scene)
            panel = QtWidgets.QGraphicsWidget()
            self.scene.addItem(panel)
            layout = QtWidgets.QGraphicsGridLayout()
            panel.setLayout(layout)
            class RectangleWidget(QtWidgets.QGraphicsWidget):
                def __init__(self, rect, parent=None):
                    super(RectangleWidget, self).__init__(parent)
                    self.rect = rect
                def paint(self, painter, *args, **kwargs):
                    painter.drawRect(self.rect)
            for i in range(4):
                for j in range(4):
                    rectangle = RectangleWidget(QtCore.QRectF(0, 0, 50, 50), panel)
                    layout.addItem(rectangle, i, j)
            self.widget_layout.addWidget(self.view)
        test()

        # ['QtWidgets.QAbstractScrollArea', 'QtWidgets.QAbstractSlider', 'QtWidgets.QAbstractSpinBox', 'QtWidgets.QCalendarWidget', 'QtWidgets.QCheckBox', 'QtWidgets.QColorDialog', 'QtWidgets.QColumnView', 'QtWidgets.QComboBox', 'QtWidgets.QCommandLinkButton', 'QtWidgets.QDateEdit', 'QtWidgets.QDateTimeEdit', 'QtWidgets.QDial', 'QtWidgets.QDialog', 'QtWidgets.QDialogButtonBox', 'QtWidgets.QDockWidget', 'QtWidgets.QDoubleSpinBox', 'QtWidgets.QErrorMessage', 'QtWidgets.QFileDialog', 'QtWidgets.QFocusFrame', 'QtWidgets.QFontComboBox', 'QtWidgets.QFontDialog', 'QtWidgets.QFrame', 'QtWidgets.QGraphicsView', 'QtWidgets.QGroupBox', 'QtWidgets.QInputDialog', 'QtWidgets.QKeySequenceEdit', 'QtWidgets.QLCDNumber', 'QtWidgets.QLabel', 'QtWidgets.QLineEdit', 'QtWidgets.QListView', 'QtWidgets.QListWidget', 'QtWidgets.QMainWindow', 'QtWidgets.QMdiArea', 'QtWidgets.QMdiSubWindow', 'QtWidgets.QMenu', 'QtWidgets.QMenuBar', 'QtWidgets.QMessageBox', 'QtWidgets.QPlainTextEdit', 'QtWidgets.QProgressBar', 'QtWidgets.QProgressDialog', 'QtWidgets.QPushButton', 'QtWidgets.QRadioButton', 'QtWidgets.QScrollArea', 'QtWidgets.QScrollBar', 'QtWidgets.QSizeGrip', 'QtWidgets.QSlider', 'QtWidgets.QSpinBox', 'QtWidgets.QSplitter', 'QtWidgets.QStackedWidget', 'QtWidgets.QStatusBar', 'QtWidgets.QTabBar', 'QtWidgets.QTabWidget', 'QtWidgets.QTableView', 'QtWidgets.QTableWidget', 'QtWidgets.QTextBrowser', 'QtWidgets.QTextEdit', 'QtWidgets.QTimeEdit', 'QtWidgets.QToolBar', 'QtWidgets.QToolBox', 'QtWidgets.QToolButton', 'QtWidgets.QTreeView', 'QtWidgets.QTreeWidget', 'QtWidgets.QUndoView', 'QtWidgets.QWidget', 'QtWidgets.QWizard', 'QtWidgets.QWizardPage']

class UiArgs(QtWidgets.QWidget):
    def __init__(self):
        super(UiArgs, self).__init__()
        self.config='./config/UiArgs.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
        self.widget_layout = MyHBoxLayout()
        self.combs={}
        for name,arg in {
            'server':'US CN JP KR',
            'minimize_stage_key':'san minClearTime',
            'lang':'en ja ko zh',
            'show':' '.join([str(i) for i in range(1,11)]),
        }.items():
            label=QtWidgets.QLabel(name)
            comb=QtWidgets.QComboBox()
            comb.addItems(arg.split())
            self.combs[name]=comb
            self.widget_layout.addWidget(label)
            self.widget_layout.addWidget(comb)
            self.widget_layout.addSpacerItem(QtWidgets.QSpacerItem(20, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Fixed))
        self.btn_ok=QtWidgets.QPushButton('OK')
        self.widget_layout.addWidget(self.btn_ok)
        self.widget_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        self.load_pos()
        self.setLayout(self.widget_layout)
    def args(self):
        return {name:comb.currentText() for name,comb in self.combs.items()}
    def args_farm(self):
        return {name:comb.currentText() for name,comb in self.combs.items() if name in ['server','minimize_stage_key','lang']}
    def args_recr(self):
        return {name:comb.currentText() for name,comb in self.combs.items() if name in ['server','lang']}
    def save_pos(self):
        d=[comb.currentText() for name,comb in self.combs.items()]
        saveobj.save_json(self.config,d)
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if d:
            for t,comb in zip(d,self.combs.values()):
                comb.setCurrentText(t)
        # UiItemImg.n=self.combs['show'].currentText()
    def closeEvent(self,event):
        self.save_pos()

def main():
    app = QtWidgets.QApplication([])
    root = UiRoot()
    root.show()
    ret = app.exec()
    exit(ret)

if __name__ == '__main__':
    main()

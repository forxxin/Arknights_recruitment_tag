import os

from PyQt6 import QtWidgets, QtGui, QtCore

from farmcalc import FarmCalc
from qtlayout import MyGridLayout,MyVBoxLayout,MyHBoxLayout
import resource
import stores
try:
    import saveobj
except:
    import mods.saveobj

app_path = os.path.dirname(__file__)
os.chdir(app_path)

class UiFarmStageWorker(QtCore.QObject):
    init_farmstage3 = QtCore.pyqtSignal(tuple,FarmCalc)
    def __init__(self, parent=None):
        super().__init__(parent)
    @QtCore.pyqtSlot(tuple,dict)
    def init_farmstage2(self,key,args):
        data=FarmCalc(**args)
        self.init_farmstage3.emit(key,data)

class UiFarmStageStore(QtWidgets.QWidget):
    init_farmstage1 = QtCore.pyqtSignal(tuple,dict)
    def __init__(self,args, parent=None):
        super().__init__(parent)
        self.views={}
        self.view=None
        self.create_worker()
        self.vlayout = MyVBoxLayout()
        self.set_view(args)
        self.setLayout(self.vlayout)
    def create_worker(self):
        self.qobj_worker = UiFarmStageWorker()
        self.worker_thread = QtCore.QThread()
        self.qobj_worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.init_farmstage1.connect(self.qobj_worker.init_farmstage2)
        self.qobj_worker.init_farmstage3.connect(self.init_farmstage4)
    @QtCore.pyqtSlot(dict)
    def set_view(self,args_raw):
        ks=['server','minimize_stage_key','lang']
        key = tuple(args_raw.get(k) for k in ks)
        args={k:v for k,v in args_raw.items() if k in ks}
        if key in self.views:
            view=self.views[key]
            self.real_set_view(view)
        else:
            self.init_farmstage1.emit(key,args|{'update':False}) #init_farmstage4
    @QtCore.pyqtSlot(tuple,FarmCalc)
    def init_farmstage4(self,key,data):
        self.data=data
        view=UiStores(key,data)
        self.views[key]=view
        self.real_set_view(view)
    @QtCore.pyqtSlot()
    def real_set_view(self,view):
        if self.view!=view:
            if self.vlayout.count()==1:
                v = self.vlayout.itemAt(0).widget()
                self.vlayout.removeWidget(v)
                v.setParent(None)
            self.vlayout.addWidget(view)
            self.view=view
    def close_worker(self):
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
    def closeEvent(self,event):
        self.close_worker()
        for view in self.views.values():
            view.close()

class UiStores(QtWidgets.QWidget):
    def __init__(self,key,data, parent=None, scene=None):
        super().__init__(parent)
        self.key=key
        self.data=stores.Store(server='US',minimize_stage_key='san',lang='en',update=False)
        vlayout = MyVBoxLayout()
        table=QtWidgets.QTableWidget()
        hlayout = MyHBoxLayout()
        label_store = QtWidgets.QLabel('store')
        line_store = QtWidgets.QLineEdit()
        label_item = QtWidgets.QLabel('item')
        line_item = QtWidgets.QLineEdit()
        spin_count = QtWidgets.QSpinBox()
        btn_add=QtWidgets.QPushButton('add')
        
        headers=['store','item','count','token_cost','san_per_token','san_per_item',]
        table.setColumnCount(len(headers));
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        
        table.setRowCount(len(self.data.side_event_memory_store))
        for row,store_item in enumerate(self.data.side_event_memory_store):
            for col,key in enumerate(['store','name','count','token_cost','san_per_token','san_per_item']):
                table_item = QtWidgets.QTableWidgetItem(str(getattr(store_item,key,'')))
                if col==1:
                    if (itemId:=store_item.itemId):
                        if (file:=resource.ItemImg.img(itemId)):
                            table_item.setIcon(QtGui.QIcon(file))
                # table_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, col, table_item)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        # completer_store = QtWidgets.QCompleter(['12','123','',])
        # completer_item = QtWidgets.QCompleter(['12','123','',])
        # line_store.setCompleter(completer_store)
        # line_item.setCompleter(completer_item)
        # spin_count.setMinimum(1)
        
        self.setLayout(vlayout)
        vlayout.addWidget(table)
        # vlayout.addLayout(hlayout)
        # hlayout.addWidget(label_store)
        # hlayout.addWidget(line_store)
        # hlayout.addWidget(label_item)
        # hlayout.addWidget(line_item)
        # hlayout.addWidget(spin_count)
        # hlayout.addWidget(btn_add)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    root = QtWidgets.QMainWindow()
    root.setWindowTitle(f"Store Priority")
    ui=UiFarmStageStore({'server':'US','minimize_stage_key':'san','lang':'en','show':'1'})
    root.setCentralWidget(ui)
    root.show()
    ret = app.exec()
    exit(ret)

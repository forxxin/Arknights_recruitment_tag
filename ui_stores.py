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

class UiStores(QtWidgets.QWidget):
    def __init__(self,args, parent=None):
        super().__init__(parent)
        self.data=stores.Store(**(args|{'lang':'en'}),update=False)
        # self.data=stores.Store(server='US',minimize_stage_key='san',,update=False)
        vlayout = MyVBoxLayout()
        tabs = QtWidgets.QTabWidget()
        self.san_icon=QtGui.QIcon(resource.ItemImg.img('AP_GAMEPLAY'))
        for idx,(store_info,store_sorted) in enumerate(self.data.stores_sorted.items()):
            store_name,store_icon = store_info
            store_icon = QtGui.QIcon(store_icon)
            table=self.create_table(store_sorted,store_icon)
            tabs.addTab(table,store_name)
            tabs.setTabIcon(idx,store_icon)
            # for store_item in store_sorted:
                # print(store_item.name,store_item.count,store_item.token_cost,store_item.san_per_token)
        self.setLayout(vlayout)
        vlayout.addWidget(tabs)
    def create_table(self,store_sorted,store_icon):
        table=QtWidgets.QTableWidget()
        table.setSortingEnabled(True)
        keys=['name','count','token_cost','san_per_token','san_per_item']
        headers=keys
        table.setColumnCount(len(headers));
        table.setHorizontalHeaderLabels(headers)
        # table.verticalHeader().setVisible(False)
        table.setRowCount(len(store_sorted))
        for row,store_item in enumerate(store_sorted):
            for col,key in enumerate(keys):
                table_item = QtWidgets.QTableWidgetItem()
                table_item.setData(QtCore.Qt.ItemDataRole.DisplayRole, getattr(store_item,key))
                if key=='name':
                    if (itemId:=store_item.itemId):
                        if (file:=resource.ItemImg.img(itemId)):
                            table_item.setIcon(QtGui.QIcon(file))
                elif key=='token_cost':
                    table_item.setIcon(store_icon)
                elif key=='san_per_item':
                    table_item.setIcon(self.san_icon)
                # table_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, col, table_item)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        return table
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    root = QtWidgets.QMainWindow()
    root.setWindowTitle(f"Store Priority")
    ui=UiStores({'server':'US','minimize_stage_key':'san','lang':'en'})
    root.setCentralWidget(ui)
    root.show()
    ret = app.exec()
    exit(ret)

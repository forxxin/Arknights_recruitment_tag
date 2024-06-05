import os

from PyQt6 import QtWidgets, QtGui, QtCore

from farmcalc import FarmCalc
from qtlayout import MyGridLayout,MyVBoxLayout,MyHBoxLayout
import resource
import char as character
try:
    import saveobj
except:
    import mods.saveobj

app_path = os.path.dirname(__file__)
os.chdir(app_path)

class UiChars(QtWidgets.QWidget):
    def __init__(self,args,parent=None):
        super().__init__(parent)
        self.data=character.Chars(**args)
            
        vlayout = MyVBoxLayout()
        table=QtWidgets.QTableWidget()
        table.setSortingEnabled(True)
        keys=['characterId','name','tier','profession','subProfessionId','position','rarity','tags','evolveCost']
        headers=keys
        table.setColumnCount(len(headers));
        table.setHorizontalHeaderLabels(headers)
        # table.verticalHeader().setVisible(False)
        table.setRowCount(len(self.data.chars_excel))
        for row,(characterId,char) in enumerate(self.data.chars_excel.items()):
            for col,key in enumerate(keys):
                table_item = QtWidgets.QTableWidgetItem()
                table_item.setData(QtCore.Qt.ItemDataRole.DisplayRole, getattr(char,key))
                if key=='name':
                    if (characterId:=char.characterId):
                        if (file:=resource.Img.avatar(characterId)):
                            table_item.setIcon(QtGui.QIcon(file))
                elif key=='token_cost':
                    table_item.setIcon(store_icon)
                elif key=='san_per_item':
                    table_item.setIcon(self.san_icon)
                # table_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, col, table_item)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.setLayout(vlayout)
        vlayout.addWidget(table)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    root = QtWidgets.QMainWindow()
    root.setWindowTitle(f"Store Priority")
    ui=UiChars({'server':'US','lang':'en'})
    root.setCentralWidget(ui)
    root.show()
    ret = app.exec()
    exit(ret)

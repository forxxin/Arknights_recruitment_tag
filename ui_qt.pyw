import sys
import os
import re
try:
    import PyQt6
    import PyQt6.QtWidgets
    import PyQt6.QtGui
    import PyQt6.QtCore
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
except Exception as e:
    print(e)
    
import anhrtags
import farmcalc

try:
    import saveobj
except:
    import mods.saveobj


class UiRoot(QMainWindow):
    def __init__(self):
        super(UiRoot, self).__init__()
        self.setWindowTitle("Arknights Best Stages")
        self.scroll = PyQt6.QtWidgets.QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.widget = PyQt6.QtWidgets.QWidget(self)
        self.widget_layout = PyQt6.QtWidgets.QVBoxLayout()
        self.setCentralWidget(self.scroll)
        self.scroll.setWidget(self.widget)
        self.widget.setLayout(self.widget_layout)
        self.config='./config/UiRoot.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
    def add(self,children):
        if isinstance(children,list):
            for child in children:
                self.widget_layout.addWidget(child)
        else:
            self.widget_layout.addWidget(children)
    def save_pos(self):
        g=self.geometry()
        d=[g.x(),g.y(),g.width(),g.height()]
        saveobj.save_json(self.config,d)
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if d:
            self.setGeometry(*d)
class UiTest(PyQt6.QtWidgets.QWidget):
    def __init__(self):
        super(UiTest, self).__init__()
        self.widget_layout = PyQt6.QtWidgets.QVBoxLayout()
        self.setLayout(self.widget_layout)
        def test():
            names=[]
            for attr in dir(PyQt6.QtWidgets):
                name = f'PyQt6.QtWidgets.{attr}'
                v = getattr(PyQt6.QtWidgets, attr)
                type_str = str(type(v))
                if (m := re.match(r'''<class '(?P<typa>[\w\.\-<>]*?)'>''',type_str)):
                    if m.group('typa') =='PyQt6.sip.wrappertype':
                        try:
                            ui_v = v(self)
                            l=PyQt6.QtWidgets.QLineEdit(name)
                            self.widget_layout.addWidget(l)
                            self.widget_layout.addWidget(ui_v)
                            names.append(name)
                        except:
                            pass
            print(names)
        # test()
        self.view = PyQt6.QtWidgets.QGraphicsView()
        self.scene = PyQt6.QtWidgets.QGraphicsScene()
        self.view.setScene(self.scene)

        panel = PyQt6.QtWidgets.QGraphicsWidget()
        self.scene.addItem(panel)

        layout = PyQt6.QtWidgets.QGraphicsGridLayout()
        panel.setLayout(layout)

        class RectangleWidget(PyQt6.QtWidgets.QGraphicsWidget):
            def __init__(self, rect, parent=None):
                super(RectangleWidget, self).__init__(parent)
                self.rect = rect

            def paint(self, painter, *args, **kwargs):
                print('Paint Called')
                painter.drawRect(self.rect)
        for i in range(4):
            for j in range(4):
                rectangle = RectangleWidget(PyQt6.QtCore.QRectF(0, 0, 50, 50), panel)
                layout.addItem(rectangle, i, j)
        self.widget_layout.addWidget(self.view)
        
        # ['PyQt6.QtWidgets.QAbstractScrollArea', 'PyQt6.QtWidgets.QAbstractSlider', 'PyQt6.QtWidgets.QAbstractSpinBox', 'PyQt6.QtWidgets.QCalendarWidget', 'PyQt6.QtWidgets.QCheckBox', 'PyQt6.QtWidgets.QColorDialog', 'PyQt6.QtWidgets.QColumnView', 'PyQt6.QtWidgets.QComboBox', 'PyQt6.QtWidgets.QCommandLinkButton', 'PyQt6.QtWidgets.QDateEdit', 'PyQt6.QtWidgets.QDateTimeEdit', 'PyQt6.QtWidgets.QDial', 'PyQt6.QtWidgets.QDialog', 'PyQt6.QtWidgets.QDialogButtonBox', 'PyQt6.QtWidgets.QDockWidget', 'PyQt6.QtWidgets.QDoubleSpinBox', 'PyQt6.QtWidgets.QErrorMessage', 'PyQt6.QtWidgets.QFileDialog', 'PyQt6.QtWidgets.QFocusFrame', 'PyQt6.QtWidgets.QFontComboBox', 'PyQt6.QtWidgets.QFontDialog', 'PyQt6.QtWidgets.QFrame', 'PyQt6.QtWidgets.QGraphicsView', 'PyQt6.QtWidgets.QGroupBox', 'PyQt6.QtWidgets.QInputDialog', 'PyQt6.QtWidgets.QKeySequenceEdit', 'PyQt6.QtWidgets.QLCDNumber', 'PyQt6.QtWidgets.QLabel', 'PyQt6.QtWidgets.QLineEdit', 'PyQt6.QtWidgets.QListView', 'PyQt6.QtWidgets.QListWidget', 'PyQt6.QtWidgets.QMainWindow', 'PyQt6.QtWidgets.QMdiArea', 'PyQt6.QtWidgets.QMdiSubWindow', 'PyQt6.QtWidgets.QMenu', 'PyQt6.QtWidgets.QMenuBar', 'PyQt6.QtWidgets.QMessageBox', 'PyQt6.QtWidgets.QPlainTextEdit', 'PyQt6.QtWidgets.QProgressBar', 'PyQt6.QtWidgets.QProgressDialog', 'PyQt6.QtWidgets.QPushButton', 'PyQt6.QtWidgets.QRadioButton', 'PyQt6.QtWidgets.QScrollArea', 'PyQt6.QtWidgets.QScrollBar', 'PyQt6.QtWidgets.QSizeGrip', 'PyQt6.QtWidgets.QSlider', 'PyQt6.QtWidgets.QSpinBox', 'PyQt6.QtWidgets.QSplitter', 'PyQt6.QtWidgets.QStackedWidget', 'PyQt6.QtWidgets.QStatusBar', 'PyQt6.QtWidgets.QTabBar', 'PyQt6.QtWidgets.QTabWidget', 'PyQt6.QtWidgets.QTableView', 'PyQt6.QtWidgets.QTableWidget', 'PyQt6.QtWidgets.QTextBrowser', 'PyQt6.QtWidgets.QTextEdit', 'PyQt6.QtWidgets.QTimeEdit', 'PyQt6.QtWidgets.QToolBar', 'PyQt6.QtWidgets.QToolBox', 'PyQt6.QtWidgets.QToolButton', 'PyQt6.QtWidgets.QTreeView', 'PyQt6.QtWidgets.QTreeWidget', 'PyQt6.QtWidgets.QUndoView', 'PyQt6.QtWidgets.QWidget', 'PyQt6.QtWidgets.QWizard', 'PyQt6.QtWidgets.QWizardPage']

def img_data2file(img_data):
    for file in img_data:
        url = farmcalc.Data.url_material + file
        yield anhrtags.GData.img(file,url)

class UiItemImg(PyQt6.QtWidgets.QGraphicsItem):
    def __init__(self, item, parent=None):
        super(UiItemImg, self).__init__(parent)
        # dump(self)
        self.setFlag(PyQt6.QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(PyQt6.QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.len=80
        self.len1=66
        self.wordlen=11
        self.item = item
        self.beststage = str([stage.code for stage in self.item.beststage])
        self.pixmaps = []
        file,file1 = img_data2file(item.img_data)
        self.pixmaps.append(PyQt6.QtGui.QPixmap(file).scaled(self.len,self.len,aspectRatioMode=PyQt6.QtCore.Qt.AspectRatioMode.KeepAspectRatio,transformMode=PyQt6.QtCore.Qt.TransformationMode.SmoothTransformation))
        self.pixmaps.append(PyQt6.QtGui.QPixmap(file1).scaled(self.len1,self.len1,aspectRatioMode=PyQt6.QtCore.Qt.AspectRatioMode.KeepAspectRatio,transformMode=PyQt6.QtCore.Qt.TransformationMode.SmoothTransformation))
    def paint(self, painter, *args, **kwargs):
        pixmap,pixmap1 = self.pixmaps
        x=int((self.len-self.len1)/2)
        painter.drawPixmap(0,0,pixmap)
        painter.drawPixmap(pixmap.rect().center()-pixmap1.rect().center(),pixmap1)
        painter.drawText(0,self.len+self.wordlen,self.item.name)
        painter.drawText(0,self.len+self.wordlen*2,self.beststage)
    def boundingRect(self):
        return PyQt6.QtCore.QRectF(0,0,self.len,self.len)

class UiGraphicsView(PyQt6.QtWidgets.QGraphicsView):
    def __init__(self):
        super(UiGraphicsView, self).__init__()
        self.scene = PyQt6.QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.imgs=[]
        self.config='./config/UiGraphicsView.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
    def addimg(self,children):
        if isinstance(children,list):
            for child in children:
                self.scene.addItem(child)
                self.imgs.append(child)
        else:
            self.scene.addItem(children)
            self.imgs.append(children)
    def addarrow(self,children):
        if isinstance(children,list):
            for child in children:
                self.scene.addItem(child)
        else:
            self.scene.addItem(children)
    def mouseMoveEvent(self,event):
        self.update()
        return super().mouseMoveEvent(event)
    def update(self):
        self.scene.update()
        return super().update()
    def save_pos(self):
        d={img.item.id:(p.x(),p.y()) for img in self.imgs if (p:=img.pos())}
        saveobj.save_json(self.config,d)
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if d:
            for img in self.imgs:
                if (p:=d.get(img.item.id)):
                    img.setPos(*p)

class UiFormulaArrow(PyQt6.QtWidgets.QGraphicsItem):

    def __init__(self, startItem, endItem, parent=None, scene=None):
        super(UiFormulaArrow, self).__init__()
        self.startItem = startItem
        self.endItem = endItem

    def boundingRect(self):
        p1 = self.startItem.pos() + self.startItem.boundingRect().center()
        p3 = self.endItem.pos() + self.endItem.boundingRect().center()
        bounds = p3 - p1
        size = PyQt6.QtCore.QSizeF(abs(bounds.x()), abs(bounds.y()))
        return PyQt6.QtCore.QRectF(p1, size)

    def paint(self, painter, option, widget=None):

        p1 = self.startItem.pos() + self.startItem.boundingRect().center()
        p3 = self.endItem.pos() + self.endItem.boundingRect().center()

        pen = PyQt6.QtGui.QPen()
        pen.setWidth(1)
        # painter.setRenderHint(PyQt6.QtGui.QPainter.Antialiasing)

        if self.isSelected():
            pen.setStyle(PyQt6.QtCore.Qt.PenStyle.DashLine)
        else:
            pen.setStyle(PyQt6.QtCore.Qt.PenStyle.SolidLine)

        # pen.setColor(PyQt6.QtGui.QColor.black)
        painter.setPen(pen)
        painter.drawLine(PyQt6.QtCore.QLineF(p1, p3))
        # painter.setBrush(PyQt6.QtCore.Qt.NoBrush)

    def updatePosition(self):
        pass

def main():
    app = QApplication(sys.argv)
    root = UiRoot()
    view= UiGraphicsView()
    # root.add(UiTest())
    root.add(view)
    itemimgs={}
    for itemId,item in farmcalc.Data.items.items():
        if item.img_data:
            itemimg = UiItemImg(item)
            view.addimg(itemimg)
            itemimgs[item.id]=itemimg
    for formulaId,formula in farmcalc.Data.formulas.items():
        for item in formula.ins:
            for item1 in formula.out:
                itemimg = itemimgs.get(item.item.id)
                itemimg1 = itemimgs.get(item1.item.id)
                if itemimg and itemimg1:
                    arrow=UiFormulaArrow(itemimg,itemimg1)
                    view.addarrow(arrow)

    def closeEvent(event):
        view.save_pos()
        root.save_pos()
    root.closeEvent=closeEvent
    
    root.load_pos()
    view.load_pos()
    
    root.show()
    ret = app.exec()
    sys.exit()

if __name__ == '__main__':
    main()
    

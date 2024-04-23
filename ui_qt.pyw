import sys
import os
import re
from functools import cache
try:
    import PyQt6
    import PyQt6.QtWidgets
    import PyQt6.QtGui
    import PyQt6.QtCore
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
    from PyQt6.QtCore import QObject,pyqtSignal,Qt,pyqtSlot
except Exception as e:
    print(e)

import anhrtags
import farmcalc

try:
    import saveobj
except:
    import mods.saveobj

try:
    from test import dump
except:
    def dump(**a):
        pass

class UiRoot(QMainWindow):
    def __init__(self):
        super(UiRoot, self).__init__()
        self.setWindowTitle(f"Arknights Best Stages"  )
        # self.scroll = PyQt6.QtWidgets.QScrollArea()
        # self.scroll.setVerticalScrollBarPolicy(PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # self.scroll.setHorizontalScrollBarPolicy(PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.scroll.setWidgetResizable(True)
        self.widget = PyQt6.QtWidgets.QWidget(self)
        self.widget_layout = PyQt6.QtWidgets.QVBoxLayout()
        # self.setCentralWidget(self.scroll)
        self.setCentralWidget(self.widget)
        # self.scroll.setWidget(self.widget)
        self.widget.setLayout(self.widget_layout)
        self.config='./config/UiRoot.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
        self.widget_args = UiArgs()
        self.widget_layout.addWidget(self.widget_args)
        self.view=None
    def args(self):
        return self.widget_args.args()
    def add(self,children):
        if isinstance(children,list):
            for child in children:
                self.widget_layout.addWidget(child)
        else:
            self.widget_layout.addWidget(children)
    def set_view(self,view):
        if self.view!=view:
            if self.widget_layout.count()==2:
                v = self.widget_layout.itemAt(1).widget()
                self.widget_layout.removeWidget(v)
                v.setParent(None)
            self.widget_layout.addWidget(view)
    def save_pos(self):
        g=self.geometry()
        d=[g.x(),g.y(),g.width(),g.height()]
        saveobj.save_json(self.config,d)
        self.widget_args.save_pos()
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if d:
            self.setGeometry(*d)
        self.widget_args.load_pos()

class UiStageSelect(PyQt6.QtWidgets.QDialog):
    def __init__(self):
        super(UiStageSelect, self).__init__()
        layout=PyQt6.QtWidgets.QVBoxLayout()
        scroll = PyQt6.QtWidgets.QScrollArea(self)
        scroll.setVerticalScrollBarPolicy(PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(PyQt6.QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(True)
        widget = PyQt6.QtWidgets.QWidget()
        self.layout = PyQt6.QtWidgets.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(scroll)
        scroll.setWidget(widget)
        widget.setLayout(self.layout)
        stagebyzone={}
        for stage in farmcalc.Data.stages.values():
            stagebyzone.setdefault(stage.zoneId,[]).append(stage)
        row=-1
        for zoneId,stages in stagebyzone.items():
            check_all = PyQt6.QtWidgets.QCheckBox(zoneId)
            row+=1
            self.layout.addWidget(check_all,row,0)
            col=1
            for stage in stages:
                check = PyQt6.QtWidgets.QCheckBox(stage.code)
                self.layout.addWidget(check,row,col)
                col+=1

class UiArgs(PyQt6.QtWidgets.QWidget):
    def __init__(self):
        super(UiArgs, self).__init__()
        self.config='./config/UiArgs.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
        self.widget_layout = PyQt6.QtWidgets.QHBoxLayout()
        self.setLayout(self.widget_layout)
        self.combs={}
        for name,arg in {
            'server':'US CN JP KR',
            'minimize_stage_key':'san minClearTime',
            'lang':'en ja ko zh',
            'show':' '.join([str(i) for i in range(1,11)]),
        }.items():
            label=PyQt6.QtWidgets.QLabel(name)
            comb=PyQt6.QtWidgets.QComboBox()
            comb.addItems(arg.split())
            self.combs[name]=comb
            self.widget_layout.addWidget(label)
            self.widget_layout.addWidget(comb)
            self.widget_layout.addSpacerItem(PyQt6.QtWidgets.QSpacerItem(20, 0, hPolicy=PyQt6.QtWidgets.QSizePolicy.Policy.Fixed))
        self.btn_ok=PyQt6.QtWidgets.QPushButton('OK')
        self.widget_layout.addWidget(self.btn_ok)
        # self.btn_stages=PyQt6.QtWidgets.QPushButton('Stages')
        # self.btn_stages.clicked.connect(self.open_stages)
        # self.widget_layout.addWidget(self.btn_stages)
        self.widget_layout.addSpacerItem(PyQt6.QtWidgets.QSpacerItem(0, 0, hPolicy=PyQt6.QtWidgets.QSizePolicy.Policy.Expanding))
    def open_stages(self):
        stages = UiStageSelect()
        stages.exec()
    def args(self):
        return {name:comb.currentText() for name,comb in self.combs.items()}
    def save_pos(self):
        d=[comb.currentText() for name,comb in self.combs.items()]
        saveobj.save_json(self.config,d)
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if d:
            for t,comb in zip(d,self.combs.values()):
                comb.setCurrentText(t)
        UiItemImg.n=self.combs['show'].currentText()

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

        def test1():
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
                    painter.drawRect(self.rect)
            for i in range(4):
                for j in range(4):
                    rectangle = RectangleWidget(PyQt6.QtCore.QRectF(0, 0, 50, 50), panel)
                    layout.addItem(rectangle, i, j)
            self.widget_layout.addWidget(self.view)
        test()

        # ['PyQt6.QtWidgets.QAbstractScrollArea', 'PyQt6.QtWidgets.QAbstractSlider', 'PyQt6.QtWidgets.QAbstractSpinBox', 'PyQt6.QtWidgets.QCalendarWidget', 'PyQt6.QtWidgets.QCheckBox', 'PyQt6.QtWidgets.QColorDialog', 'PyQt6.QtWidgets.QColumnView', 'PyQt6.QtWidgets.QComboBox', 'PyQt6.QtWidgets.QCommandLinkButton', 'PyQt6.QtWidgets.QDateEdit', 'PyQt6.QtWidgets.QDateTimeEdit', 'PyQt6.QtWidgets.QDial', 'PyQt6.QtWidgets.QDialog', 'PyQt6.QtWidgets.QDialogButtonBox', 'PyQt6.QtWidgets.QDockWidget', 'PyQt6.QtWidgets.QDoubleSpinBox', 'PyQt6.QtWidgets.QErrorMessage', 'PyQt6.QtWidgets.QFileDialog', 'PyQt6.QtWidgets.QFocusFrame', 'PyQt6.QtWidgets.QFontComboBox', 'PyQt6.QtWidgets.QFontDialog', 'PyQt6.QtWidgets.QFrame', 'PyQt6.QtWidgets.QGraphicsView', 'PyQt6.QtWidgets.QGroupBox', 'PyQt6.QtWidgets.QInputDialog', 'PyQt6.QtWidgets.QKeySequenceEdit', 'PyQt6.QtWidgets.QLCDNumber', 'PyQt6.QtWidgets.QLabel', 'PyQt6.QtWidgets.QLineEdit', 'PyQt6.QtWidgets.QListView', 'PyQt6.QtWidgets.QListWidget', 'PyQt6.QtWidgets.QMainWindow', 'PyQt6.QtWidgets.QMdiArea', 'PyQt6.QtWidgets.QMdiSubWindow', 'PyQt6.QtWidgets.QMenu', 'PyQt6.QtWidgets.QMenuBar', 'PyQt6.QtWidgets.QMessageBox', 'PyQt6.QtWidgets.QPlainTextEdit', 'PyQt6.QtWidgets.QProgressBar', 'PyQt6.QtWidgets.QProgressDialog', 'PyQt6.QtWidgets.QPushButton', 'PyQt6.QtWidgets.QRadioButton', 'PyQt6.QtWidgets.QScrollArea', 'PyQt6.QtWidgets.QScrollBar', 'PyQt6.QtWidgets.QSizeGrip', 'PyQt6.QtWidgets.QSlider', 'PyQt6.QtWidgets.QSpinBox', 'PyQt6.QtWidgets.QSplitter', 'PyQt6.QtWidgets.QStackedWidget', 'PyQt6.QtWidgets.QStatusBar', 'PyQt6.QtWidgets.QTabBar', 'PyQt6.QtWidgets.QTabWidget', 'PyQt6.QtWidgets.QTableView', 'PyQt6.QtWidgets.QTableWidget', 'PyQt6.QtWidgets.QTextBrowser', 'PyQt6.QtWidgets.QTextEdit', 'PyQt6.QtWidgets.QTimeEdit', 'PyQt6.QtWidgets.QToolBar', 'PyQt6.QtWidgets.QToolBox', 'PyQt6.QtWidgets.QToolButton', 'PyQt6.QtWidgets.QTreeView', 'PyQt6.QtWidgets.QTreeWidget', 'PyQt6.QtWidgets.QUndoView', 'PyQt6.QtWidgets.QWidget', 'PyQt6.QtWidgets.QWizard', 'PyQt6.QtWidgets.QWizardPage']

def img_data2file(img_data):
    for file in img_data:
        url = farmcalc.Data.url_material + file
        yield anhrtags.GData.img(file,url)

class UiItemImg(PyQt6.QtWidgets.QGraphicsItem):
    n=3
    len=80
    len1=66
    wordlen=11
    def __init__(self, item, parent=None):
        super(UiItemImg, self).__init__(parent)
        self.x=0
        self.y=0
        self.setFlag(PyQt6.QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(PyQt6.QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.item = item
        self.beststages = [([stage.code for stage in stages],san) for stages,san in self.item.beststage]
        self.strs = []
        for idx,(stages,san) in enumerate(self.beststages):
            s=f"""[{', '.join(stages)}] {round(san,1):g}"""
            if s not in self.strs:
                self.strs.append(s)
        self.pixmaps = []
        file,file1 = img_data2file(item.img_data)
        self.pixmaps.append(PyQt6.QtGui.QPixmap(file).scaled(UiItemImg.len,UiItemImg.len,aspectRatioMode=PyQt6.QtCore.Qt.AspectRatioMode.KeepAspectRatio,transformMode=PyQt6.QtCore.Qt.TransformationMode.SmoothTransformation))
        self.pixmaps.append(PyQt6.QtGui.QPixmap(file1).scaled(UiItemImg.len1,UiItemImg.len1,aspectRatioMode=PyQt6.QtCore.Qt.AspectRatioMode.KeepAspectRatio,transformMode=PyQt6.QtCore.Qt.TransformationMode.SmoothTransformation))
    def paint(self, painter, option, widget):
        pixmap,pixmap1 = self.pixmaps
        x=int((UiItemImg.len-UiItemImg.len1)/2)
        painter.drawPixmap(0,0,pixmap)
        painter.drawPixmap(pixmap.rect().center()-pixmap1.rect().center(),pixmap1)
        painter.drawText(0,UiItemImg.len+UiItemImg.wordlen,self.item.name)
        for idx,s in enumerate(self.strs):
            if idx>=int(UiItemImg.n):
                if not self.isSelected():
                    break
            painter.drawText(0,UiItemImg.len+UiItemImg.wordlen*(2+idx),s)
    def boundingRect(self):
        return PyQt6.QtCore.QRectF(0,0,UiItemImg.len,UiItemImg.len)

class UiGraphicsView(PyQt6.QtWidgets.QGraphicsView):
    xsd=10
    ysd=UiItemImg.len+UiItemImg.wordlen*(1+UiItemImg.n)
    def __init__(self,key):
        super(UiGraphicsView, self).__init__()
        self.key=' '.join(key)
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
    def mousePressEvent(self,event):
        self.update()
        return super().mousePressEvent(event)
    def mouseReleaseEvent(self,event):
        for img in self.scene.selectedItems():
            p=img.pos()
            x,y=p.x(),p.y()
            x,y=round(x/UiGraphicsView.xsd),round(y/UiGraphicsView.ysd)
            img.x = x
            img.y = y
            img.setPos(x*UiGraphicsView.xsd,y*UiGraphicsView.ysd)
            self.update()
        return super().mouseReleaseEvent(event)
    @staticmethod
    def init_ysd():
        UiGraphicsView.ysd=UiItemImg.len+UiItemImg.wordlen*(1+int(UiItemImg.n))
    def update_ysd(self):
        UiGraphicsView.ysd=UiItemImg.len+UiItemImg.wordlen*(1+int(UiItemImg.n))
        for img in self.imgs:
            img.setPos(img.x*UiGraphicsView.xsd,img.y*UiGraphicsView.ysd)
        self.update()
    def mouseMoveEvent(self,event):
        self.update()
        return super().mouseMoveEvent(event)
    def update(self):
        self.scene.update()
        return super().update()
    def save_pos(self):
        ds=saveobj.load_json(self.config) or {}
        d={img.item.id:(img.x,img.y) for img in self.imgs}
        minx=min([x for itemId,(x,y) in d.items()])
        miny=min([y for itemId,(x,y) in d.items()])
        d={itemId:(x-minx,y-miny) for itemId,(x,y) in d.items()}
        ds[self.key]=d
        saveobj.save_json(self.config,ds)
    def load_pos(self):
        ds=saveobj.load_json(self.config) or {}
        d=ds.get(self.key)
        if not d:
            d = {"30011":[45,5],"30012":[45,4],"30013":[45,3],"30014":[54,1],"30061":[0,5],"30062":[0,4],"30063":[0,3],"30064":[0,1],"30031":[10,5],"30032":[10,4],"30033":[10,3],"30034":[10,2],"30021":[27,5],"30022":[27,4],"30023":[27,3],"30024":[32,2],"30041":[36,5],"30042":[36,4],"30043":[36,3],"30044":[41,1],"30051":[19,5],"30052":[19,4],"30053":[19,3],"30054":[27,1],"30073":[63,3],"30074":[13,1],"30083":[82,3],"30084":[79,1],"30093":[91,3],"30094":[93,1],"30103":[54,3],"30104":[66,1],"31013":[65,4],"31014":[60,2],"31023":[71,3],"31024":[88,2],"30115":[41,0],"30125":[12,0],"30135":[73,0],"31033":[78,4],"31034":[74,2]}
        if d:
            for img in self.imgs:
                if (p:=d.get(img.item.id)):
                    x,y=p
                    img.setPos(x*UiGraphicsView.xsd,y*UiGraphicsView.ysd)
                    img.x=x
                    img.y=y

class UiFormulaArrow(PyQt6.QtWidgets.QGraphicsItem):
    def __init__(self, startItem, endItem,color, parent=None, scene=None):
        super(UiFormulaArrow, self).__init__()
        self.startItem = startItem
        self.endItem = endItem
        self.color=color
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
        # pen.setWidth(1)
        # painter.setRenderHint(PyQt6.QtGui.QPainter.Antialiasing)
        # if self.isSelected():
        # pen.setStyle(PyQt6.QtCore.Qt.PenStyle.DashLine)
        # else:
        # pen.setStyle(PyQt6.QtCore.Qt.PenStyle.SolidLine)
        pen.setColor(PyQt6.QtGui.QColor(self.color)) #https://doc.qt.io/qtforpython-5/PySide2/QtGui/QColorConstants.html
        painter.setPen(pen)
        painter.drawLine(PyQt6.QtCore.QLineF(p1, p3))
        # painter.setBrush(PyQt6.QtGui.QBrush(PyQt6.QtCore.Qt.GlobalColor.white))
    @pyqtSlot(str)
    def set_color(self,color):
        self.color=color

@cache
def getcolor():
    colorid={}
    colorid2={}
    for formulaId,formula in farmcalc.Data.formulas.items():
        colorid[formula.id]=(0,set([item.item.id for item in formula.ins+formula.out]))
    for formulaId,(color,itemids) in colorid.items():
        while True:
            intersect=False
            for formulaId1,(color1,itemids1) in colorid2.items():
                if formulaId!=formulaId1 and color==color1 and (itemids & itemids1) :
                    intersect=True
                    break
            if not intersect:
                colorid2[formulaId]=(color,itemids)
                break
            color+=1
    colors=['Red', 'Green', 'Blue', 'Cyan', 'Magenta', 'Yellow', 'DarkRed', 'DarkGreen', 'DarkBlue', 'DarkCyan', 'DarkMagenta', 'DarkYellow',]
    arrowcolor={}
    for formulaId1,(color1,itemids1) in colorid2.items():
        try:
            arrowcolor[formulaId1]=colors[color1]
        except:
            arrowcolor[formulaId1]='black'
    return arrowcolor

def farmcalc_view(root,key,**args):
    farmcalc.init(**args)
    view= UiGraphicsView(key)
    imgitems={}
    for itemId,item in farmcalc.Data.items.items():
        if item.img_data:
            imgitem = UiItemImg(item)
            imgitems[item.id]=imgitem
    arrowcolor = getcolor()
    for formulaId,formula in farmcalc.Data.formulas.items():
        for item in formula.ins:
            for item1 in formula.out:
                imgitem = imgitems.get(item.item.id)
                imgitem1 = imgitems.get(item1.item.id)
                if imgitem and imgitem1:
                    arrow=UiFormulaArrow(imgitem,imgitem1,arrowcolor[formula.id])
                    view.addarrow(arrow)
    for imgitem in imgitems.values():
        view.addimg(imgitem)
    view.load_pos()
    return view

def args2key(args):
    return tuple(args.get(k) for k in ['server','minimize_stage_key','lang'])

def main():
    app = QApplication(sys.argv)
    root = UiRoot()
    root.load_pos()
    views={}
    @pyqtSlot()
    def set_view():
        args=root.args()
        key =args2key(args)
        args={k:v for k,v in args.items() if k in ['server','minimize_stage_key','lang']}
        if key in views:
            view=views[key]
        else:
            view=farmcalc_view(root,key,**args,update=False)
            views[key]=view
        root.set_view(view)
        return view
    root.widget_args.btn_ok.clicked.connect(set_view)
    root.widget_args.combs['minimize_stage_key'].currentTextChanged.connect(set_view)
    root.widget_args.combs['lang'].currentTextChanged.connect(set_view)
    @pyqtSlot(str)
    def UiItemImg_n(text):
        UiItemImg.n=text
        view = set_view()
        view.update_ysd()
    root.widget_args.combs['show'].currentTextChanged.connect(UiItemImg_n)
    # root.add(UiTest())
    
    UiGraphicsView.init_ysd()
    set_view()

    def closeEvent(event):
        for view in views.values():
            view.save_pos()
        root.save_pos()
    root.closeEvent=closeEvent
    root.show()
    ret = app.exec()
    sys.exit()

if __name__ == '__main__':
    main()

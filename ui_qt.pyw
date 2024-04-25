
import os
import re
from functools import cache
try:
    from PyQt6 import QtWidgets, QtGui, QtCore
except Exception as e:
    print(e)

import anhrtags
import farmcalc
import char
from char import MyGridLayout,MyVBoxLayout,MyHBoxLayout

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
        self.setWindowTitle(f"Arknights Tool")
        self.ui_farm = UiFarmStage()
        self.ui_farm.load_pos()
        args=self.ui_farm.ui_args.args()
        char.init(server=args.get('server'),lang=args.get('lang'))
        self.ui_recr = char.UiRecTag({})
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.ui_farm,'Best Stages')
        tabs.addTab(self.ui_recr,'Recruit Tag')
        self.setCentralWidget(tabs)
        self.load_pos()
    def closeEvent(self,event):
        self.save_pos()
        self.ui_farm.close_worker()
        self.ui_recr.close_worker()
    def save_pos(self):
        g=self.geometry()
        d=[g.x(),g.y(),g.width(),g.height()]
        saveobj.save_json(self.config,d)
        self.ui_farm.save_pos()
    def load_pos(self):
        d=saveobj.load_json(self.config)
        if d:
            self.setGeometry(*d)

class UiFarmStageWorker(QtCore.QObject):
    finish_init = QtCore.pyqtSignal(tuple)
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    @QtCore.pyqtSlot(tuple,dict)
    def init_farmstage(self,key,args):
        farmcalc.init(**args)
        self.finish_init.emit(key)

class UiFarmStage(QtWidgets.QWidget):
    signal_init = QtCore.pyqtSignal(tuple,dict)
    def __init__(self):
        super(UiFarmStage, self).__init__()
        self.views={}
        self.view=None
        self.ui_args = UiArgs()
        self.ui_args.btn_ok.clicked.connect(self.set_view)
        self.ui_args.combs['minimize_stage_key'].currentTextChanged.connect(self.set_view)
        self.ui_args.combs['lang'].currentTextChanged.connect(self.set_view)
        self.ui_args.combs['show'].currentTextChanged.connect(self.UiItemImg_n)
        self.vlayout = MyVBoxLayout()
        self.vlayout.addWidget(self.ui_args)
        UiGraphicsView.init_ysd()
        self.set_view()
        self.setLayout(self.vlayout)
        
        self.qobj_worker = UiFarmStageWorker()
        self.worker_thread = QtCore.QThread()
        self.qobj_worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.signal_init.connect(self.qobj_worker.init_farmstage)
        self.qobj_worker.finish_init.connect(self.set_view2)
        self.empty=QtWidgets.QWidget()
    def farmcalc_view(self,key):
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
    @QtCore.pyqtSlot()
    def set_view(self):
        args_raw=self.ui_args.args()
        ks=['server','minimize_stage_key','lang']
        key = tuple(args_raw.get(k) for k in ks)
        args={k:v for k,v in args_raw.items() if k in ks}
        if key in self.views:
            view=self.views[key]
            self.real_set_view(view)
        else:
            self.signal_init.emit(key,args|{'update':False})
    @QtCore.pyqtSlot(tuple)
    def set_view2(self,key):
        view=self.farmcalc_view(key)
        self.views[key]=view
        self.real_set_view(view)
    @QtCore.pyqtSlot()
    def real_set_view(self,view):
        if self.view!=view:
            if self.vlayout.count()==2:
                v = self.vlayout.itemAt(1).widget()
                self.vlayout.removeWidget(v)
                v.setParent(None)
            self.vlayout.addWidget(view)
    @QtCore.pyqtSlot(str)
    def UiItemImg_n(self,text):
        UiItemImg.n=text
        self.set_view()
        if self.view:
            self.view.update_ysd()
    def save_pos(self):
        for view in self.views.values():
            view.save_pos()
        self.ui_args.save_pos()
    def load_pos(self):
        for view in self.views.values():
            view.load_pos()
        self.ui_args.load_pos()
    def close_worker(self):
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()

class UiStageSelect(QtWidgets.QDialog):
    def __init__(self):
        super(UiStageSelect, self).__init__()
        layout=MyVBoxLayout()
        scroll = QtWidgets.QScrollArea(self)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(True)
        widget = QtWidgets.QWidget()
        self.layout = MyGridLayout()
        self.setLayout(layout)
        layout.addWidget(scroll)
        scroll.setWidget(widget)
        widget.setLayout(self.layout)
        stagebyzone={}
        for stage in farmcalc.Data.stages.values():
            stagebyzone.setdefault(stage.zoneId,[]).append(stage)
        row=-1
        for zoneId,stages in stagebyzone.items():
            check_all = QtWidgets.QCheckBox(zoneId)
            row+=1
            self.layout.addWidget(check_all,row,0)
            col=1
            for stage in stages:
                check = QtWidgets.QCheckBox(stage.code)
                self.layout.addWidget(check,row,col)
                col+=1

class UiArgs(QtWidgets.QWidget):
    def __init__(self):
        super(UiArgs, self).__init__()
        self.config='./config/UiArgs.json'
        os.makedirs(os.path.dirname(self.config), exist_ok=True)
        self.widget_layout = MyHBoxLayout()
        self.setLayout(self.widget_layout)
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
        # self.btn_stages=QtWidgets.QPushButton('Stages')
        # self.btn_stages.clicked.connect(self.open_stages)
        # self.widget_layout.addWidget(self.btn_stages)
        self.widget_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
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

def img_data2file(img_data):
    for name in img_data:
        url = farmcalc.Data.url_material + name
        yield anhrtags.GData.img(name,url)

class UiItemImg(QtWidgets.QGraphicsItem):
    n=3
    len=80
    len1=66
    wordlen=11
    def __init__(self, item, parent=None):
        super(UiItemImg, self).__init__(parent)
        self.x=0
        self.y=0
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.item = item
        self.beststages = [([stage.code for stage in stages],san) for stages,san in self.item.beststage]
        self.strs = []
        for idx,(stages,san) in enumerate(self.beststages):
            s=f"""[{', '.join(stages)}] {round(san,1):g}"""
            if s not in self.strs:
                self.strs.append(s)
        self.pixmaps = []
        file,file1 = img_data2file(item.img_data)
        self.pixmaps.append(QtGui.QPixmap(file).scaled(UiItemImg.len,UiItemImg.len,aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio,transformMode=QtCore.Qt.TransformationMode.SmoothTransformation))
        self.pixmaps.append(QtGui.QPixmap(file1).scaled(UiItemImg.len1,UiItemImg.len1,aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio,transformMode=QtCore.Qt.TransformationMode.SmoothTransformation))
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
        return QtCore.QRectF(0,0,UiItemImg.len,UiItemImg.len)

class UiGraphicsView(QtWidgets.QGraphicsView):
    xsd=10
    ysd=UiItemImg.len+UiItemImg.wordlen*(1+UiItemImg.n)
    def __init__(self,key):
        super(UiGraphicsView, self).__init__()
        self.key=' '.join(key)
        self.scene = QtWidgets.QGraphicsScene()
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
        minx=min([x for itemId,(x,y) in d.items()]+[0])
        miny=min([y for itemId,(x,y) in d.items()]+[0])
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

class UiFormulaArrow(QtWidgets.QGraphicsItem):
    def __init__(self, startItem, endItem,color, parent=None, scene=None):
        super(UiFormulaArrow, self).__init__()
        self.startItem = startItem
        self.endItem = endItem
        self.color=color
    def boundingRect(self):
        p1 = self.startItem.pos() + self.startItem.boundingRect().center()
        p3 = self.endItem.pos() + self.endItem.boundingRect().center()
        bounds = p3 - p1
        size = QtCore.QSizeF(abs(bounds.x()), abs(bounds.y()))
        return QtCore.QRectF(p1, size)
    def paint(self, painter, option, widget=None):
        p1 = self.startItem.pos() + self.startItem.boundingRect().center()
        p3 = self.endItem.pos() + self.endItem.boundingRect().center()
        pen = QtGui.QPen()
        # pen.setWidth(1)
        # painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # if self.isSelected():
        # pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        # else:
        # pen.setStyle(QtCore.Qt.PenStyle.SolidLine)
        pen.setColor(QtGui.QColor(self.color)) #https://doc.qt.io/qtforpython-5/PySide2/QtGui/QColorConstants.html
        painter.setPen(pen)
        painter.drawLine(QtCore.QLineF(p1, p3))
        # painter.setBrush(QtGui.QBrush(QtCore.Qt.GlobalColor.white))

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

def main():
    app = QtWidgets.QApplication([])
    root = UiRoot()
    root.show()
    ret = app.exec()
    exit(ret)

if __name__ == '__main__':
    main()


import os

from PyQt6 import QtWidgets, QtGui, QtCore

from qtlayout import MyGridLayout,MyVBoxLayout,MyHBoxLayout
from farmcalc import FarmCalc
import resource
try:
    import saveobj
except:
    import mods.saveobj

app_path = os.path.dirname(__file__)
os.chdir(app_path)
UiGraphicsView_default_d = {
        "30064": [
            7,
            1
        ],
        "31063": [
            125,
            3
        ],
        "31013": [
            72,
            4
        ],
        "31044": [
            115,
            1
        ],
        "30042": [
            43,
            4
        ],
        "30052": [
            26,
            4
        ],
        "31084": [
            138,
            2
        ],
        "30063": [
            15,
            3
        ],
        "30044": [
            48,
            1
        ],
        "30054": [
            34,
            1
        ],
        "30014": [
            61,
            1
        ],
        "30051": [
            26,
            5
        ],
        "30125": [
            7,
            0
        ],
        "31053": [
            135,
            3
        ],
        "30033": [
            34,
            3
        ],
        "31064": [
            131,
            1
        ],
        "30115": [
            32,
            0
        ],
        "30073": [
            70,
            3
        ],
        "31033": [
            85,
            4
        ],
        "30031": [
            35,
            5
        ],
        "31083": [
            123,
            4
        ],
        "30024": [
            39,
            2
        ],
        "30012": [
            52,
            4
        ],
        "30084": [
            86,
            1
        ],
        "30013": [
            52,
            3
        ],
        "30145": [
            92,
            0
        ],
        "31073": [
            112,
            4
        ],
        "31014": [
            67,
            2
        ],
        "30043": [
            43,
            3
        ],
        "30061": [
            16,
            5
        ],
        "30103": [
            61,
            3
        ],
        "30074": [
            20,
            1
        ],
        "31074": [
            112,
            2
        ],
        "30032": [
            35,
            4
        ],
        "30021": [
            7,
            5
        ],
        "31024": [
            98,
            2
        ],
        "30093": [
            99,
            3
        ],
        "31043": [
            112,
            3
        ],
        "31023": [
            78,
            3
        ],
        "30022": [
            7,
            4
        ],
        "30062": [
            16,
            4
        ],
        "30041": [
            43,
            5
        ],
        "30083": [
            89,
            3
        ],
        "30104": [
            73,
            1
        ],
        "30094": [
            100,
            1
        ],
        "31034": [
            81,
            2
        ],
        "31054": [
            124,
            2
        ],
        "30135": [
            60,
            0
        ],
        "30155": [
            117,
            0
        ],
        "30023": [
            7,
            3
        ],
        "30034": [
            17,
            2
        ],
        "30011": [
            52,
            5
        ],
        "30053": [
            26,
            3
        ]
    }

class UiFarmStageWorker(QtCore.QObject):
    init_farmstage3 = QtCore.pyqtSignal(tuple,FarmCalc)
    def __init__(self,parent=None):
        super().__init__(parent)
    @QtCore.pyqtSlot(tuple,dict)
    def init_farmstage2(self,key,args):
        data=FarmCalc(**args)
        self.init_farmstage3.emit(key,data)

class UiFarmStage(QtWidgets.QWidget):
    init_farmstage1 = QtCore.pyqtSignal(tuple,dict)
    def __init__(self,args,parent=None):
        super().__init__(parent)
        self.views={}
        self.view=None
        self.create_worker()
        self.vlayout = MyVBoxLayout()
        UiGraphicsView.init_ysd(args.get('show'))
        self.set_view(args)
        self.setLayout(self.vlayout)
    def create_worker(self):
        self.qobj_worker = UiFarmStageWorker()
        self.worker_thread = QtCore.QThread()
        self.qobj_worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.init_farmstage1.connect(self.qobj_worker.init_farmstage2)
        self.qobj_worker.init_farmstage3.connect(self.init_farmstage4)
        # self.empty=QtWidgets.QWidget()
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
        view=self.farmcalc_view(key,data)
        self.views[key]=view
        self.real_set_view(view)
    def getcolor(self):
        colorid={}
        colorid2={}
        for formulaId,formula in self.data.formulas.items():
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
    def farmcalc_view(self,key,data):
        view= UiGraphicsView(key)
        imgitems={}
        itemids = set(data.result.keys())
        for formulaId,formula in data.formulas.items():
            for item in formula.ins:
                for item_out in formula.out:
                    itemids.add(item.item.id)
                    itemids.add(item_out.item.id)
        for itemId in itemids:
            item = data.items.get(itemId)
            if resource.ItemImg.img(item.id):
                imgitem = UiItemImg(item)
                imgitems[item.id]=imgitem
        arrowcolor = self.getcolor()
        for formulaId,formula in data.formulas.items():
            for item in formula.ins:
                for item_out in formula.out:
                    imgitem = imgitems.get(item.item.id)
                    imgitem1 = imgitems.get(item_out.item.id)
                    n=item.n/item_out.n
                    if imgitem and imgitem1:
                        arrow=UiFormulaArrow(imgitem,imgitem1,arrowcolor[formula.id],n)
                        imgitem1.onselected.connect(arrow.changepenwidth)
                        view.addarrow(arrow)
        for imgitem in imgitems.values():
            view.addimg(imgitem)
        view.load_pos()
        return view
    @QtCore.pyqtSlot()
    def real_set_view(self,view):
        if self.view!=view:
            if self.vlayout.count()==1:
                v = self.vlayout.itemAt(0).widget()
                self.vlayout.removeWidget(v)
                v.setParent(None)
            self.vlayout.addWidget(view)
            self.view=view
    @QtCore.pyqtSlot(str)
    def UiItemImg_n(self,text):
        UiItemImg.n=text
        if self.view:
            self.view.update_ysd()
    def close_worker(self):
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
    def closeEvent(self,event):
        self.close_worker()
        for view in self.views.values():
            view.close()

# class UiStageSelect(QtWidgets.QDialog):
    # def __init__(self,parent=None):
        # super().__init__(parent)
        # layout=MyVBoxLayout()
        # scroll = QtWidgets.QScrollArea(self)
        # scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # scroll.setWidgetResizable(True)
        # widget = QtWidgets.QWidget()
        # self.layout = MyGridLayout()
        # self.setLayout(layout)
        # layout.addWidget(scroll)
        # scroll.setWidget(widget)
        # widget.setLayout(self.layout)
        # stagebyzone={}
        # for stage in farmcalc.Data.stages.values():
            # stagebyzone.setdefault(stage.zoneId,[]).append(stage)
        # row=-1
        # for zoneId,stages in stagebyzone.items():
            # check_all = QtWidgets.QCheckBox(zoneId)
            # row+=1
            # self.layout.addWidget(check_all,row,0)
            # col=1
            # for stage in stages:
                # check = QtWidgets.QCheckBox(stage.code)
                # self.layout.addWidget(check,row,col)
                # col+=1

class UiItemImg1(QtWidgets.QGraphicsItem):
    n=3
    len=80
    len1=66
    wordlen=11
    def __init__(self, item,parent=None):
        super().__init__(parent)
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
        file,file1 = resource.ItemImg1.img(item.id)
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

class UiItemImg(QtWidgets.QGraphicsObject):
    n=3
    len=80
    len1=66
    wordlen=11
    onselected = QtCore.pyqtSignal(bool)
    def __init__(self, item,parent=None):
        super().__init__(parent)
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
        file = resource.ItemImg.img(item.id)
        self.pixmap = QtGui.QPixmap(file).scaled(UiItemImg.len,UiItemImg.len,aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio,transformMode=QtCore.Qt.TransformationMode.SmoothTransformation)
    def paint(self, painter, option, widget):
        x=int((UiItemImg.len-UiItemImg.len1)/2)
        painter.drawPixmap(0,0,self.pixmap)
        painter.drawText(0,UiItemImg.len+UiItemImg.wordlen,self.item.name)
        for idx,s in enumerate(self.strs):
            if idx>=int(UiItemImg.n):
                if not self.isSelected():
                    break
            painter.drawText(0,UiItemImg.len+UiItemImg.wordlen*(2+idx),s)
    def boundingRect(self):
        return QtCore.QRectF(0,0,UiItemImg.len,UiItemImg.len)
    def itemChange(self,change,value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # print('selection emission',value)
            if value: # 1 select
                self.onselected.emit(True)
            else: #0 deselect
                self.onselected.emit(False)
        return super().itemChange(change,value)

class UiGraphicsView(QtWidgets.QGraphicsView):
    xsd=10
    ysd=UiItemImg.len+UiItemImg.wordlen*(1+UiItemImg.n)
    def __init__(self,key,parent=None):
        super().__init__(parent)
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
    def init_ysd(n):
        UiItemImg.n=int(n)
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
            d = UiGraphicsView_default_d
        if d:
            for img in self.imgs:
                if (p:=d.get(img.item.id)):
                    x,y=p
                    img.setPos(x*UiGraphicsView.xsd,y*UiGraphicsView.ysd)
                    img.x=x
                    img.y=y
    def closeEvent(self,event):
        self.save_pos()

class UiFormulaArrow(QtWidgets.QGraphicsObject): # QGraphicsObject Inherits: QObject QGraphicsItem
    def __init__(self, startItem, endItem,color,n,parent=None):
        super().__init__(parent)
        self.startItem = startItem
        self.endItem = endItem
        self.color=color
        self.n=n
        self.pen=QtGui.QPen()
        self.pen.setWidth(1)
        self.pen.setColor(QtGui.QColor(self.color)) #https://doc.qt.io/qtforpython-5/PySide2/QtGui/QColorConstants.html
        self.fontsize=1
    def boundingRect(self):
        p1 = self.startItem.pos() + self.startItem.boundingRect().center()
        p3 = self.endItem.pos() + self.endItem.boundingRect().center()
        bounds = p3 - p1
        size = QtCore.QSizeF(abs(bounds.x()), abs(bounds.y()))
        return QtCore.QRectF(p1, size)
    def paint(self, painter, option, widget=None):
        p1 = self.startItem.pos() + self.startItem.boundingRect().center()
        p3 = self.endItem.pos() + self.endItem.boundingRect().center()
        painter.setPen(self.pen)
        font = painter.font()
        font.setPointSize(int(font.pointSize() * self.fontsize))
        painter.setFont(font)
        painter.drawLine(QtCore.QLineF(p1, p3))
        painter.drawText((p1+p3)/2,f'{self.n:g}')
    @QtCore.pyqtSlot(bool)
    def changepenwidth(self,selected):
        if selected:
            self.pen.setWidth(5)
            self.fontsize=2.2
        else:
            self.pen.setWidth(1)
            self.fontsize=1

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    root = QtWidgets.QMainWindow()
    root.setWindowTitle(f"best stages")
    ui=UiFarmStage({'server':'US','minimize_stage_key':'san','lang':'en','show':'1'})
    root.setCentralWidget(ui)
    root.show()
    ret = app.exec()
    exit(ret)


import os

from PyQt6 import QtWidgets, QtGui, QtCore

from qtlayout import MyGridLayout,MyVBoxLayout,MyHBoxLayout
from farmcalc import FarmCalc
import anhrtags
try:
    import saveobj
except:
    import mods.saveobj

app_path = os.path.dirname(__file__)
os.chdir(app_path)

class UiFarmStageWorker(QtCore.QObject):
    init_farmstage3 = QtCore.pyqtSignal(tuple,FarmCalc)
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
    @QtCore.pyqtSlot(tuple,dict)
    def init_farmstage2(self,key,args):
        data=FarmCalc(**args)
        self.init_farmstage3.emit(key,data)

class UiFarmStage(QtWidgets.QWidget):
    init_farmstage1 = QtCore.pyqtSignal(tuple,dict)
    def __init__(self,args):
        super(UiFarmStage, self).__init__()
        self.views={}
        self.view=None
        self.create_worker()
        self.vlayout = MyVBoxLayout()
        UiGraphicsView.init_ysd()
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
        for itemId,item in data.items.items():
            if item.img_data:
                imgitem = UiItemImg(item)
                imgitems[item.id]=imgitem
        arrowcolor = self.getcolor()
        for formulaId,formula in data.formulas.items():
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

def img_data2file(img_data):
    for name in img_data:
        url = FarmCalc.url_material + name
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
    def closeEvent(self,event):
        self.save_pos()

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
        pen.setColor(QtGui.QColor(self.color)) #https://doc.qt.io/qtforpython-5/PySide2/QtGui/QColorConstants.html
        painter.setPen(pen)
        painter.drawLine(QtCore.QLineF(p1, p3))

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    root = QtWidgets.QMainWindow()
    root.setWindowTitle(f"best stages")
    ui=UiFarmStage({'server':'US','minimize_stage_key':'san','lang':'en'})
    root.setCentralWidget(ui)
    root.show()
    ret = app.exec()
    exit(ret)

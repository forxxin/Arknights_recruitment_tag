
import os
import re

from PyQt6 import QtWidgets, QtGui, QtCore

from qtlayout import MyGridLayout,MyVBoxLayout,MyHBoxLayout
from char import Chars
from ocrtag import win_tag,adb_tag,adb_kill

app_path = os.path.dirname(__file__)
os.chdir(app_path)

class UiTag(QtWidgets.QLabel):
    def __init__(self,data,tag):
        super(UiTag, self).__init__()
        self.data=data
        self.setText(tag)
        color = self.data.rarity_color.get(self.data.tag_rarity.get(tag))
        self.setStyleSheet(f"QLabel{{background-color:{color};color:black;}}")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

class UiChar(QtWidgets.QLabel):
    def __init__(self,data,char):
        super(UiChar, self).__init__()
        self.data=data
        self.setText(char.name)
        color = self.data.rarity_color.get(char.rarity)
        self.setStyleSheet(f"QLabel{{background-color:{color};color:black;}}")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)
        
class UiTagset(QtWidgets.QWidget):
    def __init__(self,data,tagset):
        super(UiTagset, self).__init__()
        self.data=data
        hlayout = MyHBoxLayout()
        self.setLayout(hlayout)
        for tag in tagset:
            hlayout.addWidget(UiTag(self.data,tag))
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

class UiResultSub(QtWidgets.QWidget):
    def __init__(self,data,result):
        super(UiResultSub, self).__init__()
        self.data=data
        vlayout = MyVBoxLayout()
        self.setLayout(vlayout)
        idx=0
        hlayout = None
        for rarity,chars in result.items():
            if isinstance(rarity,int):
                for char in chars:
                    if idx%10==0:
                        if hlayout:
                            hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
                        hlayout = MyHBoxLayout()
                        vlayout.addLayout(hlayout)
                    hlayout.addWidget(UiChar(self.data,char))
                    idx+=1
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

class UiResult(QtWidgets.QWidget):
    def __init__(self,data,tags):
        super(UiResult, self).__init__()
        self.data=data
        if not tags:
            vlayout = MyVBoxLayout()
            self.setLayout(vlayout)
            vlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
            return
        res = self.data.recruit(tags)
        print(id(self.data.tags_result))
        layout = MyGridLayout()
        self.setLayout(layout)
        scroll = QtWidgets.QScrollArea(self)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        # vlayout = MyVBoxLayout()
        # hlayout = MyHBoxLayout()
        # glayout = MyGridLayout()
        vlayout = MyVBoxLayout()
        hlayout = MyHBoxLayout()
        glayout = MyGridLayout()
        hlayout.addLayout(glayout)
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        widget = QtWidgets.QWidget()
        scroll.setWidget(widget)
        vlayout.addLayout(hlayout)
        vlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        widget.setLayout(vlayout)
        for row,(tagset,result) in enumerate(res.items()):
            label_rarity = QtWidgets.QLabel(' ')
            label_rarity.setStyleSheet(f"QLabel{{background-color:{self.data.rarity_color.get(result.get('rarity'))};color:black;}}")
            glayout.addWidget(UiTagset(self.data,tagset),row,0)
            glayout.addWidget(label_rarity,row,1)
            glayout.addWidget(UiResultSub(self.data,result),row,2)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

class UiTagSelect(QtWidgets.QPushButton):
    def __init__(self,data,tag):
        super(UiTagSelect, self).__init__()
        self.data=data
        self.data.tag_rarity.get(tag)
        self.setText(tag)
        self.setCheckable(True)
        self.setStyleSheet(f'QPushButton{{background-color:{self.data.rarity_color.get(self.data.tag_rarity.get(tag))};color:black;}}')
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,QtWidgets.QSizePolicy.Policy.Preferred)
        # self.resize(self.sizeHint().width(), self.sizeHint().height())

class UiTagsSelect(QtWidgets.QWidget):
    def __init__(self,data):
        super(UiTagsSelect, self).__init__()
        self.data=data
        self.alltag=[x for xs in self.data.all_tags for x in xs]
        vlayout = MyVBoxLayout()
        self.taginput=QtWidgets.QLineEdit()
        self.taginput.returnPressed.connect(self.addtag)
        self.taginput_result=QtWidgets.QLabel()
        vlayout.addWidget(self.taginput)
        vlayout.addWidget(self.taginput_result)
        self.setLayout(vlayout)
        self.uitags={}
        hlayout=None
        for row,tag_sub in enumerate(self.data.all_tags):
            for idx,tag in enumerate(tag_sub):
                if idx%9==0:
                    if hlayout:
                        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
                    hlayout = MyHBoxLayout()
                    vlayout.addLayout(hlayout)
                uitag=UiTagSelect(self.data,tag)
                self.uitags[tag]=uitag
                hlayout.addWidget(uitag)
            hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)
        hlayout = MyHBoxLayout()
        vlayout.addLayout(hlayout)
        def create_btn(text,func=None):
            button = QtWidgets.QPushButton(text)
            hlayout.addWidget(button)
            if func:
                button.clicked.connect(func)
            return button
        self.button_ok = create_btn('Ok')
        self.button_clear = create_btn('Clear',self.clear)
        self.button_ocrwin = create_btn('OCR-win')
        self.button_ocradb = create_btn('OCR-adb')
        self.button_adbkill = create_btn('adb kill-server')
        self.line_tag=QtWidgets.QLineEdit()
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        hlayout = MyHBoxLayout()
        vlayout.addLayout(hlayout)
        hlayout.addWidget(self.line_tag)
        self.line_tag.setReadOnly(True)
        for tag,uitag in self.uitags.items():
            uitag.toggled.connect(self.ok)
        self.real_ok=None
        self.is_update_tag=False
        self.button_ok.hide()
    @QtCore.pyqtSlot()
    def addtag(self):
        text=self.taginput.text().lower()
        def set_tag(tags):
            if len(tags)==1:
                tag=tags[0]
                self.uitags.get(tag).setChecked(True)
                self.taginput_result.setText(f"'{tag}' added")
                self.taginput.setText('')
            else:
                self.taginput_result.setText(f'{tags}'[:140])
        if text:
            tags_m=[]
            tags_in=[]
            tags_split=[]
            for tag in self.alltag:
                tag_lower=tag.lower()
                if text==tag_lower:
                    return set_tag([tag])
                if re.match(f'^{text}',tag_lower):
                    tags_m.append(tag)
                if text in tag_lower:
                    tags_in.append(tag)
                if all([t in tag_lower for t in text.split()]):
                    tags_split.append(tag)
            if len(tags_m)==1:    return set_tag(tags_m)
            if len(tags_in)==1:   return set_tag(tags_in)
            if len(tags_split)==1:return set_tag(tags_split)
            if len(tags_m)>1:     return set_tag(tags_m)
            if len(tags_in)>1:    return set_tag(tags_in)
            if len(tags_split)>1: return set_tag(tags_split)
    def ok(self):
        if self.real_ok and not self.is_update_tag:
            self.real_ok()
    def clear(self):
        self.select([])
        self.button_ok.clicked.emit()
        self.taginput.setFocus()
    def select(self,tags):
        self.is_update_tag = True
        for tag,uitag in self.uitags.items():
            if tag in tags:
                uitag.setChecked(True)
            else:
                uitag.setChecked(False)
        self.is_update_tag = False
    def tagset(self):
        tags = [tag for tag,uitag in self.uitags.items() if uitag.isChecked()]
        self.line_tag.setText(str(tags))
        return frozenset(tags)

class UiRecTagWorker(QtCore.QObject):
    send_tags = QtCore.pyqtSignal(list)
    def __init__(self,alltag, parent=None):
        super(self.__class__, self).__init__(parent)
        self.img_anhrtags = './tmp/tmp_anhrtags.png'
        self.alltag=alltag
    @QtCore.pyqtSlot()
    def ocr_win(self):
        tags=win_tag(self.alltag,self.img_anhrtags)
        # self.ui_tags.select(tags)
        # self.set_view()
        self.send_tags.emit(tags)
    @QtCore.pyqtSlot()
    def ocr_adb(self):
        tags=adb_tag(self.alltag,self.img_anhrtags)
        # self.ui_tags.select(tags)
        # self.set_view()
        self.send_tags.emit(tags)
    @QtCore.pyqtSlot()
    def adb_kill_server(self):
        adb_kill()

class UiRecTag(QtWidgets.QMainWindow):
    signal_ocr_win = QtCore.pyqtSignal()
    signal_ocr_adb = QtCore.pyqtSignal()
    signal_adb_kill_server = QtCore.pyqtSignal(list)
    def __init__(self,args):
        super(UiRecTag,self).__init__()
        self.data=Chars(args.get('server'),args.get('lang'))
        alltag=[x for xs in self.data.all_tags for x in xs]
        self.setWindowTitle(f"Arknights Tags")
        widget = QtWidgets.QWidget(self)
        self.layout = MyVBoxLayout()
        vlayout = MyVBoxLayout()
        self.setCentralWidget(widget)
        widget.setLayout(vlayout)
        vlayout.addLayout(self.layout)
        self.view=None
        self.ui_tags = UiTagsSelect(self.data)
        self.add(self.ui_tags)
        self.ui_tags.select(['Vanguard', 'Crowd-Control', 'DP-Recovery', 'Debuff', 'Healing'])
        self.views={}
        self.create_worker(alltag)
        self.ui_tags.real_ok=self.set_view
        self.set_view()
        self.ui_tags.button_ok.clicked.connect(self.set_view)
        self.ui_tags.button_ocrwin.clicked.connect(self.ocr_win)
        self.ui_tags.button_ocradb.clicked.connect(self.ocr_adb)
        self.ui_tags.button_adbkill.clicked.connect(self.qobj_worker.adb_kill_server)
        self.signal_ocr_win.connect(self.qobj_worker.ocr_win)
        self.signal_ocr_adb.connect(self.qobj_worker.ocr_adb)
    def create_worker(self,alltag):
        self.qobj_worker = UiRecTagWorker(alltag)
        self.worker_thread = QtCore.QThread()
        self.qobj_worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.qobj_worker.send_tags.connect(self.update_tags)
    @QtCore.pyqtSlot()
    def ocr_win(self):
        self.update_tags([])
        self.signal_ocr_win.emit()
        self.ui_tags.button_ocrwin.setEnabled(False)
    @QtCore.pyqtSlot()
    def ocr_adb(self):
        self.update_tags([])
        self.signal_ocr_adb.emit()
        self.ui_tags.button_ocradb.setEnabled(False)
    @QtCore.pyqtSlot(list)
    def update_tags(self,tags):
        self.ui_tags.select(tags)
        self.set_view()
        self.ui_tags.button_ocrwin.setEnabled(True)
        self.ui_tags.button_ocradb.setEnabled(True)
    @QtCore.pyqtSlot()
    def set_view(self):
        tagset = self.ui_tags.tagset()
        if tagset in self.views:
            view=self.views[tagset]
        else:
            view=UiResult(self.data,tagset)
            self.views[tagset]=view
        if self.view!=view:
            if self.layout.count()==2:
                v = self.layout.itemAt(1).widget()
                self.layout.removeWidget(v)
                v.setParent(None)
            self.layout.addWidget(view)
        return view
    def add(self,children):
        if isinstance(children,list):
            for child in children:
                self.layout.addWidget(child)
        else:
            self.layout.addWidget(children)
    def close_worker(self):
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
    def closeEvent(self,event):
        self.close_worker()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    root = UiRecTag({'server':'US','lang':'en'})
    root.show()
    ret = app.exec()
    exit(ret)

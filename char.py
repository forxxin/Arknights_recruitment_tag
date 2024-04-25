from dataclasses import dataclass
from itertools import combinations
import json
import pprint
import os
import re

app_path = os.path.dirname(__file__)
os.chdir(app_path)
try:
    import pandas as pd
    from PyQt6 import QtWidgets, QtGui, QtCore
    import cv2 as cv
    import numpy as np
    import pytesseract
    import win32gui
    import win32ui
    pytesseract.pytesseract.tesseract_cmd = os.path.abspath(r'../../Tesseract-OCR/tesseract.exe')
except Exception as e:
    print(e)

import anhrtags
from anhrtags import GData,TimeCost

try:
    from test import dump
except:
    def dump(**a):
        pass

try:
    import mods.shellcmd1 as shellcmd
except:
    import shellcmd1 as shellcmd

###

def windows_image(img_anhrtags,queue,app_title='Arknights',border=False,scaled=True):
    from ctypes import windll
    from PIL import Image
    try:
        tc=TimeCost()
        def remove_img(img_anhrtags):
            if os.path.isfile(img_anhrtags):
                os.remove(img_anhrtags)
        remove_img(img_anhrtags)
        hwnd = win32gui.FindWindow(None, app_title)
        if scaled:
            # if use a high DPI display or >100% scaling size
            SetProcessDPIAware=windll.user32.SetProcessDPIAware()
        if border:
            left, top, right, bot = win32gui.GetWindowRect(hwnd)
        else:
            left, top, right, bot = win32gui.GetClientRect(hwnd)
        w = right - left
        h = bot - top
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)
        if border:
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        else:
            result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        if result == 1:
            tc.end('in windows_image')
            # img.save(img_anhrtags)
            queue.put(img)
        else:
            queue.put(None)
    except Exception as e:
        print(e)
        queue.put(None)

def resize(image, width=None, height=None):
    dim = None
    (h, w) = image.shape[:2]
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    return cv.resize(image, dim, interpolation=cv.INTER_AREA)


class roi_data():
    os.makedirs('./config/', exist_ok=True)
    file='./config/roi.json'
    @staticmethod
    def load():
        if not os.path.isfile(roi_data.file):
            with open(roi_data.file, "a", encoding="utf-8"):
                pass
        with open(roi_data.file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    @staticmethod
    def save(data):
        with open(roi_data.file, "w", encoding="utf-8") as f:
            json.dump(data,f)

def win_tag(img_anhrtags, setup=False):
    from multiprocessing import Process,Queue
    tc=TimeCost()
    tc1=TimeCost()
    queue = Queue()
    p = Process(target=windows_image, args=(img_anhrtags,queue))
    p.start()
    img=queue.get()
    tc.end('windows_image')
    ret = list(img_tag(img_anhrtags,setup=setup,img=img))
    tc.end('img_tag')
    p.join()
    tc1.end('win_tag')
    return ret

def img_tag(img_anhrtags,setup=False,img=None):
    if img==None:
        if not os.path.isfile(img_anhrtags):
            return iter(())
        img = cv.imread(img_anhrtags,cv.IMREAD_GRAYSCALE)
    else:
        from PIL import Image
        if isinstance(img,Image.Image):
            img = cv.cvtColor(np.array(img), cv.COLOR_RGB2GRAY)
    img=resize(img,width=1000)
    height=int(img.shape[0])
    height_key=str(height)
    print(f'\nimg_tag:\n{height=}')
    roidata=roi_data().load()
    if setup or (height_key not in roidata) or (height_key in roidata and height<1000 and not roidata[height_key]):
        ROIs=[]
        tags=[]
        for tag,x,y,w,h in _img_tag(img,setup=setup):
            ROIs.append([x,y,w,h])
            tags.append(tag)
        if len(ROIs)>=5:
            roidata[height_key]=ROIs
            roi_data().save(roidata)
        yield from tags
    else:
        ROIs=roidata[height_key]
        tags=[]
        for x,y,w,h in ROIs:
            for tag in ocr_img(img,x,y,w,h):
                if tag not in tags:
                    tags.append(tag)
                    yield tag

def _img_tag(img,setup=False):
    # cv.imwrite(f"anhrtags_1000.png",img)
    height=int(img.shape[0])
    print(f'\n_img_tag :\n{height=}')
    th = cv.inRange(img, 49, 49)
    th1 = cv.inRange(img, 114, 114)
    th2 = cv.inRange(img, 141, 141)
    th = cv.bitwise_or(th, th1)
    th = cv.bitwise_or(th, th2)
    contours, hier = cv.findContours(th, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    contours_list = [(contour,cv.boundingRect(contour)) for contour in contours if cv.contourArea(contour)>1000]
    # cv.imshow('img',th)
    # cv.waitKey(0)
    # cv.destroyAllWindows()
    print()
    tags=[]
    for contour,(x,y,w,h) in sorted(contours_list, key=lambda i:i[1][1],reverse=True):
        if len(tags)>=5:
            return
        # if w in range(98-1,111+2) and h in range(30-1,35+2):
        x+=1
        y+=1
        w-=2
        h-=2
        print(x,y,w,h,end=' ')
        for tag in ocr_img(img,x,y,w,h):
            if tag not in tags:
                tags.append(tag)
                yield tag,x,y,w,h

def ocr_img(img,x,y,w,h):
    img_crop=img[y:y+h,x:x+w]
    tag_ocrs = pytesseract.image_to_string(img_crop, config='''D:/CS/PythonCodes/Arknights/tessdata/bazaar''')
    tag_ocrs = re.sub(r'[^\w-]', ' ', tag_ocrs).replace('OPS','DPS').replace('bps','DPS')
    alltag=[x for xs in Data.all_tags for x in xs]
    taglow_tag = {tag.lower():tag for tag in sorted(alltag, key=len, reverse=True)}
    print(tag_ocrs.strip())
    for tag_ocr in tag_ocrs.lower().split():
        for taglow,tag in taglow_tag.items():
            if taglow in tag_ocr:
                yield tag
                break

def adb_tag(img_anhrtags,setup=False):
    def _adb_tag(adev_name=''):
        try:
            adev = shellcmd.AndroidDev(adev_name, adb_tcpip=False) # adb wireless
        except Exception as e:
            print('adb_tag',e)
            adev=None
        if isinstance(adev,shellcmd.AndroidDev):
            img = adev.screencap(name1=img_anhrtags,open_img=False)
            if img:
                return list(img_tag(img,setup=setup))
    tags = _adb_tag()
    if tags:
        return tags
    mdns = shellcmd.AndroidDev.adb_mdns(retry=2)
    pprint.pprint(['mdns',mdns])
    adev_name=None
    for device,info in mdns.items():
        adev_name = info['device_ip']
        if adev_name:
            tags = _adb_tag(adev_name)
            if tags:
                return tags
    return []

def adb_kill():
    shellcmd.AndroidDev.adb_kill()


###

class Data:
    server='US'
    lang='en'
    lang2={'en':'en_US','ja':'ja_JP','ko':'ko_KR','zh':'zh_CN','ch':'zh_TW',}
    rarity_color={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }
    itemObtainApproach_recruit='Recruitment & Headhunting'
    chars={}
    tag_rarity={}
    tags_result={}
    all_tags=[]
    url_agr = 'https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/'
    name_avatar = 'avatar/{charid}.png'
    name_avatar2 = 'avatar/{charid}_2.png'
    name_portrait = 'portrait/{charid}_1.png'
    name_portrait2 = 'portrait/{charid}_2.png'

    position_tagId = {
            "RANGED": 10,
            "MELEE": 9,
    }
    profession_tagId = {
            "WARRIOR": 1,
            "SNIPER": 2,
            "TANK": 3,
            "MEDIC": 4,
            "SUPPORT": 5,
            "CASTER": 6,
            "SPECIAL": 7,
            "PIONEER": 8,
    }

@dataclass
class Character:
    characterId:str
    name:str
    profession:str
    subProfessionId:str
    position:str
    tags:frozenset
    rarity:int
    avatar:str
    # avatar2:str
    # portrait:str
    # portrait2:str
    itemObtainApproach:str
    recruitable:bool
    # description:str
    # potentialItemId:str
    # nationId:str
    # displayNumber:str
    # appellation:str
    # itemUsage:str
    # itemDesc:str
    # groupId:str
    # teamId:str
    # classicPotentialItemId:str
    # activityPotentialItemId:str
    # canUseGeneralPotentialItem:bool
    # canUseActivityPotentialItem:bool
    # isNotObtainable:bool
    # isSpChar:bool
    # canUseGeneralPotentialItem:int
    # canUseActivityPotentialItem:int
    # isNotObtainable:int
    # isSpChar:int
    # maxPotentialLevel:int
    # phases:list
    # skills:list
    # talents:list
    # potentialRanks:list
    # favorKeyFrames:list
    # allSkillLvlup:list
    # trait:dict
    # displayTokenDict:dict
    def __repr__(self):
        s=f'Character({self.name})'
        return s
    def __str__(self):
        s=f'{self.name}'
        return s

def subset(items,maxtag=5,self=0):
    for i in range(1,min(maxtag+1,len(items)+self)):
        for s in combinations(items, i):
            yield frozenset(s)

def prep_chars():
    Data.chars={}
    lang2=Data.lang2.get(Data.lang)
    character_table = GData.json_table('character', lang=lang2)  # 'zh_CN'
    gacha_table = GData.json_table('gacha', lang=lang2)  # 'zh_CN'
    tagsid_name = {tag.get('tagId'):tag.get('tagName') for tag in gacha_table.get('gachaTags')}
    tag_profession = set()
    tag_position = set()
    tag_tagList = set()
    def gen_tags(char_data):
        tags=char_data.get('tagList') or []
        profession=char_data.get('profession')
        position=char_data.get('position')
        profession_name=tagsid_name.get(Data.profession_tagId.get(profession))
        position_name=tagsid_name.get(Data.position_tagId.get(position))
        if recruitable(char_id):
            tag_profession.add(profession_name)
            tag_position.add(position_name)
            tag_tagList.update(tags)
        tags.append(profession_name)
        tags.append(position_name)
        return frozenset(tags)
    def gen_rarity(char_data):
        return int(char_data.get('rarity')[-1:])
    def gen_img(url_raw,char_id):
        file = url_raw.format(charid=char_id)
        url = Data.url_agr + file
        return GData.img(file,url)
    def recruitable(char_id):
        if Data.server=='CN':
            if GData.json_tl('akhr').get(char_id) and GData.json_tl('akhr').get(char_id,{}).get('hidden')!=True:
                return True
        else:
            if GData.json_tl('akhr').get(char_id) and GData.json_tl('akhr').get(char_id,{}).get('globalHidden')!=True:
                return True
        return False
    for char_id,char_data in character_table.items():
        if (
            'notchar' in char_data.get('subProfessionId')
            or char_data.get('profession') in ['TOKEN','TRAP']
        ):
            continue
        char=Character(
            characterId=char_id,
            name=char_data.get('name'),
            profession=char_data.get('profession'),
            subProfessionId=char_data.get('subProfessionId'),
            position=char_data.get('position'),
            tags=gen_tags(char_data),
            rarity=gen_rarity(char_data),
            avatar=gen_img(Data.name_avatar,char_id),
            # avatar2=gen_img(Data.name_avatar2,char_id),
            # portrait=gen_img(Data.name_portrait,char_id),
            # portrait2=gen_img(Data.name_portrait2,char_id),
            itemObtainApproach=char_data.get('itemObtainApproach') or '',
            recruitable=recruitable(char_id),
        )
        Data.chars[char_id]=char
    Data.chars = {k:v for k,v in sorted(Data.chars.items(), key=lambda item:(-item[1].rarity,item[1].name))}
    Data.all_tags = [tag_profession,tag_position,tag_tagList]
    
def prep_tags_char():
    Data.tags_result={}
    Data.tag_rarity={}
    for char_id,char in Data.chars.items():
        # if Data.itemObtainApproach_recruit in char.itemObtainApproach:
        if char.recruitable==True:
            if char.rarity<6:
                for tags_ in subset(char.tags,self=1):
                    Data.tags_result.setdefault(tags_,{}).setdefault(char.rarity,[]).append(char)
    for tags,rarity_char in Data.tags_result.items():
        m3 = min([r for r in rarity_char if r>=3] or [0])
        m2 = min([r for r in rarity_char if r>=2] or [0])
        m1 = min([r for r in rarity_char if r>=1] or [0])
        m=max(m3,m2,m1)
        rarity_char['rarity']=m
        if len(tags)==1:
            Data.tag_rarity[next(iter(tags))]=m
    Data.all_tags=[sorted(list(tag_sub),key=lambda tag:(Data.tag_rarity.get(tag),tag)) for tag_sub in Data.all_tags]

def sort_result(res):
    return {k:v for k,v in sorted(res.items(), key=lambda item:item[1]['rarity'],reverse=True)}

def recruit(tags):
    return sort_result({tags_:Data.tags_result.get(tags_) for tags_ in subset(tags,self=1) if tags_ in Data.tags_result})

@dataclass
class CharacterExcel:
    characterId:str
    name:str
    profession:str
    subProfessionId:str
    position:str
    rarity:str
    tags:frozenset
    @classmethod
    def from_character(cls, char):
        return cls(
            characterId=char.characterId,
            name=char.name,
            profession=char.profession.title(),
            subProfessionId=char.subProfessionId.title(),
            position=char.position.title(),
            rarity=char.rarity,
            tags=char.tags,
        )

def prep_chars_excel():
    Data.chars_excel={}
    Data.chars_excel = {characterId:CharacterExcel.from_character(char) for characterId,char in Data.chars.items()}

def save_excel():
    df = pd.DataFrame(Data.chars_excel.values())
    df.to_excel('char.xlsx')
    print(df)

def init(server='US',lang='en'):
    Data.server=server #US CN JP KR
    Data.lang=lang #en ja ko zh
    # Data.server='CN' #US CN JP KR
    # Data.lang='zh' #en ja ko zh
    print('char init',Data.server,Data.lang)
    prep_chars()
    prep_tags_char()
    prep_chars_excel()

class UiTag(QtWidgets.QLabel):
    def __init__(self,tag):
        super(UiTag, self).__init__()
        self.setText(tag)
        color = Data.rarity_color.get(Data.tag_rarity.get(tag))
        self.setStyleSheet(f"QLabel{{background-color:{color};color:black;}}")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

class UiChar(QtWidgets.QLabel):
    def __init__(self,char):
        super(UiChar, self).__init__()
        self.setText(char.name)
        color = Data.rarity_color.get(char.rarity)
        self.setStyleSheet(f"QLabel{{background-color:{color};color:black;}}")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)
        
class UiTagset(QtWidgets.QWidget):
    def __init__(self,tagset):
        super(UiTagset, self).__init__()
        hlayout = MyHBoxLayout()
        self.setLayout(hlayout)
        for tag in tagset:
            hlayout.addWidget(UiTag(tag))
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

class UiResultSub(QtWidgets.QWidget):
    def __init__(self,result):
        super(UiResultSub, self).__init__()
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
                    hlayout.addWidget(UiChar(char))
                    idx+=1
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

def set_space(layout):
    if hasattr(layout,'setHorizontalSpacing'):
        layout.setHorizontalSpacing(0)
    if hasattr(layout,'setVerticalSpacing'):
        layout.setVerticalSpacing(0)

class MyGridLayout(QtWidgets.QGridLayout):
    def __init__(self):
        super(MyGridLayout, self).__init__()
        set_space(self)
class MyVBoxLayout(QtWidgets.QVBoxLayout):
    def __init__(self):
        super(MyVBoxLayout, self).__init__()
        set_space(self)
class MyHBoxLayout(QtWidgets.QHBoxLayout):
    def __init__(self):
        super(MyHBoxLayout, self).__init__()
        set_space(self)

class UiResult(QtWidgets.QWidget):
    def __init__(self,tags):
        super(UiResult, self).__init__()
        if not tags:
            vlayout = MyVBoxLayout()
            self.setLayout(vlayout)
            vlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, vPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
            return
        res = recruit(tags)
        layout = MyGridLayout()
        set_space(layout)
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
            label_rarity.setStyleSheet(f"QLabel{{background-color:{Data.rarity_color.get(result.get('rarity'))};color:black;}}")
            glayout.addWidget(UiTagset(tagset),row,0)
            glayout.addWidget(label_rarity,row,1)
            glayout.addWidget(UiResultSub(result),row,2)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)

class UiTagSelect(QtWidgets.QPushButton):
    def __init__(self,tag):
        super(UiTagSelect, self).__init__()
        Data.tag_rarity.get(tag)
        self.setText(tag)
        self.setCheckable(True)
        self.setStyleSheet(f'QPushButton{{background-color:{Data.rarity_color.get(Data.tag_rarity.get(tag))};color:black;}}')
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum,QtWidgets.QSizePolicy.Policy.Minimum)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,QtWidgets.QSizePolicy.Policy.Preferred)
        # self.resize(self.sizeHint().width(), self.sizeHint().height())

class UiTagsSelect(QtWidgets.QWidget):
    def __init__(self,ui_rectag):
        super(UiTagsSelect, self).__init__()
        self.ui_rectag = ui_rectag
        self.alltag=[x for xs in Data.all_tags for x in xs]
        vlayout = MyVBoxLayout()
        self.taginput=QtWidgets.QLineEdit()
        self.taginput.returnPressed.connect(self.addtag)
        self.taginput_result=QtWidgets.QLabel()
        vlayout.addWidget(self.taginput)
        vlayout.addWidget(self.taginput_result)
        self.setLayout(vlayout)
        self.uitags={}
        hlayout=None
        for row,tag_sub in enumerate(Data.all_tags):
            for idx,tag in enumerate(tag_sub):
                if idx%9==0:
                    if hlayout:
                        hlayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, hPolicy=QtWidgets.QSizePolicy.Policy.Expanding))
                    hlayout = MyHBoxLayout()
                    vlayout.addLayout(hlayout)
                uitag=UiTagSelect(tag)
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
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.img_anhrtags = './tmp/tmp_anhrtags.png'
    @QtCore.pyqtSlot()
    def ocr_win(self):
        tags=win_tag(self.img_anhrtags)
        # self.ui_tags.select(tags)
        # self.set_view()
        self.send_tags.emit(tags)
    @QtCore.pyqtSlot()
    def ocr_adb(self):
        tags=adb_tag(self.img_anhrtags)
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
    def __init__(self,server='US',lang='en'):
        super(UiRecTag,self).__init__()
        init(server,lang)
        self.setWindowTitle(f"Arknights Tags")
        widget = QtWidgets.QWidget(self)
        self.layout = MyVBoxLayout()
        vlayout = MyVBoxLayout()
        self.setCentralWidget(widget)
        widget.setLayout(vlayout)
        vlayout.addLayout(self.layout)
        self.view=None
        self.ui_tags = UiTagsSelect(self)
        self.add(self.ui_tags)
        self.ui_tags.select(['Vanguard', 'Crowd-Control', 'DP-Recovery', 'Debuff', 'Healing'])
        self.views={}
        self.set_view()
        self.qobj_worker = UiRecTagWorker()
        self.worker_thread = QtCore.QThread()
        self.qobj_worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        self.qobj_worker.send_tags.connect(self.update_tags)
        self.ui_tags.real_ok=self.set_view
        self.ui_tags.button_ok.clicked.connect(self.set_view)
        self.ui_tags.button_ocrwin.clicked.connect(self.ocr_win)
        self.ui_tags.button_ocradb.clicked.connect(self.ocr_adb)
        self.ui_tags.button_adbkill.clicked.connect(self.qobj_worker.adb_kill_server)
        self.signal_ocr_win.connect(self.qobj_worker.ocr_win)
        self.signal_ocr_adb.connect(self.qobj_worker.ocr_adb)
    @QtCore.pyqtSlot()
    def ocr_win(self):
        self.update_tags([])
        self.signal_ocr_win.emit()
    @QtCore.pyqtSlot()
    def ocr_adb(self):
        self.update_tags([])
        self.signal_ocr_adb.emit()
    @QtCore.pyqtSlot(list)
    def update_tags(self,tags):
        self.ui_tags.select(tags)
        self.set_view()
    @QtCore.pyqtSlot()
    def set_view(self):
        tagset = self.ui_tags.tagset()
        if tagset in self.views:
            view=self.views[tagset]
        else:
            view=UiResult(tagset)
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

if __name__ == "__main__":
    init()
    save_excel()
    
    # tags = ['减速','控场','费用回复','特种','远程位',]
    tags = ['Vanguard', 'Crowd-Control', 'DP-Recovery', 'Debuff', 'Healing']
    res = recruit(tags)
    pprint.pprint(res)
    
    # app = QtWidgets.QApplication([])
    # root = UiRecTag()
    # root.show()
    # ret = app.exec()
    # exit(ret)

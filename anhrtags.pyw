import os
import sys
import pickle
import json
from functools import cache
import urllib.request
import tkinter as tk
from tkinter import ttk
from itertools import combinations
import threading
import re
app_path = os.path.dirname(__file__)
os.chdir(app_path)
try:
    import cv2 as cv
    import numpy as np
    import pytesseract
    import win32gui
    import win32ui
    pytesseract.pytesseract.tesseract_cmd = os.path.abspath(r'../../Tesseract-OCR/tesseract.exe')
except Exception as e:
    print(e)
    print("""
    #1 Install tesseract https://github.com/UB-Mannheim/tesseract/wiki
    #2 pip install --upgrade pywin32 pytesseract opencv-python
    #3 set pytesseract.pytesseract.tesseract_cmd = r'your path/tesseract.exe'
    """)
    
def subset(taglist,maxtag=6,self=0):
    for i in range(1,min(maxtag+1,len(taglist)+self)):
        for s in combinations(taglist, i):
            yield frozenset(s)

class Character():
    version=14
    @staticmethod
    @cache
    def json_tl(name):
        url_tl_akhr = f'https://github.com/Aceship/AN-EN-Tags/raw/master/json/tl-{name}.json'
        file_tl_akhr = f'tl-{name}.json'
        if not os.path.isfile(file_tl_akhr):
            urllib.request.urlretrieve(url_tl_akhr, file_tl_akhr)
        with open(file_tl_akhr, "r", encoding="utf-8") as f:
            if name=='akhr':
                return {item.get('id'):item for item in json.load(f)}
            # if name=='type':
                # return {item.get('type_data'):item for item in json.load(f)}

    @staticmethod
    @cache
    def _character_table(lang='en_US'):
        url_character_table = f'https://github.com/Aceship/AN-EN-Tags/raw/master/json/gamedata/{lang}/gamedata/excel/character_table.json'
        file_character_table = f'character_table_{lang}.json'
        if not os.path.isfile(file_character_table):
            urllib.request.urlretrieve(url_character_table, file_character_table)
        with open(file_character_table, "r", encoding="utf-8") as f:
            return json.load(f)
    
    @staticmethod
    def key_type(typa):
        keys=[]
        for char_id,char_data in Character._character_table().items():
            for key in ['name', 'description', 'canUseGeneralPotentialItem', 'canUseActivityPotentialItem', 'potentialItemId', 'activityPotentialItemId', 'classicPotentialItemId', 'nationId', 'groupId', 'teamId', 'displayNumber', 'appellation', 'position', 'tagList', 'itemUsage', 'itemDesc', 'itemObtainApproach', 'isNotObtainable', 'isSpChar', 'maxPotentialLevel', 'rarity', 'profession', 'subProfessionId', 'trait', 'phases', 'skills', 'displayTokenDict', 'talents', 'potentialRanks', 'favorKeyFrames', 'allSkillLvlup']:
                if isinstance(char_data[key],typa):
                    if key not in keys:
                        keys.append(key)
        return keys

    @staticmethod
    def recruitable(char_id):
        if Character.json_tl('akhr').get(char_id) and Character.json_tl('akhr').get(char_id,{}).get('globalHidden')!=True:
            return True

    position_name = {
        "RANGED": "Ranged",
        "MELEE": "Melee",
    }
    profession_name = {  
        "WARRIOR": "Guard",
        "SNIPER": "Sniper",
        "TANK": "Defender",
        "MEDIC": "Medic",
        "SUPPORT": "Supporter",
        "CASTER": "Caster",
        "SPECIAL": "Specialist",
        "PIONEER": "Vanguard",
    }
    
    @staticmethod
    @cache
    def get_all(key):
        values = []
        for char_id,char_data in Character._character_table().items():
            if Character.recruitable(char_id):
                if key in Character.key_type(list):
                    for value in char_data.get(key,[]) or []:
                        if value not in values:
                            values.append(value)
                else:
                    value = char_data.get(key,'')
                    if key=='profession':
                        value=Character.profession_name.get(value,value)
                    elif key=='position':
                        value=Character.position_name.get(value,value)
                    if value not in values:
                        values.append(value)
        return values

    @staticmethod
    @cache
    def profession():
        return tuple(sorted([Character.profession_name.get(profession,profession) for profession in Character.get_all('profession')]))

    @staticmethod
    @cache
    def position():
        return tuple(sorted([Character.position_name.get(position,position) for position in Character.get_all('position')]))

    @staticmethod
    @cache
    def tagList():
        return tuple(sorted(Character.get_all('tagList')))

    @staticmethod
    @cache
    def all_tags():
        return tuple(Character.tagList()+Character.profession()+Character.position())
        
    @staticmethod
    @cache
    def all_tags_sorted():
        return sorted(Character.all_tags(), key=len, reverse=True)

    @staticmethod
    @cache
    def recruits_tag(tier_str='345'):        
        # 1234 2345 345 5 6
        tier=[]
        for i in tier_str:
            tier.append(f'TIER_{i}')

        characters_tag={}
        for char_id,char_data in Character._character_table().items():
            if Character.recruitable(char_id) and char_data.get('rarity','None') in tier:
                char_tags=set(char_data.get('tagList',[])or[])
                profession=char_data.get('profession')
                char_tags.add(Character.profession_name.get(profession,profession))
                position=char_data.get('position')
                char_tags.add(Character.position_name.get(position,position))
                characters_tag[char_id]=char_tags
        return characters_tag
        
    @staticmethod
    def char_ids(tag,tier_str='345'):
        if isinstance(tag,str):
            tag=[tag]
        return Character._char_ids(frozenset(tag),tier_str)

    @staticmethod
    @cache
    def _char_ids(tag,tier_str='345'):
        def search():
            for char_id,char_tags in Character.recruits_tag(tier_str).items():
                if set(tag).issubset(char_tags):
                    yield char_id
        return list(search())
        
    @staticmethod
    def char_id_rarity(char_ids):
        if char_ids:
            if isinstance(char_ids,str):
                return [int(Character._character_table()[char_ids].get('rarity')[-1:])]
            raritys=[]
            for char_id in char_ids:
                rarity = Character._character_table()[char_id].get('rarity')
                rarity = int(rarity[-1:])
                raritys.append(rarity)
            return raritys
            
    @staticmethod
    def rarity(tag) -> int:
        rarity = Character._rarity(tag, '345')
        if rarity:
            return rarity
        rarity = Character._rarity(tag, '2345')
        if rarity:
            return rarity
        rarity = Character._rarity(tag, '1234')
        return rarity

    @staticmethod
    def _rarity(tag,tier_str='345'):
        raritys = Character.char_id_rarity(Character.char_ids(tag,tier_str))
        if raritys:
            return min(raritys)
        
    @staticmethod
    @cache
    def tag_byrarity():
        x = {tag:Character.rarity(tag) for tag in Character.all_tags()}
        return {k: v for k, v in sorted(x.items(), key=lambda item: item[1], reverse=True)}

    @staticmethod
    @cache
    def comb(taglist=None,maxtag=6,shorten=True):
        if taglist==None:
            taglist=Character.all_tags()
        tagset_list=list(subset(taglist,maxtag=maxtag,self=1))
        tagset_list_valid=[]
        for tagset in tagset_list:
            ok=True
            if Character.rarity(tagset):
                for subtagset in subset(tagset,maxtag=maxtag,self=0):
                    if Character.rarity(subtagset) and (shorten and Character.rarity(tagset)<=Character.rarity(subtagset)):
                        ok=False
                        break
            else:
                ok=False
            if ok:
                tagset_list_valid.append(tagset)
        return tagset_list_valid
        
    @staticmethod
    @cache
    def comb_dict(taglist=None,maxtag=6):
        tagset_list = Character.comb(taglist,maxtag,shorten=True)
        tagset_dict={}
        added=[]
        for tag in Character.tag_byrarity():
            for tagset in tagset_list:
                if tag in tagset and tagset not in added:
                    taglist=list(tagset)
                    taglist.remove(tag)
                    tagset_dict.setdefault(tag,[]).append(taglist)
                    added.append(tagset)
        return tagset_dict

    @staticmethod
    @cache
    def min_tier(tier_str):
        return min([int(i) for i in tier_str])
        
    @staticmethod
    def char_ids_format(taglist=None,maxtag=6):
        if taglist==None:
            return Character._char_ids_format(taglist,maxtag)
        else:
            return Character._char_ids_format(frozenset(taglist),maxtag)
    
    @staticmethod
    @cache
    def _char_ids_format(taglist=None,maxtag=6):
        txt_data=[]
        def txt_insert(value,style=''):
            txt_data.append((value,style))
            return len(value)
        def generate_txt_data(tagset_list):
            length_max=max([len(' '.join(tagset)) for tagset in tagset_list])
            for tagset in tagset_list:
                rarity = Character.rarity(tagset)
                if rarity:
                    char_ids = Character.char_ids(tagset,'12345')
                    length=0
                    for tag in tagset:
                        if length>0:
                            length+=txt_insert(' ')
                        length+=txt_insert(tag, Character.rarity(tag))
                    length+=txt_insert(f'{' '*(length_max-length)}')
                    length+=txt_insert(':',rarity)
                    length+=txt_insert(' ')
                    char_ids_rarity = Character.char_id_rarity(char_ids)
                    for char_id,char_id_rarity in sorted(zip(char_ids,char_ids_rarity), key=lambda x: (-x[1],x[0])):
                        name = Character._character_table()[char_id].get('name')
                        if length+len(name) > 101:
                            length=0
                            length+=txt_insert(f'\n{' '*(length_max+2)}')
                        length+=txt_insert(name, char_id_rarity)
                        length+=txt_insert(' ')
                    length+=txt_insert('\n')
        tagset_list = Character.comb(taglist,maxtag,shorten=False)
        generate_txt_data(sorted(tagset_list,key=lambda tagset: Character.rarity(tagset),reverse=True))
        return txt_data

    @staticmethod
    def tagset_format(taglist=None,maxtag=6):
        if taglist==None:
            return Character._tagset_format(taglist,maxtag)
        else:
            return Character._tagset_format(frozenset(taglist),maxtag)

    @staticmethod
    @cache
    def _tagset_format(taglist=None,maxtag=6):
        txt_data=[]
        def txt_insert(value,style=''):
            txt_data.append((value,style))
        def generate_txt_data(tagset_dict):
            for tag,part_tags in tagset_dict.items():
                show=False
                rarity = Character.rarity(tag)
                for part_tag in part_tags:
                    if part_tag:
                        show=True
                        break
                if not (rarity==3 and not show and taglist==None):
                    txt_insert(tag, rarity)
                if show:
                    txt_insert(' '*(max(15-len(tag),1))+'+ ')
                    for part_tag in part_tags:
                        if part_tag:
                            rarity1=Character.rarity([tag]+part_tag)
                            txt_insert('+'.join(part_tag), rarity1)
                            txt_insert(' ')
                if not (rarity==3 and not show and taglist==None):
                    txt_insert('\n')
        tagset_dict = Character.comb_dict(taglist,maxtag)
        generate_txt_data(tagset_dict)
        return txt_data

    @staticmethod
    def hr_all():
        result_file="ArknightsRecruitmentTag.tmp"
        def save_result(obj):
            with open(result_file, "wb") as pickle_file:
                pickle.dump([Character.version,obj], pickle_file, pickle.HIGHEST_PROTOCOL)
        def load_result():
            try:
                with open(result_file, "rb") as pickle_file:
                    version,obj = pickle.load(pickle_file)
                    if version==Character.version:
                        return obj
            except: pass
            return []
        txt_data=load_result()
        if not txt_data:
            def txt_insert(value,style=''):
                txt_data.append((value,style))
            for i in range(6,0,-1):
                txt_insert(f"t{i}", i)
            txt_insert("\n")
            txt_insert("Top Operator", 6)
            txt_insert("\n")
            txt_insert("Senior Operator", 5)
            txt_insert("\n")
            txt_data+=Character.tagset_format()
            save_result(txt_data)
        return txt_data

def windows_image(img,app_title='Arknights',border=False,scaled=True):
    from ctypes import windll
    from PIL import Image
    def remove_img(img):
        if os.path.isfile(img):
            os.remove(img)
    remove_img(img)
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
    im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    if result == 1:
        im.save(img)

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
    file='roi.json'
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
    from multiprocessing import Process
    p = Process(target=windows_image, args=(img_anhrtags,))
    p.start()
    p.join()
    return list(img_tag(img_anhrtags,setup=setup))

def img_tag(img_anhrtags,setup=False):
    if not os.path.isfile(img_anhrtags):
        return iter(())
    img = cv.imread(img_anhrtags,cv.IMREAD_GRAYSCALE)
    img=resize(img,width=1000)
    height=int(img.shape[0])
    height_key=str(height)
    print(f'\nimg_tag:\n{height=}')
    roidata=roi_data().load()
    if setup or (height_key not in roidata) or (height_key in roidata and height<1000 and not roidata[height_key]):
        ROIs=[]
        tags=[]
        for tag,x,y,w,h in _img_tag(img_anhrtags,setup=setup):
            ROIs.append([x,y,w,h])
            tags.append(tag)
        if len(ROIs)>=5:
            roidata[height_key]=ROIs
            roi_data().save(roidata)
        yield from tags
    else:
        ROIs=roidata[height_key]
        tags=[]
        for rect in ROIs:
            x,y,w,h=rect
            img_crop=img[y:y+h,x:x+w]
            tag_ocrs = pytesseract.image_to_string(img_crop)
            taglow_tag = {tag.lower():tag for tag in Character.all_tags_sorted()}
            print(tag_ocrs.strip())
            for tag_ocr in tag_ocrs.lower().split():
                for taglow,tag in taglow_tag.items():
                    if taglow in tag_ocr:
                        if tag not in tags:
                            yield tag
                            tags.append(tag)
                        break

def _img_tag(img_anhrtags,setup=False):
    if not os.path.isfile(img_anhrtags):
        return iter(())
    img = cv.imread(img_anhrtags,cv.IMREAD_GRAYSCALE)
    img=resize(img,width=1000)
    # cv.imwrite(f"anhrtags_1000.png",img)
    height=int(img.shape[0])
    print(f'\nimg_tag :\n{height=}')
    th = cv.inRange(img, 49, 49)
    th1 = cv.inRange(img, 114, 114)
    th2 = cv.inRange(img, 141, 141)
    th = cv.bitwise_or(th, th1)    
    th = cv.bitwise_or(th, th2)    
    contours, hier = cv.findContours(th, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    contours_list = [(contour,cv.boundingRect(contour)) for contour in contours if cv.contourArea(contour)>1000]
    tags=[]
    for contour,(x,y,w,h) in sorted(contours_list, key=lambda i:i[1][1],reverse=True):
        if len(tags)>=5:
            return
        # if w in range(98-1,111+2) and h in range(30-1,35+2):
        print(x,y,w,h,end=' ')
        # mask = np.zeros_like(img)
        # cv.drawContours(mask, [contour], 0, 255, -1)
        # img_ = cv.bitwise_and(img, mask)
        img_crop = img[y+1:y+h-1, x+1:x+w-1]
        tag_ocrs = pytesseract.image_to_string(img_crop)
        tag_ocrs = re.sub(r'[^\w-]', ' ', tag_ocrs).replace('OPS','DPS').replace('bps','DPS')
        taglow_tag = {tag.lower():tag for tag in Character.all_tags_sorted()}
        print(tag_ocrs.strip())
        for tag_ocr in tag_ocrs.lower().split():
            for taglow,tag in taglow_tag.items():
                if taglow in tag_ocr:
                    if tag not in tags:
                        tags.append(tag)
                        yield tag,x+1,y+1,w-2,h-2
                        # yield tag,x,y,w,h
                        # yield tag
                    break

# def img_tag1(img_anhrtags,setup=False):
    # if not os.path.isfile(img_anhrtags):
        # return iter(())
    # img = cv.imread(img_anhrtags,cv.IMREAD_GRAYSCALE)
    # img=resize(img,width=1000)
    # height=int(img.shape[0])
    # height_key=str(height)
    # print(f'\nimg_tag:\n{height=}')
    # def set_roi():
        # ROIs = cv.selectROIs('Select 5 tag area, ok=Space/Enter, finish=ESC', img, showCrosshair=False, fromCenter=False, printNotice=True)
        # cv.destroyAllWindows()
        # ROIs = [[int(x),int(y),int(w),int(h)] for x,y,w,h in ROIs]
        # print(f'{ROIs=}')
        # if ROIs:
            # roidata=roi_data().load()
            # roidata[height_key]=ROIs
            # roi_data().save(roidata)
            # return roidata
        # return {}
    # roidata=roi_data().load()
    # if setup or (height_key not in roidata) or (height_key in roidata and height<1000 and not roidata[height_key]):
        # roidata=set_roi()
    # ROIs=roidata[height_key]
    # tags=[]
    # for idx,rect in enumerate(ROIs):
        # x,y,w,h=rect
        # img_crop=img[y:y+h,x:x+w]
        # tag_ocrs = pytesseract.image_to_string(img_crop)
        # taglow_tag = {tag.lower():tag for tag in Character.all_tags_sorted()}
        # print(tag_ocrs.strip())
        # for tag_ocr in tag_ocrs.lower().split():
            # for taglow,tag in taglow_tag.items():
                # if taglow in tag_ocr:
                    # if tag not in tags:
                        # yield tag
                        # tags.append(tag)
                    # break

def adb_tag(img_anhrtags,setup=False):
    import shellcmd1 as shellcmd
    import pprint
    def _adb_tag(adev):
        if isinstance(adev,shellcmd.AndroidDev):
            img = adev.screencap(name1=img_anhrtags,open_img=False)
            if img:
                return list(img_tag(img,setup=setup))
    try:
        adev = shellcmd.AndroidDev() # adb usb
        tags = _adb_tag(adev)
        if tags:
            return tags
    except Exception as e:
        print(e)
    mdns = shellcmd.AndroidDev.adb_mdns(retry=2)
    pprint.pprint(mdns)
    adev_name=None
    for device,info in mdns.items():
        adev_name = info['device_ip']
        if adev_name:    
            adev = shellcmd.AndroidDev(adev_name, adb_tcpip=False) # adb wireless 
            tags = _adb_tag(adev)
            if tags:
                return tags
    return []

def ui_hr_tag(tags=[]):
    class Checkbar(tk.Frame):
        def __init__(self, parent=None, picks=[]):
            super().__init__(parent)
            self.checks_value = []
            self.checks={}
            for r,checklist in enumerate(picks):
                tag_frame = tk.Frame(self, bg='white')
                for c,tag in enumerate(checklist):
                    value = tk.StringVar(value="")
                    chk = tk.Checkbutton(tag_frame, text=tag, variable=value, onvalue=tag, offvalue="", indicatoron=False,foreground=colors.get(Character.rarity(tag),'black'))
                    chk.grid(row=0, column=c)
                    self.checks[tag]=chk
                    self.checks_value.append(value)
                tag_frame.grid(row=r, column=0, sticky="wens")
            btn_frame = tk.Frame(self, bg='white')
            btn_frame.grid(row=len(picks), column=0, sticky="wens")
            img_anhrtags = 'tmp_anhrtags.png'
            def ocr_win():
                self.ui_clear()
                tags=win_tag(img_anhrtags)
                self.select(tags)
                self.real_ok(tags)
            def ocr_adb():
                self.ui_clear()
                tags=adb_tag(img_anhrtags)
                self.select(tags)
                self.real_ok(tags)
            # def draw_roi():
                # self.ui_clear()
                # tags=list(img_tag(img_anhrtags,setup=True))
                # print(tags)
                # self.select(tags)
                # self.real_ok(tags)
            column_btn=0
            def create_btn(text,command):
                nonlocal column_btn
                def real_on_click():
                    real_on_click.btn.config(state=tk.DISABLED) #prevent call twice
                    real_on_click.btn.update()
                    try:
                        command()
                    except Exception as e:
                        print(e)
                    real_on_click.btn.config(state=tk.NORMAL)
                def on_click():
                    if not (getattr(on_click,'timer',None) and on_click.timer.is_alive()): #prevent call twice
                        on_click.timer = threading.Timer(0, real_on_click) 
                        on_click.timer.start()
                btn = ttk.Button(btn_frame,text=text,command=on_click)
                real_on_click.btn=btn
                btn.grid(row=len(picks), column=column_btn)
                column_btn+=1
            create_btn('Ok',self.ok)
            create_btn('Clear',lambda:[self.select([]), self.ui_clear()])
            create_btn('OCR-win',ocr_win)
            create_btn('OCR-adb',ocr_adb)
            # create_btn('draw ROI',draw_roi)
            
            self.real_ok=None
        def ok(self):
            if getattr(self,'real_ok',None):
                self.real_ok(self.check())
        def check(self):
            return [value.get() for value in self.checks_value if value.get()]
        def select(self,tags):
            for tag,chk in self.checks.items():
                if tag in tags:
                    chk.select()
                else:
                    chk.deselect()
    def txt_color(txt):
        for i in range(6,0,-1):
            txt.tag_config(str(i), background=colors.get(i,'white'), foreground="black")
            txt.tag_config(i, background=colors.get(i,'white'), foreground="black")
        txt.tag_config('', background="white", foreground="black")
    def real_txt_insert(txt, txt_data):
        for value,style in txt_data:
            txt.insert('end',value,style)

    root = tk.Tk()
    root.title("Arknights Recruitment Tag")
    
    txt_frame = tk.Frame(root, bg='white', pady=3)
    txtm_frame = tk.Frame(root, bg='white', pady=3)
    
    colors={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }

    check_frame=Checkbar(root,[Character.profession(),Character.position(),Character.tagList()])
    print(Character.profession()) 
    print(Character.position()) 
    print(Character.tagList())

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    txt_frame.grid(row=0, sticky="wens")
    check_frame.grid(row=1, sticky="wes")
    txtm_frame.grid(row=2, sticky="wens")

    txt = tk.Text(txt_frame, wrap='none',width=5,height=10)
    txtm = tk.Text(txtm_frame, wrap='none',width=5,height=10)
    txt.pack(fill="both", expand=True)
    txtm.pack(fill="both", expand=True)
    
    txt_color(txt)
    txt_color(txtm)
    
    txt_data = Character.hr_all()
    txt.configure(state='normal')
    real_txt_insert(txt, txt_data)
    text=txt.get('1.0', 'end-1c').splitlines()
    txt_width=len(max(text, key=len))
    txt.configure(height=len(text),width=txt_width)
    txt.configure(state='disabled')
    def clear():
        txtm.configure(state='normal')
        txtm.delete("1.0",tk.END)
        txtm.configure(state='disabled')
        txtm.update()
    def ok(tags):
        txt_data=[]
        txt_data+=Character.tagset_format(taglist=tags,maxtag=len(tags))
        txt_data.append(('\n',''))
        txt_data+=Character.char_ids_format(taglist=tags,maxtag=len(tags))
        txtm.configure(state='normal')
        txtm.delete("1.0",tk.END)
        txtm.insert('end', f"{tags}\n")
        real_txt_insert(txtm, txt_data)
        text=txtm.get('1.0', 'end-1c').splitlines()
        width=len(max(text, key=len))
        txtm.configure(height=len(text),width=max(width,txt_width))
        txtm.configure(state='disabled')
    if tags:
        check_frame.select(tags)
        ok(tags)
    check_frame.real_ok=ok
    check_frame.ui_clear=clear
    root.mainloop()

if __name__ == "__main__":
    tags=['Caster', 'Defense']
    ui_hr_tag(tags)

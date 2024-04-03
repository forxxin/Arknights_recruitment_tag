import os
import sys
import pickle
import json
from functools import cache
import urllib.request
import tkinter as tk
from itertools import combinations
#1 Install tesseract https://github.com/UB-Mannheim/tesseract/wiki
#2 pip install --upgrade pywin32 pytesseract opencv-python
#3 set pytesseract.pytesseract.tesseract_cmd = r'your path/tesseract.exe'
app_path = os.path.dirname(__file__)
os.chdir(app_path)
try:
    import cv2 as cv
    import pytesseract
    import win32gui
    import win32ui
    pytesseract.pytesseract.tesseract_cmd = os.path.abspath(r'../../Tesseract-OCR/tesseract.exe')
except:
    pass
    
def subset(taglist,maxtag=6,self=0):
    for i in range(1,min(maxtag+1,len(taglist)+self)):
        for s in combinations(taglist, i):
            yield frozenset(s)

class Character():
    version=9
    @staticmethod
    @cache
    def _tl_akhr():
        url_tl_akhr = 'https://github.com/Aceship/AN-EN-Tags/raw/master/json/tl-akhr.json'
        file_tl_akhr = 'tl-akhr.json'
        if not os.path.isfile(file_tl_akhr):
            urllib.request.urlretrieve(url_tl_akhr, file_tl_akhr)
        with open(file_tl_akhr, "r", encoding="utf-8") as f:
            return {akhr.get('id'):akhr for akhr in json.load(f)}

    @staticmethod
    @cache
    def _character_table():
        # lang='ja_JP'
        # lang='ko_KR'
        # lang='zh_TW'
        # lang='zh_CN'
        lang='en_US'
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
        if Character._tl_akhr().get(char_id) and Character._tl_akhr().get(char_id,{}).get('globalHidden')!=True:
            return True

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
        return tuple(sorted(Character.get_all('position')))

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
                char_tags.add(char_data.get('position'))
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
    def char_ids_rarity(char_ids):
        if char_ids:
            raritys=[]
            for char_id in char_ids:
                rarity = Character._character_table()[char_id].get('rarity')
                raritys.append(rarity)
            raritys.sort()
            return int(raritys[0][-1:])

        
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
        return Character.char_ids_rarity(Character.char_ids(tag,tier_str))
        
    @staticmethod
    @cache
    def tag_byrarity():
        x = {tag:Character.rarity(tag) for tag in Character.all_tags()}
        return {k: v for k, v in sorted(x.items(), key=lambda item: item[1], reverse=True)}

    @staticmethod
    def comb(taglist=None,maxtag=6):
        if taglist==None:
            taglist=Character.all_tags()
        tagset_list=list(subset(taglist,maxtag=maxtag,self=1))
        tagset_list_norepeat=[]
        for tagset in tagset_list:
            ok=True
            if Character.rarity(tagset):
                for subtagset in subset(tagset,maxtag=maxtag,self=0):
                    if Character.rarity(subtagset) and Character.rarity(tagset)<=Character.rarity(subtagset):
                        ok=False
                        break
            else:
                ok=False
            if ok:
                tagset_list_norepeat.append(tagset)
        return tagset_list_norepeat

    @staticmethod
    def comb_dict(taglist=None,maxtag=6):
        tagset_list = Character.comb(taglist,maxtag)
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

def app_image(img,app_title='Arknights',border=False,scaled=True):
    from ctypes import windll
    from PIL import Image
    def remove_img(img):
        if os.path.isfile(img):
            os.remove(img)
    remove_img(img)
    hwnd = win32gui.FindWindow(None, app_title)
    if scaled:
        # if use a high DPI display or >100% scaling size
        windll.user32.SetProcessDPIAware()
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
    # print(result)
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

def ocr_tag(img_anhrtags, setup=False):
    app_image(img=img_anhrtags)
    return list(img_tag(img_anhrtags,setup=setup))
def img_tag(img_anhrtags,setup=False):
    img = cv.imread(img_anhrtags,cv.IMREAD_GRAYSCALE)
    img=resize(img,width=1000)
    height=int(img.shape[0])
    height_key=str(height)
    print(f'\nimg_tag:\n{height=}')
    def set_roi():
        ROIs = cv.selectROIs('Select 5 tag area, ok=Space/Enter, finish=ESC', img, showCrosshair=False, fromCenter=False, printNotice=True)
        cv.destroyAllWindows()
        ROIs = [[int(x),int(y),int(w),int(h)] for x,y,w,h in ROIs]
        print(f'{ROIs=}')
        if ROIs:
            roidata=roi_data().load()
            roidata[height_key]=ROIs
            roi_data().save(roidata)
            return roidata
        return {}
    roidata=roi_data().load()
    if setup or (height_key not in roidata) or (height_key in roidata and height<1000 and not roidata[height_key]):
        roidata=set_roi()
    ROIs=roidata[height_key]
    for idx,rect in enumerate(ROIs):
        x,y,w,h=rect
        img_crop=img[y:y+h,x:x+w]
        tag_ocrs = pytesseract.image_to_string(img_crop)
        taglow_tag = {tag.lower():tag for tag in Character.all_tags_sorted()}
        print(tag_ocrs.strip())
        tags=[]
        for tag_ocr in tag_ocrs.lower().split():
            for taglow,tag in taglow_tag.items():
                if taglow in tag_ocr:
                    if tag not in tags:
                        yield tag
                        tags.append(tag)
                    break

def adb_tag(img_anhrtags,setup=False):
    import shellcmd1 as shellcmd
    import pprint
    def _adb_tag(adev):
        if isinstance(adev,shellcmd.AndroidDev):
            img = adev.screencap(name1=img_anhrtags,open_img=False)
            if img:
                return list(img_tag(img,setup=setup))
    # adb usb
    try:
        adev = shellcmd.AndroidDev()
        tags = _adb_tag(adev)
        if tags:
            return tags
    except:
        pass
    mdns = shellcmd.AndroidDev.adb_mdns()
    pprint.pprint(mdns)
    adev_name=None
    for device,info in mdns.items():
        adev_name = info['device_ip']
        if adev_name:    
            # adb wireless 
            adev = shellcmd.AndroidDev(adev_name, adb_tcpip=False)
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
                for c,tag in enumerate(checklist):
                    value = tk.StringVar(value="")
                    chk = tk.Checkbutton(self, text=tag, variable=value, onvalue=tag, offvalue="", indicatoron=False,foreground=colors.get(Character.rarity(tag),'black'))
                    chk.grid(row=r, column=c)
                    self.checks[tag]=chk
                    self.checks_value.append(value)
            btnk = tk.Button(self,text="Ok",command=self.ok)
            btnc = tk.Button(self,text="Clear",command=lambda:[self.select([]), self.ui_clear()])
            img_anhrtags = 'tmp_anhrtags.png'
            def ocr():
                self.ui_clear()
                tags=ocr_tag(img_anhrtags)
                self.select(tags)
                self.real_ok(tags)
            btnocr = tk.Button(self,text="OCR",command=ocr)
            def adb():
                self.ui_clear()
                tags=adb_tag(img_anhrtags)
                self.select(tags)
                self.real_ok(tags)
            def draw_roi():
                self.ui_clear()
                tags=list(img_tag(img_anhrtags,setup=True))
                print(tags)
                self.select(tags)
                self.real_ok(tags)
            btnadb = tk.Button(self,text="adb",command=adb)
            btnroi = tk.Button(self,text="draw ROI",command=draw_roi)
            btnk.grid(row=len(picks), column=0)
            btnc.grid(row=len(picks), column=1)
            btnocr.grid(row=len(picks), column=2)
            btnadb.grid(row=len(picks), column=3)
            btnroi.grid(row=len(picks), column=4)
            self.real_ok=None
        def ok(self):
            if self.real_ok:
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
    
    txt_frame = tk.Frame(root, bg='white', width=450, height=60, pady=3)
    txtm_frame = tk.Frame(root, bg='white', width=450, height=60, pady=3)
    
    colors={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }

    check_frame=Checkbar(root,[Character.profession(),Character.position(),Character.tagList()])
    print(Character.profession()) 
    print(Character.position()) 
    print(Character.tagList())

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    txt_frame.grid(row=0, sticky="nsew")
    check_frame.grid(row=1, sticky="nsew")
    txtm_frame.grid(row=2, sticky="nsew")

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

from dataclasses import dataclass
from itertools import combinations
import json
import pprint
import os
import re

import cv2 as cv
import numpy as np
import pytesseract
import win32gui
import win32ui

from anhrtags import TimeCost
try:
    import mods.shellcmd1 as shellcmd
except:
    import shellcmd1 as shellcmd

app_path = os.path.dirname(__file__)
os.chdir(app_path)
pytesseract.pytesseract.tesseract_cmd = os.path.abspath(r'../../Tesseract-OCR/tesseract.exe')

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

def win_tag(alltag,img_anhrtags, setup=False):
    from multiprocessing import Process,Queue
    tc=TimeCost()
    tc1=TimeCost()
    queue = Queue()
    p = Process(target=windows_image, args=(img_anhrtags,queue))
    p.start()
    img=queue.get()
    tc.end('windows_image')
    ret = list(img_tag(alltag,img_anhrtags,setup=setup,img=img))
    tc.end('img_tag')
    p.join()
    tc1.end('win_tag')
    return ret

def img_tag(alltag,img_anhrtags,setup=False,img=None):
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
        for tag,x,y,w,h in _img_tag(alltag,img,setup=setup):
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
            for tag in ocr_img(alltag,img,x,y,w,h):
                if tag not in tags:
                    tags.append(tag)
                    yield tag

def _img_tag(alltag,img,setup=False):
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
        for tag in ocr_img(alltag,img,x,y,w,h):
            if tag not in tags:
                tags.append(tag)
                yield tag,x,y,w,h

def ocr_img(alltag,img,x,y,w,h):
    img_crop=img[y:y+h,x:x+w]
    tag_ocrs = pytesseract.image_to_string(img_crop, config='''D:/CS/PythonCodes/Arknights/tessdata/bazaar''')
    tag_ocrs = re.sub(r'[^\w-]', ' ', tag_ocrs).replace('OPS','DPS').replace('bps','DPS')
    # alltag=[x for xs in Data.all_tags for x in xs]
    taglow_tag = {tag.lower():tag for tag in sorted(alltag, key=len, reverse=True)}
    print(tag_ocrs.strip())
    for tag_ocr in tag_ocrs.lower().split():
        for taglow,tag in taglow_tag.items():
            if taglow in tag_ocr:
                yield tag
                break

def adb_tag(alltag,img_anhrtags,setup=False):
    def _adb_tag(adev_name=''):
        try:
            adev = shellcmd.AndroidDev(adev_name, adb_tcpip=False) # adb wireless
        except Exception as e:
            print('adb_tag',e)
            adev=None
        if isinstance(adev,shellcmd.AndroidDev):
            img = adev.screencap(name1=img_anhrtags,open_img=False)
            if img:
                return list(img_tag(alltag,img,setup=setup))
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

if __name__ == '__main__':
    pass

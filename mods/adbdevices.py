import re
import pprint
import socket
import weakref
import subprocess
import threading
import string
import secrets
from io import BytesIO
#pip install adbutils zeroconf qrcode
import adbutils
from adbutils import adb
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
from adbutils.errors import AdbError,AdbTimeout
import qrcode

def create_passwd():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(8))

def adb_start_server():
    subprocess.run('adb start-server')

class MDnsListener(ServiceListener):
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            AdbMDns.update(info)
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            AdbMDns.remove(info)
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            AdbMDns.add(info)
class AdbMDnsError(Exception):
    pass
class AdbMDns:
    _devices={}
    started=False
    type="_adb-tls-connect._tcp.local."
    # type='_adb._tcp.local.'
    lock = threading.Lock()
    zeroconf=None
    finalize=None
    @staticmethod
    def start():
        if AdbMDns.started==False:
            AdbMDns.zeroconf = Zeroconf()
            ServiceBrowser(AdbMDns.zeroconf, AdbMDns.type, MDnsListener())
            def atexit(zeroconf):
                zeroconf.close()
            AdbMDns.finalize = weakref.finalize(AdbMDns.zeroconf, atexit, AdbMDns.zeroconf)
            AdbMDns.started=True
    @staticmethod
    def update(info):
        info=AdbMDns._info(info)
        AdbMDns.remove(info)
        AdbMDns.add(info)
        # AdbMDns.print()
    @staticmethod
    def add(info):
        if not isinstance(info,tuple):
            info=AdbMDns._info(info)
        ip,serialno=info
        AdbMDns.lock.acquire()
        AdbMDns._devices[serialno]=ip
        AdbMDns.lock.release()
        # AdbMDns.print()
    @staticmethod
    def remove(info):
        if not isinstance(info,tuple):
            info=AdbMDns._info(info)
        ip,serialno=info
        ip,port=ip.split(':')
        AdbMDns.lock.acquire()
        for serialno_,ip_ in tuple(AdbMDns._devices.items()):
            ip_,port=ip_.split(':')
            if ip_==ip or serialno_==serialno:
                del AdbMDns._devices[serialno_]
        AdbMDns.lock.release()
        # AdbMDns.print()
    @staticmethod
    def _info(info):
        ip = f'{socket.inet_ntoa(info.addresses[0])}:{info.port}'
        if (m:=re.match(fr'adb\-(\w+)\-\w+\.{AdbMDns.type}',info.name)):
            serialno = m.group(1)
        else:
            serialno = ''
            raise AdbMDnsError(f'AdbMDns not match: {info.name}')
        return ip,serialno
    @staticmethod
    def devices():
        AdbMDns.lock.acquire()
        d=tuple(AdbMDns._devices.items())
        AdbMDns.lock.release()
        return d
    @staticmethod
    def print():
        pprint.pprint(['mDns',AdbMDns.devices()])

def adb_devices():
    serialnos=[]
    serials=[]
    ds=[]
    key_serialno='ro.serialno'
    # key_guid='persist.adb.wifi.guid' #could be ''
    def devices():
        yield from adb_devices.ds
        a = adb.device_list()
        for d in adb.device_list():
            serials.append(d.serial)
            yield d
        for serialno,ip in AdbMDns.devices():
            if ip not in serials and serialno not in serialnos:
                output = adb.connect(ip)
                if re.match(f'^(already )?connected to {ip}',output):
                    d = adb.device(serial=ip)
                    if serialno:
                        d._properties[key_serialno]=serialno
                    serials.append(ip)
                    yield d
                else:
                    print(output)
                    # cannot connect to 10.1.1.1:100: No connection could be made because the target machine actively refused it. (10061)
    def devices_available():
        for d in devices():
            if d and d not in ds:
                try:
                    model = d.shell('getprop ro.product.model') or '' #check avaliable
                    serialno = d.prop.get(key_serialno, cache=True) 
                    if not serialno:
                        raise AdbMDnsError(f'serialno {serialno}')
                except:
                    continue
                if serialno not in serialnos:
                    if serialno: serialnos.append(serialno)
                    ds.append(d)
                    yield d,(serialno,model)
    try:
        yield from devices_available()
        adb_devices.ds=ds
    except GeneratorExit:
        adb_devices.ds=ds
        return
adb_devices.ds=[]

class PairListener(ServiceListener):
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        AdbPair.pair(info)

class AdbPair:
    name='name'
    passwd=create_passwd()
    type="_adb-tls-pairing._tcp.local."
    def __init__(self):
        self.start_pair()
        self.qrcode()
    def start_pair(self):
        self.zeroconf = Zeroconf()
        ServiceBrowser(self.zeroconf, AdbPair.type, PairListener())
    def qrcode(self):
        s=f'WIFI:T:ADB;S:{AdbPair.name};P:{AdbPair.passwd};;'
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=2)
        qr.add_data(s)
        qr.print_ascii(tty=True)
        self.img = qr.make_image(fill_color="black", back_color="white")
    @property
    def img_pil(self):
        return self.img.convert('RGB')
    @property
    def img_cv(self):
        import cv2 as cv
        import numpy as np
        return cv.cvtColor(np.array(self.img_pil), cv.COLOR_RGB2BGR)
    @property
    def img_buf(self):
        buf = BytesIO()     
        self.img.save(buf, "PNG")
        return buf
    @staticmethod
    def pair(info):
        ip=AdbPair._info(info)
        subprocess.run(f'adb pair {ip} {AdbPair.passwd}')
    @staticmethod
    def _info(info):
        ip = f'{socket.inet_ntoa(info.addresses[0])}:{info.port}'
        return ip
    def stop_pair(self):
        self.zeroconf.close()

def ui_qt():
    from PyQt6 import QtWidgets, QtGui, QtCore
    class UiQrCode(QtWidgets.QDialog):
        def __init__(self,parent=None):
            super().__init__(parent)
            self.setWindowTitle(f"adb pair")
            self.pair=adbdevices.AdbPair()
            img = QtGui.QPixmap()
            img.loadFromData(self.pair.img_buf.getvalue(), "PNG")
            label=QtWidgets.QLabel()
            vlayout = QtWidgets.QVBoxLayout()
            label.setPixmap(img)
            self.setLayout(vlayout)
            vlayout.addWidget(label)
        def closeEvent(self,event):
            self.pair.stop_pair()
    app = QtWidgets.QApplication([])
    root = UiQrCode()
    root.show()
    ret = app.exec()
def ui_cv():
    import cv2 as cv
    pair=adbdevices.AdbPair()
    cv.imshow('pair',pair.img_cv)
    cv.waitKey(0) 
    cv.destroyAllWindows()
    pair.stop_pair()

AdbMDns.start()
adb_start_server()

import sys
adbdevices = sys.modules[__name__]
# import adbdevices
if __name__ == "__main__":
    ui_qt()
    ui_cv()
    while True:
        try:
            for d,(serialno,model) in adbdevices.adb_devices():
                print(d.serial,(serialno,model))
                print(d.shell('date'))
        except (adbdevices.AdbError,adbdevices.AdbTimeout) as e:
            adbdevices.adb_start_server()
            print('adbdevices',type(e),e)
        except Exception as e:
            print('adbdevices',type(e),e)
        input()


import sys
import os
import datetime
import json
import pprint
import re
import time
try:
    import mods.myprocess1 as myprocess
except:
    import myprocess1 as myprocess
    
adb = 'adb'
_tmpdir='/data/local/tmp/'
prjdir = os.path.dirname(os.path.abspath(__file__))+'/'
prjtmp=f'{prjdir}tmp/'

class AndroidDev():
    devices={}
    mdns={}
    adb_env = os.environ.copy()
    def __init__(self, device_id='', adb_tcpip=True):
        self.device_id=device_id.strip()
        AndroidDev.adb_env['ADB_MDNS_OPENSCREEN']='1'
        self.my_env = AndroidDev.adb_env
        ADB_MDNS_OPENSCREEN=1
        self.set_env('ANDROID_SERIAL','')
        self.connect(adb_tcpip=adb_tcpip)
        
    def runs(self,cmds,hidecmd=False, print_out=False, break_err=True,shell=False,print_err=True,run=myprocess.run):
        '''result=self.runs(cmds,hidecmd=False, print_out=False, break_err=True)'''
        # hidecmd=False
        # print_out=True
        result=myprocess.result_empty
        for cmd in cmds.splitlines():
            cmd = cmd.strip()
            if cmd.startswith('#') or not cmd:
                continue
            if self:
                env = self.my_env
            else:
                env = AndroidDev.adb_env
            result = run(cmd,shell=False,hidecmd=hidecmd,env=env)
            if print_out:
                myprocess.print_run(result,print_out=True,print_err=True)
            if result.returncode!=0:
                if not print_out:
                    if print_err:
                        myprocess.print_run(result,print_out=True,print_err=True)
                if break_err:
                    break
        return result
        
    def pair(android_ip_pair):
        cmds=f"""
        {adb} pair {android_ip_pair}
        """
        result=AndroidDev.runs(None,cmds,hidecmd=False, print_out=True, break_err=True)
        return result.returncode
        
    def set_env(self,key,value):
        self.my_env[key]=value
        
    def wait_connect(self,retry=3):
        result=myprocess.result('','1')
        for i in range(retry,0,-1):
            print(f'\rwait_connect {i}  ',end='')
            cmd=f"""{adb} shell echo 0"""
            result=myprocess.run(cmd,hidecmd=True,env=self.my_env)
            if result.returncode==0:
                print()
                return True
            time.sleep(1)
        print()
            
    def adb_kill():
        AndroidDev.adb_env['ADB_MDNS_OPENSCREEN']='1'
        cmd=f"""{adb} kill-server"""
        result = AndroidDev.runs(None, cmd,hidecmd=True, print_out=False, break_err=False)
        
    def adb_mdns(retry=3):
        AndroidDev.adb_env['ADB_MDNS_OPENSCREEN']='1'
        re_adb_mdns=r'''^(?P<device_id>.*?)\s+(?P<device_mdns>.*?)\s+(?P<device_ip>.*)'''
        cmd=f"""
        {adb} start-server
        {adb} start-server
        {adb} start-server
        {adb} mdns services
        {adb} mdns services
        {adb} mdns services
        """
        result = AndroidDev.runs(None, cmd,hidecmd=True, print_out=False, break_err=False)
        if result.returncode!=0:
            myprocess.print_run(result,print_out=True,print_err=True)
        else:
            for line in result.stdout.splitlines():
                if line.startswith('List of discovered mdns services'): continue
                mobj = re.match(re_adb_mdns, line)
                if mobj:
                    AndroidDev.mdns.setdefault(mobj.group('device_id'), {})['device_ip'] = mobj.group('device_ip')
                    AndroidDev.mdns.setdefault(mobj.group('device_id'), {})['device_mdns'] = mobj.group('device_mdns')
        if AndroidDev.mdns:
            return AndroidDev.mdns
        else:
            if retry>0:
                time.sleep(0.5)
                if AndroidDev.__dict__.get('killed') != True:
                    AndroidDev.killed=True
                    cmd=f"""{adb} kill-server"""
                    result = AndroidDev.runs(None, cmd,hidecmd=True, print_out=False, break_err=True)
                return AndroidDev.adb_mdns(retry-1)
            else:
                return {}

    def adb_devices():
        re_adb_devices=r'''^(?P<device_id>.*?)\s+(?P<status>.*?)\s+(?P<info>.*)'''
        cmd=f"""{adb} devices -l"""
        result = AndroidDev.runs(None,cmd,hidecmd=True)
        if result.returncode!=0:
            myprocess.print_run(result,print_out=True,print_err=True)
        else:
            for line in result.stdout.splitlines():
                if line.startswith('List of devices attached'): continue
                mobj = re.match(re_adb_devices, line)
                if mobj:
                    # mobj.group('device_id')
                    # mobj.group('status')
                    # mobj.group('info')
                    AndroidDev.devices.setdefault(mobj.group('device_id'), {})['status'] = mobj.group('status')
                    AndroidDev.devices.setdefault(mobj.group('device_id'), {})['info'] = mobj.group('info')
        return AndroidDev.devices
    
    def connected(device_id):
        if AndroidDev.adb_devices().get(device_id,{}).get('status') == 'device':
            return True

    def connect(self,adb_tcpip=True):
        print(f'connect {self.device_id}')
        if not self.device_id:
            self.set_env('ANDROID_SERIAL','')
            
            cmds=f'''{adb} shell echo test'''
            result=self.runs(cmds,hidecmd=True, print_out=False, break_err=True)
            devices = AndroidDev.adb_devices()
            if result.returncode!=0:
                if 'adb.exe: more than one device/emulator' in result.stderr:
                    pprint.pprint(devices)
                raise Exception([result.stderr,result.stdout])
            else:
                self.device_id = next(iter(devices))

        self.set_env('ANDROID_SERIAL',self.device_id)
        def get_ip_port(device_id):
            from ipaddress import ip_address
            ip,port,*_ = device_id.rsplit(':',maxsplit=1) + ['5555']
            try:
                ip_address(ip)
                return ip,port
            except:
                return None,None
        ip,port = get_ip_port(self.device_id)
        
        def _connect():
            if ip:
                cmds=f"""{adb} connect {self.device_id}"""
                result =  self.runs(cmds,hidecmd=False, print_out=True, break_err=True)
                if 'A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond. (10060)' in result.stdout:
                    raise Exception([result.stderr,result.stdout])
                self.wait_connect(1)
                return result

        if ip:
            result = _connect()
            if adb_tcpip and (not f'already connected to {self.device_id}' in result.stdout):
                cmds=f"""{adb} tcpip {port}"""
                result = self.runs(cmds,hidecmd=True)
                result = _connect()

        cmds=f"""{adb} -s {self.device_id} root"""
        result = self.runs(cmds,hidecmd=True)
        if result.returncode!=0:
            print(result.stderr)
            if ip:
                result = _connect()

        if AndroidDev.connected(self.device_id):
            print(f'''connected: {self.my_env['ANDROID_SERIAL']} {AndroidDev.devices.get(self.device_id,{}).get('info')}''')
            return self.device_id

    def screencap(self,name='screen',name1=None,open_img=True):
        if name1:
            png = name1
        else:
            png = f'{prjtmp}{name}.png'
        _png = f'{_tmpdir}screen.png'
        cmds=f"""
        # {adb} shell screencap --help
        {adb} shell rm -f {_png}
        {adb} shell screencap -p {_png}
        {adb} pull {_png} {png}
        {'' if open_img else '#'} {myprocess.cmd_ps(png)}
        """
        result=self.runs(cmds,hidecmd=True, print_out=False, break_err=True,shell=open_img)
        if result.returncode==0:
            return png

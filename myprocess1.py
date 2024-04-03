import subprocess
import sys
import os
my_env=None

# powershell = 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
powershell = 'C:/Program Files/PowerShell/7/pwsh.exe'
def cmd_ps(cmd):
    return f'''"{powershell}" -command {cmd}'''

result_empty=subprocess.CompletedProcess(args='', returncode=0, stdout='', stderr='')
def result(cmd,e):
    if isinstance(e,BaseException):
        return subprocess.CompletedProcess(args=cmd, returncode=type(e), stdout=e.args, stderr=e)
    else:
        return subprocess.CompletedProcess(args=cmd, returncode=type(e), stdout=e, stderr=e)

def run(cmd='',shell=False,hidecmd=False,env=my_env):
    '''
        # capture_output=True
        import myprocess
        result=myprocess.result_empty
        result = myprocess.run(cmd)
        myprocess.print_run(result)
'''
    cmd = cmd.strip()
    if (not cmd) or cmd.startswith('#'):
        return result_empty
    if not hidecmd:
        print(f'>{cmd}')
    '''https://docs.python.org/3/library/subprocess.html '''
    # stdin=None, input=None, stdout=None, stderr=None, capture_output=False, shell=False, cwd=None, timeout=None, check=False, encoding=None, errors=None, text=None, env=None, universal_newlines=None
    try:
        r = subprocess.run(cmd, capture_output=True, shell=shell, encoding='utf-8', errors='replace', env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        r.hidecmd=hidecmd
        return r
    except Exception as e:
        return result(cmd,e)

def run0(cmd='',shell=False,hidecmd=False,env=my_env):
    '''
        # capture_output=False
        import myprocess
        result=myprocess.result_empty
        result = myprocess.run0(cmd)
        myprocess.print_run(result)
'''
    cmd = cmd.strip()
    if (not cmd) or cmd.startswith('#'):
        return result_empty
    if not hidecmd:
        print(f'>{cmd}')
    my_env = os.environ.copy()
    my_env['COMSPEC'] = r'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
    '''https://docs.python.org/3/library/subprocess.html '''
    try:
        r = subprocess.run(cmd, shell=shell, env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        r.hidecmd=hidecmd
        return r
    except Exception as e:
        return result(cmd,e)

def runw(cmd,shell=False,hidecmd=False,env=my_env):
    '''
        import myprocess
        result=myprocess.result_empty
        mpopen = myprocess.runw(cmd)
        result = myprocess.wait_runw(cmd,mpopen)
        myprocess.print_run(result)

    '''
    cmd = cmd.strip()
    if (not cmd) or cmd.startswith('#'):
        return result_empty
    if not hidecmd:
        print(f'1>{cmd}')
    try:
        mpopen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, close_fds=False, env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        # mpopen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, encoding='utf-8', errors='replace', close_fds=False, env=env)
        return mpopen
    except Exception as e:
        return result(cmd,e)

def wait_runw(cmd,mpopen,print_out=True,print_err=True,hidecmd=False):
    cmd=cmd.strip()
    if isinstance(mpopen,subprocess.Popen):
        _out=b''
        _err=b''
        # _out=''
        # _err=''
        # for c in iter(mpopen.stdout.readline, b''):
        for c in iter(lambda: mpopen.stdout.read(1), b""):
        # for c in iter(lambda: mpopen.stdout.read(1), ""):
            _out+=c
            if print_out: 
                sys.stdout.buffer.write(c)
                if c<=b'~' and c>=b' ':
                # if c<=b'\x7e' and c>=b'\x20':
                    sys.stdout.buffer.flush()
                # sys.stdout.write(c)
                # sys.stdout.flush()
                # print(c,end='')
        # for c in iter(mpopen.stderr.readline, b''):
        for c in iter(lambda: mpopen.stderr.read(1), b""):
        # for c in iter(lambda: mpopen.stderr.read(1), ""):
            _err+=c
            if print_err: 
                sys.stderr.buffer.write(c)
                if c<=b'~' and c>=b' ':
                    sys.stderr.buffer.flush()
                # sys.stderr.write(c)
                # sys.stderr.flush()
                # print(c,end='')
        if not hidecmd:
            print(f'2>{cmd}')
        returncode=mpopen.wait()
        _out=_out.decode(encoding='utf-8', errors='replace')
        _err=_err.decode(encoding='utf-8', errors='replace')
        return subprocess.CompletedProcess(args=cmd, returncode=returncode, stdout=_out, stderr=_err)
    elif isinstance(mpopen,subprocess.CompletedProcess):
        return mpopen
    else:
        return result_empty

def print_run(result,print_out=True,print_err=True,args=False,end=''):
    printed=False
    if isinstance(result,subprocess.CompletedProcess):
        if result.args!='':
            if result:
                if (result.returncode!=0 and hasattr(result,'hidecmd') and result.hidecmd==True) or (args and result.args):
                    printed=True
                    print(f'[args] {result.args}')
                if result.returncode!=0:
                    printed=True
                    print(f'[return] {result.returncode}')
                if print_out and result.stdout:
                    printed=True
                    print(f'[stdout] {result.stdout}',end=end)
                if print_err and result.stderr:
                    printed=True
                    print(f'[stderr] {result.stderr}',end=end)
                # if printed!=True:
                    # print(f'[result] {result}')
            else:
                print(f'[result] type:{type(result)} value={result}')
    else:
        print(f'[result] type:{type(result)} value={result}')

import shelve
import weakref
import os
import sys
import inspect

def shelve_cache(cache_file=None):
    '''
        @shelve_cache('D:/CS/PythonModules/cache/ydl.downloaded.status.cache')
        def download_status(ytid,status=download_status_unknown):
            return status

        def set_download_status(ytid,status=download_status_unknown):
            return download_status(ytid,usecache=False,status=status)
    '''
    caller_filename, caller_fileext = os.path.splitext(os.path.basename(inspect.stack()[1].filename))
    app_dir = os.path.dirname(sys.argv[0])
    def decorator(func):
        def _func(key,*arg,usecache=True,**args):
            if _func.debug:
                print(f'cache_file:{_func.cache_file} {_func.func.__name__}{(key,arg,usecache,args)}')
            if (not usecache) or (key not in _func.d):
                res = _func.func(key,*arg,**args)
                _func.d[key] = res
                return res
            else:
                try:
                    if _func.debug:
                        print(f'\treturn {_func.d[key]}')
                    return _func.d[key]
                except Exception as e:
                    try: _func.d[key]=None #might fix a truncated save file
                    except: pass
                    try: del _func.d[key] #might fix a truncated save file
                    except: pass
                    print('Exception shelve_cache',key,e.__class__.__name__,e)
                    res = _func.func(key,*arg,**args)
                    _func.d[key] = res
                    return res
        def set_file(file=None):
            if file==None:
                file = os.path.abspath(os.path.join(
                            app_dir, 'cache', f'{caller_filename}.{func.__name__}.cache'))
                
            if _func.debug:
                print(f'set_file {file}')
            _func.cache_file=file
            if getattr(_func, 'd', None):
                _func.finalize()
            os.makedirs(os.path.dirname(file), exist_ok=True)
            _func.d = shelve.open(file)
            def atexit(d):
                if _func.debug:
                    print(f'save {d}')
                d.close()
            _func.finalize = weakref.finalize(_func.d, atexit, _func.d)
        def sync():
            if getattr(_func, 'd', None):
                if _func.debug:
                    print(f'sync {_func.d}')
                _func.d.sync()
        _func.debug=False
        _func.func=func
        _func.set_file = set_file
        _func.sync = sync
        set_file(cache_file)
        return _func
    return decorator

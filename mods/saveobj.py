
def savestr(cachefile,webpage):
    with open(cachefile,'w') as file:
        file.write(webpage)

def loadstr(cachefile):
    with open(cachefile,'r') as file:
        return file.read()

class CacheStr:
    def __init__(self, file):
        self.file=file
        self.data=''
        
    def save(self,s):
        with open(self.file,'w') as file:
            file.write(s)

    def load(self):
        with open(self.file,'r') as file:
            self.data=file.read()
            return self.data
    def __str__(self):
        return self.data

import json
def save_json(file,data):
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

def load_json(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        pass
# if __name__ == "__main__":
    # s=''
    # saveobj.savestr(cachefile,s)
    # s = saveobj.loadstr(cachefile)

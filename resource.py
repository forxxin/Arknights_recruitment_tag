
from functools import cache
import urllib.request
import os
import requests
import json
import shutil
import urllib.parse

try:
    from shelve_cache import shelve_cache
except:
    from mods.shelve_cache import shelve_cache
try:
    from saveobj import save_json,load_json
except:
    from mods.saveobj import save_json,load_json

app_path = os.path.dirname(__file__)
os.chdir(app_path)

colors={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }
def lang2(lang):
    return {'en':'en_US','ja':'ja_JP','ko':'ko_KR','zh':'zh_CN','ch':'zh_TW',}[lang]
def rarity_int(rarity_str):
    return int(rarity_str[-1:])

def download(name,url,update=False,folder='tmp'):
    file = os.path.abspath(os.path.join(folder,name))
    if not os.path.isfile(file) or update==True:
        os.makedirs(os.path.dirname(file), exist_ok=True)
        print(f'downloading {url} -o {file}')
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if content_type.startswith('application/json'):
                    data = response.json()
                    save_json(file,data)
                else:
                    response.raw.decode_content = True
                    with open(file, 'wb') as out_file:
                        shutil.copyfileobj(response.raw, out_file)
        except Exception as e:
            print('download',type(e),e)
            return None
            # urllib.request.urlretrieve(url, file)
    return file

@cache
def json_tl(name):
    ''' https://github.com/Aceship/AN-EN-Tags/ '''
    url = f'https://github.com/Aceship/AN-EN-Tags/raw/master/json/tl-{name}.json'
    file = download(f'Aceship/tl-{name}.json',url)
    data = load_json(file)
    if name=='akhr':
        return {item.get('id'):item for item in data}
    elif name=='type':
        return {item.get('type_data'):item for item in data}
    else:
        return data

class GameData:
    ''' https://github.com/Kengxxiao/ArknightsGameData_YoStar '''
    @staticmethod
    @cache
    def url_base(lang): #story_review
        if lang=='zh_CN':
            return f'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/'
        else:
            return f'https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData_YoStar/main/'
        # return f'https://github.com/Aceship/AN-EN-Tags/raw/master/json/gamedata/'

    @staticmethod
    @cache
    def json_table(name, lang='en_US'): #story_review
        """ resource.GameData.json_table('item', lang='en_US') """
        url = urllib.parse.urljoin(GameData.url_base(lang), f'{lang}/gamedata/excel/{name}_table.json')
        file = download(f'gamedata/{name}_table_{lang}.json',url)
        return load_json(file)
    @staticmethod
    @cache
    def json_data(name, lang='en_US'):
        if name=='gamedata':
            url = urllib.parse.urljoin(GameData.url_base(lang), f'{lang}/gamedata/excel/{name}_const.json')
            file = download(f'gamedata/{name}_const_{lang}.json',url)
        else:
            url = urllib.parse.urljoin(GameData.url_base(lang), f'{lang}/gamedata/excel/{name}_data.json')
            file = download(f'gamedata/{name}_data_{lang}.json',url)
        return load_json(file)

class Img:
    ''' https://github.com/yuanyan3060/ArknightsGameResource '''
    base = 'https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/'
    item_table=GameData.json_table('item', lang='en_US')
    @staticmethod
    @cache
    def img(key,name):
        name = name.format(k=key)
        url = urllib.parse.urljoin(Img.base, name)
        return download(f'img/{name}',url,folder='resource')
    @staticmethod
    @cache
    def avatar(charid):
        return Img.img(charid,'avatar/{k}.png')
    @staticmethod
    @cache
    def avatar2(charid):
        return Img.img(charid,'avatar/{k}_2.png')
    @staticmethod
    @cache
    def portrait(charid):
        return Img.img(charid,'portrait/{k}_1.png')
    @staticmethod
    @cache
    def portrait2(charid):
        return Img.img(charid,'portrait/{k}_2.png')
    @staticmethod
    @cache
    def dorm_skill(skillIcon):
        return Img.img(skillIcon,'building_skill/{k}.png')
    @staticmethod
    @cache
    def item(itemid):
        iconId = Img.item_table.get('items',{}).get(itemid,{}).get('iconId','') or ''
        return Img.img(iconId,'item/{k}.png')

# class ItemImg:
    # url_base = "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/item/"
    # item_table=GameData.json_table('item', lang='en_US')
    # @staticmethod
    # @cache
    # def img(itemid):
        # iconId = ItemImg.item_table.get('items',{}).get(itemid,{}).get('iconId','') or ''
        # url_img = urllib.parse.urljoin(ItemImg.url_base, f'{iconId}.png')
        # return download(f'img/item/{itemid}.png',url_img)

def penguin_stats(server='US',update=False):
    @cache
    def _penguin_stats(name,query,server=''):
        penguin_api = 'https://penguin-stats.io/PenguinStats/api/v2/'
        url = urllib.parse.urljoin(penguin_api, query)
        file= download(f'./PenguinStats/{name}{server}.json',url)
        return load_json(file)
    stages = _penguin_stats('stages',f'stages?server={server}',server)
    items = _penguin_stats('items','items')
    stageitems = _penguin_stats('stageitems','result/matrix?show_closed_zone=false')
    stageitems_all = _penguin_stats('stageitems_all','result/matrix?show_closed_zone=true')
    formulas = _penguin_stats('formulas','formula')
    return stages,items,stageitems,formulas

if __name__ == "__main__":
    url1='https://penguin-stats.io/PenguinStats/api/v2/formula'
    url2 = f'https://github.com/Aceship/AN-EN-Tags/raw/master/json/tl-akhr.json'
    file1='./resource.test1.json'
    file2='./resource.test2.json'


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

def download(name,url,update=False):
    file = os.path.abspath(os.path.join('./resource/',name))
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

class CharImg:
    ''' https://github.com/yuanyan3060/ArknightsGameResource '''
    url_base = 'https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/'
    name_avatar='avatar/{charid}.png'
    name_avatar2='avatar/{charid}_2.png'
    name_portrait='portrait/{charid}_1.png'
    name_portrait2='portrait/{charid}_2.png'
    @staticmethod
    @cache
    def img(charid,name_url):
        name = name_url.format(charid=charid)
        url = urllib.parse.urljoin(CharImg.url_base, name)
        return download(f'img/{name}',url)
    @staticmethod
    @cache
    def avatar(charid):
        return CharImg.img(charid,'avatar/{charid}.png')
    @staticmethod
    @cache
    def avatar2(charid):
        return CharImg.img(charid,'avatar/{charid}_2.png')
    @staticmethod
    @cache
    def portrait(charid):
        return CharImg.img(charid,'portrait/{charid}_1.png')
    @staticmethod
    @cache
    def portrait2(charid):
        return CharImg.img(charid,'portrait/{charid}_2.png')

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

class ItemImg:
    url_base = "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/item/"
    item_table=GameData.json_table('item', lang='en_US')
    @staticmethod
    @cache
    def img(itemid):
        iconId = ItemImg.item_table.get('items',{}).get(itemid,{}).get('iconId','') or ''
        url_img = urllib.parse.urljoin(ItemImg.url_base, f'{iconId}.png')
        # print(itemid,iconId)
        return download(f'img/item/{itemid}.png',url_img)

class ItemImg1:
    ''' https://github.com/Aceship/Arknight-Images '''
    url_base = "https://raw.githubusercontent.com/Aceship/Arknight-Images/main/material/"
    img_data={'30011': ('bg/item-1.png', '30.png'), '30012': ('bg/item-2.png', '24.png'), '30013': ('bg/item-3.png', '18.png'), '30014': ('bg/item-4.png', '12.png'), '30061': ('bg/item-1.png', '25.png'), '30062': ('bg/item-2.png', '19.png'), '30063': ('bg/item-3.png', '13.png'), '30064': ('bg/item-4.png', '7.png'), '30031': ('bg/item-1.png', '28.png'), '30032': ('bg/item-2.png', '22.png'), '30033': ('bg/item-3.png', '16.png'), '30034': ('bg/item-4.png', '10.png'), '30021': ('bg/item-1.png', '29.png'), '30022': ('bg/item-2.png', '23.png'), '30023': ('bg/item-3.png', '17.png'), '30024': ('bg/item-4.png', '11.png'), '30041': ('bg/item-1.png', '27.png'), '30042': ('bg/item-2.png', '21.png'), '30043': ('bg/item-3.png', '15.png'), '30044': ('bg/item-4.png', '9.png'), '30051': ('bg/item-1.png', '26.png'), '30052': ('bg/item-2.png', '20.png'), '30053': ('bg/item-3.png', '14.png'), '30054': ('bg/item-4.png', '8.png'), '30073': ('bg/item-3.png', '31.png'), '30074': ('bg/item-4.png', '6.png'), '30083': ('bg/item-3.png', '33.png'), '30084': ('bg/item-4.png', '5.png'), '30093': ('bg/item-3.png', '32.png'), '30094': ('bg/item-4.png', '4.png'), '30103': ('bg/item-3.png', '34.png'), '30104': ('bg/item-4.png', '3.png'), '31013': ('bg/item-3.png', '63.png'), '31014': ('bg/item-4.png', '64.png'), '31023': ('bg/item-3.png', '61.png'), '31024': ('bg/item-4.png', '62.png'), '30115': ('bg/item-5.png', '2.png'), '30125': ('bg/item-5.png', '1.png'), '30135': ('bg/item-5.png', '0.png'), '31033': ('bg/item-3.png', '67.png'), '31034': ('bg/item-4.png', '66.png')}
    @staticmethod
    @cache
    def imgs():
        res={}
        for itemid,(bg,img) in ItemImg1.img_data.items():
            url_bg = urllib.parse.urljoin(ItemImg1.url_base, bg)
            url_img = urllib.parse.urljoin(ItemImg1.url_base, img)
            res[itemid]=[download(f'img/{bg}',url_bg), download(f'img/item/{itemid}.png',url_img)]
        return res
    @staticmethod
    @cache
    def img(itemid):
        return ItemImg1.imgs().get(itemid) or []

if __name__ == "__main__":
    url1='https://penguin-stats.io/PenguinStats/api/v2/formula'
    url2 = f'https://github.com/Aceship/AN-EN-Tags/raw/master/json/tl-akhr.json'
    file1='./resource.test1.json'
    file2='./resource.test2.json'

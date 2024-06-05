import test
import os
from functools import cache

import requests
from bs4 import BeautifulSoup
try:
    from shelve_cache import shelve_cache
except:
    from mods.shelve_cache import shelve_cache

app_path = os.path.dirname(__file__)
os.chdir(app_path)

@shelve_cache('./tmp/tier.requests_get.cache')
def requests_get(url):
    return requests.get(url).text

@cache
def char_tier_gamepress():
    ''' https://gamepress.gg/arknights/tier-list/arknights-operator-tier-list '''
    url = 'https://gamepress.gg/arknights/tier-list/arknights-operator-tier-list'
    text=requests_get(url)
    soup = BeautifulSoup(text,"html.parser")
    def tiers2int():
        t=[]
        # for obj in soup.find_all('div', class_='clearfix text-formatted field field--name-field-text field--type-text-long field--label-hidden field__item'):
            # for x in obj.find_all('tr'):
                # for y in x.find_all('td'):
                    # if y.text=='Tier':
                        # t=[]
                    # else:
                        # t.append(y.text)
                    # break
        # print(t) #['EX', 'S', 'A', 'B', 'C', 'D',]
        t=['EX', 'S', 'A', 'B', 'C', 'D','E']
        t1=[]
        for i in t:
            if i in ['EX']:
                t1.append(i)
            else:
                t1.append(i+'+')
                t1.append(i)
                t1.append(i+'-')
        # print(t1)
        return {t1:i+1 for i,t1 in enumerate(t1)}
    tiers = tiers2int()
    # print(tiers)
    res={}
    tier=0
    for obj in soup.find_all('div', class_='list-main'):
        for x in obj.find_all(['td','div'], class_=['tier-cell-label','operator-title']):
            if x.name=='td':
                tier=x.text
            elif x.name=='div':
                charname=x.text
                if charname=='Rosa (Poca)':
                    charname='Rosa'
                res[charname]=tiers[tier]
    return res #{name:int}

def char_tier():
    try:
        return char_tier_gamepress()
    except Exception as e:
        print('char_tier_gamepress',type(e),e)
        return {'Mostima': 4, 'Dusk': 5, 'Leonhardt': 6, 'Santalla': 8, 'Gitano': 9, 'Lava the Purgatory': 9, 'Greyy': 11, 'Skyfire': 11, 'Lava': 12, '12F': 15, 'Ifrit': 3, 'Corroserum': 11, 'Passenger': 3, 'Leizi': 6, 'Astgenne': 6, 'Pudding': 9, 'Ebenholz': 4, 'Indigo': 8, 'Harmonie': 8, 'Delphine': 9, 'Iris': 9, 'Goldenglow': 2, 'Rockrock': 5, 'Kjera': 5, 'Click': 6, 'Minimalist': 7, 'Lin': 3, 'Carnelian': 5, 'Beeswax': 6, 'Mint': 6, 'Diamante': 9, 'Eyjafjalla': 2, 'Ceobe': 3, "Ho'olheyak": 5, 'Absinthe': 6, 'Amiya': 6, 'Qanipalaat': 8, 'Haze': 9, 'Tomimi': 11, 'Steward': 12, 'Nightmare': 12, 'Durin': 15, 'Shalem': 7, 'Asbestos': 8, 'Czerny': 9, 'Dur-nar': 9, 'Eunectes': 5, 'Aurora': 8, 'Cement': 10, 'Penance': 2, 'Mudrock': 2, 'Vulcan': 9, 'Horn': 2, 'Ashlock': 6, 'Firewhistle': 6, 'Saria': 2, 'Blemishine': 4, 'Bassline': 5, 'Nearl': 5, 'Gummy': 8, 'Hung': 9, 'Spot': 12, 'Hoshiguma': 3, 'Nian': 3, 'Croissant': 5, 'Cuora': 7, 'Heavyrain': 7, 'Bubble': 7, 'Bison': 8, 'Matterhorn': 10, 'Cardigan': 12, 'Beagle': 12, 'Friston-3': 13, 'Noir Corne': 14, 'Jessica the Liberated': 3, 'Liskarm': 6, 'Blitz': 7, 'Gavial the Invincible': 2, 'Blaze': 3, 'Specter': 3, 'Broca': 6, 'Estelle': 9, 'Savage': 9, 'Popukar': 12, 'Surtr': 1, 'Viviana': 4, 'Amiya (Guard)': 5, 'Astesia': 8, 'Mousse': 8, 'Sideroca': 9, 'Mountain': 2, 'Chongyue': 3, 'Dagda': 7, 'Indra': 8, 'Flint': 9, 'Beehunter': 10, 'Jackie': 12, 'Hoederer': 4, 'Quartz': 12, 'Wind Chimes': 13, 'Irene': 3, "Ch'en": 4, 'Bibeak': 5, 'Cutter': 6, 'Tachanka': 7, 'Nearl the Radiant Knight': 2, 'Skadi': 4, 'Lessing': 6, 'Franka': 8, 'Morgan': 9, 'Matoimaru': 9, 'Flamebringer': 9, 'Conviction': 10, 'Melantha': 10, 'Castle-3': 12, 'Hellagur': 5, 'Akafuyu': 7, 'Rathalos S Noir Corne': 7, 'Utage': 7, 'Młynar': 1, 'Tequila': 5, 'SilverAsh': 2, 'Thorns': 3, 'Qiubai': 3, 'Lappland': 5, 'Arene': 7, 'Luo Xiaohei': 7, 'Ayerscarpe': 7, 'Midnight': 11, 'Frostleaf': 13, 'Executor the Ex Foedere': 2, 'La Pluma': 4, 'Highmore': 6, 'Humus': 9, 'Pallas': 4, 'Whislash': 10, 'Swire': 12, 'Bryophyta': 13, 'Dobermann': 13, 'Nightingale': 2, 'Ptilopsis': 3, 'Perfumer': 6, 'Breeze': 7, 'Paprika': 9, 'Reed the Flame Shadow': 2, 'Hibiscus the Purifier': 6, 'Vendela': 9, "Kal'tsit": 2, 'Warfarin': 3, 'Shining': 5, 'Sussurro': 5, 'Silence': 6, 'Tuye': 7, 'Folinic': 8, 'Myrrh': 9, 'Gavial': 10, 'Ansel': 11, 'Lancet-2': 12, 'Hibiscus': 12, 'Eyjafjalla the Hvít Aska': 2, 'Honeyberry': 5, 'Mulberry': 5, 'Chestnut': 10, 'Lumen': 4, 'Whisperain': 6, 'Purestream': 6, 'Ceylon': 11, 'Rosmontis': 4, 'Greyy the Lightningbearer': 7, 'Terra Research Commission': 11, 'Exusiai': 3, 'Ash': 3, 'Archetto': 4, 'April': 5, 'Kroos the Keen Glint': 6, 'Blue Poison': 6, 'Platinum': 6, 'GreyThroat': 7, 'Insider': 7, 'May': 8, 'Vermeil': 9, 'Meteor': 10, 'Jessica': 10, 'Kroos': 11, 'Adnachiel': 13, 'Rangers': 15, "'Justice Knight'": 18, 'Fiammetta': 3, 'W': 4, 'Meteorite': 7, 'Jieyun': 7, 'Shirayuki': 8, 'Sesa': 9, 'Catapult': 12, "Ch'en the Holungday": 1, 'Pinecone': 6, 'Executor': 9, 'Aosta': 11, 'Pozëmka': 2, 'Schwarz': 3, 'Provence': 6, 'Melanite': 8, 'Aciddrop': 9, 'Rosa (Poca)': 2, 'Typhon': 2, 'Erato': 8, 'Totter': 8, 'Toddifons': 8, 'Coldshot': 9, 'Fartooth': 4, 'Firewatch': 6, 'Andreana': 7, 'Ambriel': 9, 'Lunacub': 10, 'Caper': 8, 'Mizuki': 4, 'Ethan': 5, 'Manticore': 6, 'Kirara': 15, 'Jaye': 4, 'Lee': 4, 'Swire the Elegant Wit': 5, 'Mr. Nothing': 9, 'Kirin R Yato': 1, 'Texas the Omertosa': 1, 'Phantom': 4, 'Projekt Red': 5, 'Gravel': 6, 'Kafka': 7, 'Waai Fu': 8, 'THRM-EX': 11, 'Gladiia': 3, 'Cliffheart': 6, 'Snowsant': 9, 'Rope': 9, 'Almond': 10, 'Weedy': 3, 'Enforcer': 6, 'FEater': 6, 'Shaw': 9, 'Aak': 4, 'Spuria': 16, 'Specter the Unchained': 2, 'Kazemaru': 6, 'Bena': 10, 'Verdant': 13, 'Dorothy': 3, 'Robin': 6, 'Frost': 7, 'Stainless': 5, 'Roberta': 9, 'Windflit': 14, 'Skadi the Corrupting Heart': 2, 'Heidi': 8, 'Sora': 9, 'U-Official': 19, 'Silence the Paradigmatic': 6, 'Quercus': 7, 'Tsukinogi': 12, 'Nine-Colored Deer': 15, 'Gnosis': 2, 'Shamare': 4, 'Pramanix': 6, 'Virtuosa': 2, 'Valarqvin': 8, 'Suzuran': 2, 'Angelina': 4, 'Proviso': 6, 'Istina': 7, 'Podenco': 7, 'Glaucus': 8, 'Earthspirit': 11, 'Orchid': 12, 'Ling': 1, 'Magallan': 4, 'Scene': 5, 'Mayer': 6, 'Deepcolor': 9, 'Ines': 2, 'Cantabile': 3, 'Puzzle': 6, 'Bagpipe': 2, 'Vigna': 6, 'Reed': 7, 'Wild Mane': 7, 'Grani': 9, 'Plume': 12, 'Elysium': 2, 'Saileach': 2, 'Myrtle': 4, 'Flametail': 3, 'Saga': 4, 'Texas': 5, 'Siege': 5, 'Zima': 7, 'Chiave': 8, 'Poncirus': 9, 'Scavenger': 9, 'Courier': 9, 'Vanilla': 12, 'Fang': 12, 'Yato': 14, 'Muelsyse': 3, 'Blacknight': 5, 'Vigil': 8, 'Beanstalk': 8}

if __name__ == '__main__':
    res=char_tier_gamepress()
    # print(res)

    import char
    data=char.Chars(server='US',lang='en')
    # for charname,tier in res.items():
        # if charname not in data.chars:
            # print(charname)
    names=list(res.keys())
    for charid,char in data.chars.items():
        if char.name not in res:
            print('no_tier',char.name)
        else:
            if char.name in names:
                names.remove(char.name)
    print('tier_unmatch',names)
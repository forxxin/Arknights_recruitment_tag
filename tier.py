import test
import os

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

def char_tier_gamepress():
    ''' https://gamepress.gg/arknights/tier-list/arknights-operator-tier-list '''
    url = 'https://gamepress.gg/arknights/tier-list/arknights-operator-tier-list'
    text=requests_get(url)
    soup = BeautifulSoup(text,"html.parser")
    def tiers():
        t=[]
        # for obj in soup.find_all('div', class_='clearfix text-formatted field field--name-field-text field--type-text-long field--label-hidden field__item'):
            # for x in obj.find_all('tr'):
                # for y in x.find_all('td'):
                    # if y.text=='Tier':
                        # t=[]
                    # else:
                        # t.append(y.text)
                    # break
        # print(t)
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
    tiers = tiers()
    # print(tiers)
    res={}
    tier=0
    for obj in soup.find_all('div', class_='list-main'):
        for x in obj.find_all(['td','div'], class_=['tier-cell-label','operator-title']):
            if x.name=='td':
                tier=x.text
            elif x.name=='div':
                char=x.text
                res[char]=tiers[tier]
    return res

if __name__ == '__main__':
    res=char_tier_gamepress()
    print(res)

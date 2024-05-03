import os
import re
from dataclasses import dataclass

from farmcalc import FarmCalc
import resource
try:
    import saveobj
except:
    import mods.saveobj

app_path = os.path.dirname(__file__)
os.chdir(app_path)

#Herbstmondeskonzert
side_event_memory_store_raw = """
module data b 1 75
polyme prep 1 100
nuc cry sint 1 100
oriro concen 1 25
orir bloc 1 40
grinds penta 1 35
polyme gel 1 30
cutt flu solu 1 35
tran salt agglo 1 30
# pip orga liter stan 1 110
# librar stair 1 90
# scen e of know 1 90
# knowle seek hall floor 1 90
data supp instru 1 15
polyes pac 1 15
mangan ore 1 10
coagu gel 1 12
crysta compo 1 10
lmd 5000 7
stra batt rec 2 5
tacti batt rec 2 3
front batt reco 2 1
skill sum - 3 1 4
skill sum - 2 1 2
oriro cub 1 2
sugar 1 3
polyes 1 3
oriron 1 3
polyk 1 3
devic 1 4
guard chi 1 6
furni par 10 2
lmd 20 1
"""

@dataclass
class StoreItem:
    store:str
    name:str
    itemId:str
    count:int
    token_cost:int
    san_per_item:float
    san_per_token:float

class Store():
    def __init__(self,server='US',minimize_stage_key='',lang='en',update=False):
        self.server=server
        self.minimize_stage_key=minimize_stage_key
        self.data=FarmCalc(server,minimize_stage_key,lang,update)
        self.side_event_memory_store=self.gen_store(side_event_memory_store_raw)
    def gen_item(self,name_raw):
        if name_raw.startswith('#'):
            return name_raw
        name_raw_=name_raw.lower().split()
        items=[]
        for itemId,item in self.data.items_all.items():
            name=item.name
            name_=name.lower().split()
            if len(name_)==len(name_raw_) and all(i.startswith(r) for i,r in zip(name_,name_raw_)):
                items.append(item)
        if len(items)==1:
            return items[0]
        else:
            raise Exception(name_raw,items)
    def gen_store(self,store_raw):
        store=[]
        for line in store_raw.splitlines():
            line=line.strip()
            if line=='':
                continue
            if (m:=re.match(r'^(?P<name_raw>.*?)\s+(?P<count>\d+)\s+(?P<token_cost>\d+)$',line)):
                name_raw = m.group('name_raw')
                item = self.gen_item(name_raw)
                name=getattr(item,'name',item)
                itemId=getattr(item,'id','')
                def get_san(itemid):
                    return result[0][1] if (result:= (
                            self.data.result.get(itemid) 
                            or self.data.calc_multi(' '.join((self.server,self.minimize_stage_key,itemid))))
                    ) else 0
                if itemId=='4001': #LMD
                    san = get_san('gold') 
                    print('gold',san)
                elif itemId in FarmCalc.item_exp: #Battle Record
                    san = get_san('exp')
                    print('exp',san)
                elif itemId:
                    san = get_san(itemId)
                if getattr(item,'itemType','')=='MATERIAL' and 'Chip' in name:
                    san/=2 #chip san/2
                if itemId in FarmCalc.item_exp:
                    count = int(m.group('count'))*FarmCalc.item_exp.get(itemId)
                else:
                    count = int(m.group('count'))
                token_cost = int(m.group('token_cost'))
                obj=StoreItem(
                    store='Herbstmondeskonzert',
                    name=name,
                    itemId=itemId,
                    count=count,
                    token_cost=token_cost,
                    san_per_item=round(san,2),
                    san_per_token =round(san*count/token_cost,2),
                ) 
                store.append(obj)    
            else:
                raise Exception(line)
        return sorted(store,key=lambda storeitem:storeitem.san_per_token,reverse=True)
    def print(self):
        for store_item in self.side_event_memory_store:
            print(store_item.name,store_item.count,store_item.token_cost,store_item.san_per_token)

if __name__ == "__main__":
    data=Store(server='US',minimize_stage_key='san',lang='en',update=False)
    data.print()

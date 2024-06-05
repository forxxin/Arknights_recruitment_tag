import os
import re
import pprint
from dataclasses import dataclass

from farmcalc import FarmCalc
import resource
try:
    import saveobj
except:
    import mods.saveobj

app_path = os.path.dirname(__file__)
os.chdir(app_path)

#
shops_raw={
('Dipartimento', 'act21side_token_permesso'):
                                                ['Headhunting Permit 1 150',
                                                'Bipolar Nanoflake 1 100',
                                                'Crystalline Electronic Unit 1 100',
                                                'Refined Solvent 1 35',
                                                'Incandescent Alloy Block 1 35',
                                                'Keton Colloid 1 35',
                                                'Manganese Trihydrate 1 35',
                                                # 'Module Data Block 1 75',
                                                # 'Polymerization Preparation 1 100',
                                                # 'Nuclock Concentration 1 25',
                                                # 'Oriron Block 1 40',
                                                # 'Grieic Crystal Sinter 1 100',
                                                # 'Orirndstone Pentahydrate 1 35',
                                                'Polymerized Gel 1 30',
                                                'Orirock Concentration 1 25',
                                                # 'Cutting Fluid Solution 1 35',
                                                # 'Transmuted Salt Agglomerate 1 30',
                                                "'Truck Passage' 1 110",
                                                'Patching Planks 1 90',
                                                'Wooden Coat Hanger 1 90',
                                                'Public Bookshelf 1 85',
                                                # 'Data Supplement Instrument 1 15',
                                                # 'Data Supplement Stick 1 5',
                                                'Sugar Pack 1 8',
                                                'RMA70-12 1 15',
                                                # 'Polyester Pack 1 15',
                                                # 'Manganese Ore 1 10',
                                                # 'Coagulating Gel 1 12',
                                                # 'Crystalline Component 1 10',
                                                'LMD 5000 7',
                                                'Strategic Battle Record 2 5',
                                                'Tactical Battle Record 2 3',
                                                'Frontline Battle Record 2 1',
                                                'Skill Summary - 3 1 4',
                                                'Skill Summary - 2 1 2',
                                                'Orirock Cube 1 2',
                                                # 'Sugar 1 3',
                                                # 'Polyester 1 3',
                                                'Oriron 1 3',
                                                'Polyketon 1 3',
                                                # 'Device 1 4',
                                                'Vanguard Chip 1 6',
                                                # 'Furniture Part 10 2',
                                                'LMD 20 1'],
('Herbstmondeskonzert', 'act29side_token_erin','skip'): ['Headhunting Permit 1 150',
                                               'Module Data Block 1 75',
                                               'Polymerization Preparation 1 100',
                                               'Nucleic Crystal Sinter 1 100',
                                               'Orirock Concentration 1 25',
                                               'Oriron Block 1 40',
                                               'Grindstone Pentahydrate 1 35',
                                               'Polymerized Gel 1 30',
                                               'Cutting Fluid Solution 1 35',
                                               'Transmuted Salt Agglomerate 1 30',
                                               'Pipe Organ Literature Stand 1 110',
                                               'Library Stairs 1 90',
                                               "'Scenery of Knowledge' 1 90",
                                               'Knowledge-Seeking Hall Flooring 1 90',
                                               'Data Supplement Instrument 1 15',
                                               'Data Supplement Stick 1 5',
                                               'Polyester Pack 1 15',
                                               'Manganese Ore 1 10',
                                               'Coagulating Gel 1 12',
                                               'Crystalline Component 1 10',
                                               'LMD 5000 7',
                                               'Strategic Battle Record 2 5',
                                               'Tactical Battle Record 2 3',
                                               'Frontline Battle Record 2 1',
                                               'Skill Summary - 3 1 4',
                                               'Skill Summary - 2 1 2',
                                               'Orirock Cube 1 2',
                                               'Sugar 1 3',
                                               'Polyester 1 3',
                                               'Oriron 1 3',
                                               'Polyketon 1 3',
                                               'Device 1 4',
                                               'Guard Chip 1 6',
                                               'Furniture Part 10 2',
                                               'LMD 20 1'],
# Commendations
('Cert-Green', '4005'): ['★3 Recruitment Voucher I 1 200',
                      '★4 Recruitment Voucher I 1 750',
                      'Headhunting Permit 1 450',
                      'Recruitment Permit 1 15',
                      'Orirock Cluster 1 25',
                      'Sugar Pack 1 30',
                      'Polyester Pack 1 30',
                      'Oriron Cluster 1 35',
                      'Aketon 1 35',
                      'Integrated Device 1 45',
                      'Loxic Kohl 1 30',
                      'Manganese Ore 1 35',
                      'Grindstone 1 40',
                      'RMA70-12 1 45',
                      'Coagulating Gel 1 40',
                      'Incandescent Alloy 1 35',
                      'Crystalline Component 1 30',
                      'Semi-Synthetic Solvent 1 40',
                      'Compound Cutting Fluid 1 40',
                      'Transmuted Salt 1 45',
                      'Fuscous Fiber 1 40',
                      'Aggregate Cyclicene 1 45'],
# Headhunting Data Contract
('Cert-Orange', 'EPGS_COIN'): ['Cyclicene Prefab 1 80',
                            'Solidified Fiber Board 1 75',
                            'Transmuted Salt Agglomerate 1 70',
                            'Cutting Fluid Solution 1 70',
                            'Refined Solvent 1 70',
                            'Crystalline Circuit 1 90',
                            'Incandescent Alloy Block 1 75',
                            'Polymerized Gel 1 65',
                            'RMA70-24 1 80',
                            'Grindstone Pentahydrate 1 75',
                            'Manganese Trihydrate 1 80',
                            'White Horse Kohl 1 65',
                            'Optimized Device 1 85',
                            'Keton Colloid 1 85',
                            'Oriron Block 1 90',
                            'Polyester Lump 1 80',
                            'Sugar Lump 1 75',
                            'Orirock Concentration 1 60',
                            'Aggregate Cyclicene 2 60',
                            'Fuscous Fiber 2 55',
                            'Transmuted Salt 2 55',
                            'Compound Cutting Fluid 2 50',
                            'Semi-Synthetic Solvent 2 50',
                            'Crystalline Component 2 40',
                            'Incandescent Alloy 2 40',
                            'Coagulating Gel 2 50',
                            'RMA70-12 2 60',
                            'Grindstone 2 50',
                            'Manganese Ore 2 45',
                            'Loxic Kohl 2 40',
                            'Integrated Device 2 60',
                            'Aketon 2 45',
                            'Oriron Cluster 2 45',
                            'Polyester Pack 2 35',
                            'Sugar Pack 2 35',
                            'Orirock 2 30',
                            'Device 4 40',
                            'Polyketon 4 30',
                            'Oriron 4 30',
                            'Polyester 4 25',
                            'Sugar 4 25',
                            'Orirock Cube 4 15',
                            'Damaged Device 8 40',
                            'Diketon 8 30',
                            'Oriron Shard 8 30',
                            'Ester 8 25',
                            'Sugar Substitute 8 25',
                            'Orirock 8 15'],
# Intelligence Certification
('Cert-Purple', 'REP_COIN'): ['Orundum 100 20',
                           'Optimized Device 1 85',
                           'Orirock Concentration 1 50',
                           'Keton Colloid 1 65',
                           'Sugar Lump 1 60',
                           'Oriron Block 1 70',
                           'Polyester Lump 1 60',
                           'Grindstone Pentahydrate 1 60',
                           'Manganese Trihydrate 1 60',
                           'Incandescent Alloy Block 1 60',
                           'Polymerized Gel 1 50',
                           'RMA70-24 1 65',
                           'Crystalline Circuit 1 70',
                           'White Horse Kohl 1 50',
                           'Refined Solvent 1 55',
                           'Cutting Fluid Solution 1 55',
                           'Transmuted Salt Agglomerate 1 55',
                           'LMD 2000 15',
                           'Strategic Battle Record 1 15',
                           'Skill Summary - 3 1 20'],
('Credit','SOCIAL_PT'):"""
oriron 2 240
Polyketon 2 240
Carbon Brick 3 200
Device 1 160
Recruitment Permit 1 160
LMD 3600 200
Oriron 2 240
Expedited Plan 1 160
Orirock Cube 3 200
Furniture Part 25 200
Sugar 2 200
Polyester 2 200
Skill Summary - 2 3 200
Frontline Battle Record 9 200
    """,
    ('',''):"""""",
}

@dataclass
class StoreItem:
    store:str
    name:str
    itemId:str
    count:int
    token_cost:int
    san_per_item:float
    san_per_token:float
    raw:str

class Store():
    def __init__(self,server='US',minimize_stage_key='',lang='en',update=False):
        self.server=server
        self.minimize_stage_key=minimize_stage_key
        self.data=FarmCalc(server=server,minimize_stage_key=minimize_stage_key,lang=lang,update=update)
        self.furnitures=resource.GameData.json_data('building').get('customData',{}).get('furnitures',{})
        self.stores,self.stores_sorted=self.gen_stores(shops_raw)
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
        for furnitureid,furniture in self.furnitures.items():
            name=furniture.get('name')
            name_=name.lower().split()
            if len(name_)==len(name_raw_) and all(i.startswith(r) for i,r in zip(name_,name_raw_)):
                items.append(name)
        if len(items)==1:
            return items[0]
        raise Exception(name_raw,[item.name for item in items])
    def gen_stores(self,shops_raw):
        stores={}
        stores_sorted={}
        self.shops_raw_={}
        for store_info_raw,store_raw in shops_raw.items():
            if len(store_info_raw)>2:
                continue
            store_name,store_icon_itemid=store_info_raw
            if not store_name: continue
            store_icon=resource.Img.item(store_icon_itemid)
            store_info=store_name,store_icon
            store,store_sorted = self.gen_store(store_raw,store_info)
            stores[store_info] = store
            stores_sorted[store_info] = store_sorted
            self.shops_raw_[store_info_raw] = [store_item.raw for store_item in store]
        return stores,stores_sorted
    def gen_store(self,store_raw,store_info):
        # def get_san(itemid):
            # return result[0][1] if (result:= (
                    # self.data.result.get(itemid) 
                    # or self.data.calc_multi(' '.join((self.server,self.minimize_stage_key,itemid))))
            # ) else 0
        if isinstance(store_raw,str):
            store_raw=store_raw.splitlines()
        store=[]
        for line in store_raw:
            line=line.strip()
            if line=='':
                continue
            if (m:=re.match(r'^(?P<name_raw>.*?)\s+(?P<count>\d+)\s+(?P<token_cost>\d+)$',line)):
                name_raw = m.group('name_raw')
                item = self.gen_item(name_raw)
                name=getattr(item,'name',item)
                count = int(m.group('count'))
                token_cost = int(m.group('token_cost'))
                raw=f'{name} {count} {token_cost}'
                itemId=getattr(item,'id','')
                if itemId=='4001': #LMD
                    san = self.data.get_san('gold') 
                elif itemId in FarmCalc.item_exp: #Battle Record
                    san = self.data.get_san('exp')
                elif itemId:
                    san = self.data.get_san(itemId)
                else:
                    san = 0
                if itemId in FarmCalc.item_exp:
                    count*=FarmCalc.item_exp.get(itemId)
                obj=StoreItem(
                    store=store_info,
                    name=name,
                    itemId=itemId,
                    count=count,
                    token_cost=token_cost,
                    san_per_item=round(san,2),
                    san_per_token =round(san*count/token_cost,2),
                    raw=raw,
                )
                store.append(obj)    
            else:
                raise Exception(line)
        return store,sorted(store,key=lambda storeitem:storeitem.san_per_token,reverse=True)
    def print(self):
        for name,store in self.stores.items():
            print(name)
            for store_item in store:
                print(store_item.name,store_item.count,store_item.token_cost,store_item.san_per_token)
        for name,store in self.stores_sorted.items():
            print(name)
            for store_item in store:
                print(store_item.name,store_item.count,store_item.token_cost,store_item.san_per_token)

if __name__ == "__main__":
    data=Store(server='US',minimize_stage_key='san',lang='en',update=False)
    pprint.pprint(data.shops_raw_, width=100)

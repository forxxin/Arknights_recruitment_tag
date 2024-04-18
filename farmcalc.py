
import urllib.request
import json
import requests
import pprint
import os
from datetime import datetime
from functools import cache
from dataclasses import dataclass
import copy
import re

try:
    from scipy.optimize import linprog
    import numpy as np
except Exception as e:
    print(e)

try:
    from shelve_cache import shelve_cache
except:
    from mods.shelve_cache import shelve_cache

try:
    from saveobj import save_json,load_json
except:
    from mods.saveobj import save_json,load_json

import anhrtags

app_path = os.path.dirname(__file__)
os.chdir(app_path)

class Gv:
    server='US' #US CN JP KR
    lang='en'
    now = datetime.now().timestamp()*1000
    
@shelve_cache('./tmp/farmcalc._get_json.cache')
def _get_json(key):
    penguin_api = 'https://penguin-stats.io/PenguinStats/api/v2/'
    url = penguin_api + key
    print(url)
    response = requests.get(url)
    return response.json()

def get_json(key,update=False):
    if update:
        return _get_json(key,usecache=False)
    else:
        return _get_json(key)

def penguin_stats(update=False):
    def _penguin_stats(name,query):
        data=get_json(query,update)
        file=f'./tmp/{name}.json'
        if (not os.path.isfile(file)) or update:
            save_json(file,data)
        return data
    stages = _penguin_stats('stages',f'stages?server={Gv.server}')
    items = _penguin_stats('items','items')
    stageitems = _penguin_stats('stageitems','result/matrix?show_closed_zone=false')
    stageitems_all = _penguin_stats('stageitems_all','result/matrix?show_closed_zone=true')
    formulas = _penguin_stats('formulas','formula')
    # def check():
        # for item in stageitems_all.get('matrix'):
            # if item not in stageitems.get('matrix'):
                # print(item)
                # return False
        # return True
    # assert check()
    return stages,items,stageitems,formulas

def str_itemlist(itemlist):
    return ' + '.join([str(i) for i in itemlist if str(i)])

@dataclass
class Stage:
    name:str
    id:str
    code:str
    san:int
    normal_drop:list #list of itemId
    outs:list #list of Item
    danger_level:float
    def __str__(self):
        return f'{self.name}|{self.danger_level}: {self.san}San = {str_itemlist(self.outs)}'
    def normaldrops(self):
        return [Data.items[itemId] for itemId in self.normal_drop]
    
@dataclass
class ItemType():
    name:str
    id:str
    rarity:int
    itemType:str
    groupID:str
    img_data:list
    beststage:list
    def __str__(self):
        # return f'{self.name}:{self.id}:{self.rarity}:{self.itemType}:{self.groupID}'
        return f'{self.name}'

@dataclass
class Item():
    item:ItemType
    n:float
    def __str__(self):
        if self.n>0.0:
            return f'{self.n:.3f}{self.item.name}'
        else:
            return ''
    def __mul__(self, other):
        v=float(other)
        ret = copy.copy(self)
        ret.n*=v
        return ret

    __rmul__ = __mul__
@dataclass
class Formula:
    name:str
    id:str
    goldCost:int
    ins:list #list of Item
    out:list #list of Item
    out_ex:list #list of Item
    def __str__(self):
        return f'{self.goldCost}LMD + {str_itemlist(self.ins)} = {str_itemlist(self.out+self.out_ex)}'

@dataclass
class Req:
    gold:int
    exp:int
    reqs:list #list of Item
    def __str__(self):
        str_gold=f'{self.gold}LMD' if self.gold else ''
        str_exp=f'{self.exp}Exp' if self.exp else ''
        return f'Req: {' + '.join([i for i in [str_gold,str_exp,str_itemlist(self.reqs)] if i])}'
    
class Data:
    items={}
    stages={}
    formulas={}
    item_exp={
        '2001':200,
        '2002':400,
        '2003':1000,
        '2004':2000,
    }
    stagecode_gold={
        '1-1':660,
        '2-7':1500,
        '3-6':2040,
        '4-1':2700,
        '6-1':1216,
        '7-3':1216,
        'R8-1':2700,
        'R8-4':1216,
        '9-2':2700,
        '9-3':1216,
        '10-8':3480,
        'S2-2':1020,
        'S4-6':3480,
        'S5-2':2700,
        'S5-3':1216,
        'S5-5':1216,
        'S6-2':1216,
        'S6-4':2700,
        'S7-1':2700,
        'S7-2':1216,
        'CE-1':1700,
        'CE-2':2800,
        'CE-3':4100,
        'CE-4':5700,
        'CE-5':7500,
        'CE-6':10000,
    }
    except_itemType=['RECRUIT_TAG'] + ['TEMP','LGG_SHD','ACTIVITY_ITEM',] 
    except_stageId=['recruit',]
    url_material = "https://raw.githubusercontent.com/Aceship/Arknight-Images/main/material/"
    img_data={
        "D32 Steel":('bg/item-5.png','0.png'),
        "Bipolar Nanoflake":('bg/item-5.png','1.png'),
        "Polymerization Preparation":('bg/item-5.png','2.png'),
        "Crystalline Electroassembly":('bg/item-5.png','65.png'),
        "RMA70-24":('bg/item-4.png','3.png'),
        "Grindstone Pentahydrate":('bg/item-4.png','4.png'),
        "Manganese Trihydrate":('bg/item-4.png','5.png'),
        "White Horse Kohl":('bg/item-4.png','6.png'),
        "Optimized Device":('bg/item-4.png','7.png'),
        "Keton Colloid":('bg/item-4.png','8.png'),
        "Oriron Block":('bg/item-4.png','9.png'),
        "Polyester Lump":('bg/item-4.png','10.png'),
        "Sugar Lump":('bg/item-4.png','11.png'),
        "Orirock Concentration":('bg/item-4.png','12.png'),
        "Incandescent Alloy Block":('bg/item-4.png','62.png'),
        "Polymerized Gel":('bg/item-4.png','64.png'),
        "Crystalline Circuit":('bg/item-4.png','66.png'),
        "Integrated Device":('bg/item-3.png','13.png'),
        "Aketon":('bg/item-3.png','14.png'),
        "Oriron Cluster":('bg/item-3.png','15.png'),
        "Polyester Pack":('bg/item-3.png','16.png'),
        "Sugar Pack":('bg/item-3.png','17.png'),
        "Orirock Cluster":('bg/item-3.png','18.png'),
        "Loxic Kohl":('bg/item-3.png','31.png'),
        "Grindstone":('bg/item-3.png','32.png'),
        "Manganese Ore":('bg/item-3.png','33.png'),
        "RMA70-12":('bg/item-3.png','34.png'),
        "Incandescent Alloy":('bg/item-3.png','61.png'),
        "Coagulating Gel":('bg/item-3.png','63.png'),
        "Crystalline Component":('bg/item-3.png','67.png'),
        "Device":('bg/item-2.png','19.png'),
        "Polyketon":('bg/item-2.png','20.png'),
        "Oriron":('bg/item-2.png','21.png'),
        "Polyester":('bg/item-2.png','22.png'),
        "Sugar":('bg/item-2.png','23.png'),
        "Orirock Cube":('bg/item-2.png','24.png'),
        "Damaged Device":('bg/item-1.png','25.png'),
        "Diketon":('bg/item-1.png','26.png'),
        "Oriron Shard":('bg/item-1.png','27.png'),
        "Ester":('bg/item-1.png','28.png'),
        "Sugar Substitute":('bg/item-1.png','29.png'),
        "Orirock":('bg/item-1.png','30.png'),
    }
    
def prep_items(items):
    for item in items:
        if item.get('existence').get(Gv.server).get('exist')==True and (item.get('itemType') not in Data.except_itemType):
            itemId=item.get('itemId')
            obj=ItemType(
                name=item.get('name_i18n').get(Gv.lang),
                id=itemId,
                rarity=item.get('rarity'),
                itemType=item.get('itemType'),
                groupID=item.get('groupID') or '',
                img_data=[],
                beststage=[],
            )
            if (img_data:=Data.img_data.get(obj.name)):
                obj.img_data=img_data
            Data.items[itemId]=obj

def prep_stages(stages):
    stageinfos = anhrtags.GData.json_table('stage').get('stages',{})
    def dangerLevel(stageinfo):
        if (m:=re.match(r'Elite *(\d+) *Lv. *(\d+)',stageinfo.get('dangerLevel') or '')):
            return float(f'{m.group(1)}.{m.group(2)}')
        return 0
    for stage in stages:
        if ((dropInfos:=stage.get('dropInfos')) 
            and stage.get('existence').get(Gv.server).get('exist')==True 
            and ((stageId:=stage.get('stageId')) not in Data.except_stageId)
            ):
            normal_drop = [dropInfo.get('itemId') for dropInfo in dropInfos if dropInfo.get('dropType')=='NORMAL_DROP' and dropInfo.get('itemId')]
            stageinfo=stageinfos.get(stageId,{})
            obj=Stage(
                name=f'stage:{stage.get('code_i18n').get(Gv.lang)}',
                id=stageId,
                code=stage.get('code'),
                san=stage.get('apCost'),
                normal_drop=normal_drop,
                outs=[],
                danger_level=dangerLevel(stageinfo),
            )
            itemIds=set()
            for dropInfo in dropInfos:
                if (itemId:=dropInfo.get('itemId')):
                    if itemId not in itemIds:
                        itemIds.add(itemId)
                        obj.outs.append(Item(
                                            item=Data.items[itemId],
                                            n=0,
                                        ))
            Data.stages[stageId]=obj
            # print(obj)

def prep_stageitems(stageitems):
    for stageitem in stageitems.get('matrix',{}):
        stageId=stageitem.get('stageId')
        itemId=stageitem.get('itemId')
        times=stageitem.get('times')
        quantity=stageitem.get('quantity')
        start=stageitem.get('start')
        end=stageitem.get('end')
        n=quantity/times
        if Gv.now>start and ((not end) or Gv.now<end):
            # continue
            # if n>1:
            # print(stageId,itemId,n)
            if Data.stages.get(stageId):
                for loot in Data.stages[stageId].outs:
                    if loot.item.id==itemId:
                        loot.n=n
        # else:
            # print(stageId,itemId,n)

def prep_formula(formulas):
    for formula in formulas:
        itemId=formula.get('id')
        obj=Formula(
            name=f'formula:{Data.items[itemId].name}',
            id=itemId,
            goldCost=formula.get('goldCost'),
            ins=[],
            out=[Item(
                            item=Data.items[itemId],
                            n=1,
                        )],
            out_ex=[],
        )
        for cost in formula.get('costs'):
            itemId_cost=cost.get('id')
            obj.ins.append(Item(
                            item=Data.items[itemId_cost],
                            n=cost.get('count'),
                        ))
        weight_all=0
        totalWeight=formula.get('totalWeight')
        for extraOutcome in formula.get('extraOutcome'):
            itemId_out=extraOutcome.get('id')
            count=extraOutcome.get('count')
            weight=extraOutcome.get('weight')
            weight_all+=weight
            n=count*weight/totalWeight
            obj.out_ex.append(Item(
                                item=Data.items[itemId_out],
                                n=n,
                            ))
        Data.formulas[itemId]=obj
        assert totalWeight==weight_all


def print_lp(lp,args,req_,p=True):
    if not lp.success:
        if p: print(lp.message)
        return
    x=lp.x
    san = np.dot(args.get('c'),x)
    if p: print('print_lp:')
    if p: print(req_)
    if p: print(f'    {san=}')
    res_stage=[]
    res_formula=[]
    for idx,(n,obj) in enumerate(zip(list(x),list(Data.stages.values())+list(Data.formulas.values()))):
        if n>0:
            if isinstance(obj,Stage):
                res_stage.append((obj,n))
            elif isinstance(obj,Formula):
                # if p: print(f'    {obj.name}:{n:.1f}')
                res_formula.append((obj,n))
    res_stage=sorted(res_stage,key=lambda i:-i[1])
    res_formula=sorted(res_formula,key=lambda i:-i[1])
    for obj,n in res_stage:
        if p: print(f'    {obj.name}:{n:.1f}')
    for obj,n in res_formula:
        if p: print(f'    {obj.name}:{n:.1f}')
    return res_stage,res_formula,san

def calc(req,test=False):
    '''
        x=[?]
        minimize: san(Stages+formulas,x)
        subject to: -loot(stages+formulas,x) <= -req
    '''
    ex=0.018
    def to_array(obj):
        exp=0
        gold=0
        def item_array(items):
            nonlocal exp
            d={}
            for item in items:
                itemId=item.item.id
                n=item.n
                exp+=Data.item_exp.get(itemId,0)*n
                d[itemId]=n
                # if isinstance(obj,Stage) and obj.id in ['wk_kc_6','tough_12-08']:
                    # if Data.item_exp.get(itemId,0):
                        # print(Data.item_exp.get(itemId,0),n)
            return np.array([n if (n:=d.get(itemtype.id)) else 0 for itemtype in Data.items.values()])
        if isinstance(obj,Stage):
            # if obj.id in ['wk_kc_6','tough_12-08']:
                # print(obj)
            gold+=Data.stagecode_gold.get(obj.code,0)
            return np.append(item_array(obj.outs),[exp,gold])
        elif isinstance(obj,Formula):
            gold+=-obj.goldCost
            return np.append(item_array(obj.out)+item_array(obj.out_ex)*ex-item_array(obj.ins),[exp,gold])
        elif isinstance(obj,Req):
            return np.append(item_array(obj.reqs),[obj.exp,obj.gold])
    xkey0=list(Data.stages.keys())
    xkey1=list(Data.formulas.keys())
    xkey=xkey0+xkey1
    
    req_=Req(
        gold=req.get('gold',0),
        exp=req.get('exp',0),
        reqs=[Item(
            item=Data.items[itemId],
            n=n,
        ) for itemId,n in req.items() if Data.items.get(itemId)],
    )
    # integrality=[1]*len(xkey)
    # integrality=3
    integrality=None
    args={
        'c':np.array([stage.san for stage in Data.stages.values()] + [0 for formula in Data.formulas.values()]),
        'A_ub':-np.array(
            [to_array(stage) for stage in Data.stages.values()] + 
            [to_array(formula) for formula in Data.formulas.values()]
        ).T,
        'b_ub':-to_array(req_), 
        'integrality':integrality, #1,3: very slow
        'A_eq':None, 'b_eq':None, 'bounds':(0, None), 'method':'highs', 'callback':None, 'options':None, 'x0':None #default
    }
    lp=linprog(**args)
    return lp,args,req_

def print_items():
    '''print req={}'''
    items=sorted(list(Data.items.values()),key=lambda i:(i.itemType,i.groupID,i.rarity,i.name,i.id))
    print(*[f"""{' '*8}'{i.id}':100,{' '*(28-len(i.id))}#{i.name:<37}#{i.rarity} #{i.itemType}:{i.groupID}""" for i in items],sep='\n')
    
req={
    'gold':0,
    'exp':0,
    '30125':0,                       #Bipolar Nanoflake                    #4 #ARKPLANNER:
    '30145':0,                       #Crystalline Electronic Unit          #4 #ARKPLANNER:
    '30135':0,                       #D32 Steel                            #4 #ARKPLANNER:
    '30155':0,                       #Nucleic Crystal Sinter               #4 #ARKPLANNER:
    '30115':0,                       #Polymerization Preparation           #4 #ARKPLANNER:
    '2001':0,                        #Drill Battle Record                  #1 #CARD_EXP:exp
    '2002':0,                        #Frontline Battle Record              #2 #CARD_EXP:exp
    '2003':0,                        #Tactical Battle Record               #3 #CARD_EXP:exp
    '2004':0,                        #Strategic Battle Record              #4 #CARD_EXP:exp
    '3251':0,                        #Caster Chip                          #2 #CHIP:chip
    '3231':0,                        #Defender Chip                        #2 #CHIP:chip
    '3221':0,                        #Guard Chip                           #2 #CHIP:chip
    '3261':0,                        #Medic Chip                           #2 #CHIP:chip
    '3241':0,                        #Sniper Chip                          #2 #CHIP:chip
    '3281':0,                        #Specialist Chip                      #2 #CHIP:chip
    '3271':0,                        #Supporter Chip                       #2 #CHIP:chip
    '3211':0,                        #Vanguard Chip                        #2 #CHIP:chip
    '3252':0,                        #Caster Chip Pack                     #3 #CHIP:chip
    '3232':0,                        #Defender Chip Pack                   #3 #CHIP:chip
    '3222':0,                        #Guard Chip Pack                      #3 #CHIP:chip
    '3262':0,                        #Medic Chip Pack                      #3 #CHIP:chip
    '3242':0,                        #Sniper Chip Pack                     #3 #CHIP:chip
    '3282':0,                        #Specialist Chip Pack                 #3 #CHIP:chip
    '3272':0,                        #Supporter Chip Pack                  #3 #CHIP:chip
    '3212':0,                        #Vanguard Chip Pack                   #3 #CHIP:chip
    'furni':0,                       #Furniture                            #0 #FURN:
    '3003':0,                        #Pure Gold                            #3 #MATERIAL:
    '31023':0,                       #Incandescent Alloy                   #2 #MATERIAL:alloy
    '31024':0,                       #Incandescent Alloy Block             #3 #MATERIAL:alloy
    '3112':0,                        #Carbon Stick                         #1 #MATERIAL:carbon
    '3113':0,                        #Carbon Brick                         #2 #MATERIAL:carbon
    '3114':0,                        #Carbon Brick                         #3 #MATERIAL:carbon
    '31033':0,                       #Crystalline Component                #2 #MATERIAL:crystal
    '31034':0,                       #Crystalline Circuit                  #3 #MATERIAL:crystal
    '31053':0,                       #Compound Cutting Fluid               #2 #MATERIAL:cutting_fluid
    '31054':0,                       #Cutting Fluid Solution               #3 #MATERIAL:cutting_fluid
    '30061':1,                       #Damaged Device                       #0 #MATERIAL:device
    '30062':0,                       #Device                               #1 #MATERIAL:device
    '30063':0,                       #Integrated Device                    #2 #MATERIAL:device
    '30064':0,                       #Optimized Device                     #3 #MATERIAL:device
    '30031':0,                       #Ester                                #0 #MATERIAL:ester
    '30032':0,                       #Polyester                            #1 #MATERIAL:ester
    '30033':0,                       #Polyester Pack                       #2 #MATERIAL:ester
    '30034':0,                       #Polyester Lump                       #3 #MATERIAL:ester
    '31013':0,                       #Coagulating Gel                      #2 #MATERIAL:gel
    '31014':0,                       #Polymerized Gel                      #3 #MATERIAL:gel
    '30093':0,                       #Grindstone                           #2 #MATERIAL:grindstone
    '30094':0,                       #Grindstone Pentahydrate              #3 #MATERIAL:grindstone
    '30051':0,                       #Diketon                              #0 #MATERIAL:keton
    '30052':0,                       #Polyketon                            #1 #MATERIAL:keton
    '30053':0,                       #Aketon                               #2 #MATERIAL:keton
    '30054':0,                       #Keton Colloid                        #3 #MATERIAL:keton 
    # https://raw.githubusercontent.com/Aceship/Arknight-Images/main/material/bg/item-4.png
    # https://raw.githubusercontent.com/Aceship/Arknight-Images/main/items/MTL_SL_KETONE4.png
    '30073':0,                       #Loxic Kohl                           #2 #MATERIAL:kohl
    '30074':0,                       #White Horse Kohl                     #3 #MATERIAL:kohl
    '30083':0,                       #Manganese Ore                        #2 #MATERIAL:manganese
    '30084':0,                       #Manganese Trihydrate                 #3 #MATERIAL:manganese
    '30011':0,                       #Orirock                              #0 #MATERIAL:orirock
    '30012':0,                       #Orirock Cube                         #1 #MATERIAL:orirock
    '30013':0,                       #Orirock Cluster                      #2 #MATERIAL:orirock
    '30014':0,                       #Orirock Concentration                #3 #MATERIAL:orirock
    '30041':0,                       #Oriron Shard                         #0 #MATERIAL:oriron
    '30042':0,                       #Oriron                               #1 #MATERIAL:oriron
    '30043':0,                       #Oriron Cluster                       #2 #MATERIAL:oriron
    '30044':0,                       #Oriron Block                         #3 #MATERIAL:oriron
    '30103':0,                       #RMA70-12                             #2 #MATERIAL:rma
    '30104':0,                       #RMA70-24                             #3 #MATERIAL:rma
    '31063':0,                       #Transmuted Salt                      #2 #MATERIAL:salt
    '31064':0,                       #Transmuted Salt Agglomerate          #3 #MATERIAL:salt
    '3301':0,                        #Skill Summary - 1                    #1 #MATERIAL:skillbook
    '3302':0,                        #Skill Summary - 2                    #2 #MATERIAL:skillbook
    '3303':0,                        #Skill Summary - 3                    #3 #MATERIAL:skillbook
    '31043':0,                       #Semi-Synthetic Solvent               #2 #MATERIAL:solvent
    '31044':0,                       #Refined Solvent                      #3 #MATERIAL:solvent
    '30021':0,                       #Sugar Substitute                     #0 #MATERIAL:sugar
    '30022':0,                       #Sugar                                #1 #MATERIAL:sugar
    '30023':0,                       #Sugar Pack                           #2 #MATERIAL:sugar
    '30024':0,                       #Sugar Lump                           #3 #MATERIAL:sugar
}

@cache
def best_stages():
    s4=[]
    s5=[]
    count=1234321
    for itemid,v in req.items():
        lp,args,req_=calc({itemid:count},test=True)
        if lp.success:
            res_stage,res_formula,san=print_lp(lp,args,req_,p=False)
            beststage=[]
            for stage,n in res_stage:
                # if n>count/10:
                if stage.id not in s4:
                    s4.append(stage.id)
                    s5.append(stage.id.replace('_perm',''))
                if stage.code!='CE-6':
                    beststage.append(stage)
            if (item:=Data.items.get(itemid)):
                item.beststage=beststage
        else:
            print(itemid,lp)
    if s4:
        return s4,s5

loaded=False
def init():
    global loaded
    if not loaded:
        loaded=True
        stages,items,stageitems,formulas = penguin_stats()
        prep_items(items)
        prep_stages(stages)
        prep_stageitems(stageitems)
        prep_formula(formulas)
        best_stages()
    
init()
if __name__ == '__main__':
    # print(*[str(i) for i in Data.items.values()],sep='\n')
    # print(*[str(i) for i in Data.stages.values()],sep='\n')
    # print(*[str(i) for i in Data.formulas.values()],sep='\n')
    res=calc(req)
    print_lp(*res)

'''
scipy.optimize.linprog(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=(0, None), method='highs', callback=None, options=None, x0=None, integrality=None)
minimize
    c @ x
such that
    A_ub @ x <= b_ub
    A_eq @ x == b_eq
    lb <= x <= ub (default lb = 0 and ub = None)
c    1-D array
b_ub 1-D array
b_eq 1-D array
A_ub 2-D array
A_eq 2-D array
'''


'''wk_melee_6|wk_kc_6|act18d0_08_perm|tough_10-02|tough_10-06|main_12-15|main_01-07|main_00-02|act16d5_03_perm|tough_12-08|wk_kc_6|pro_b_1|pro_a_1|pro_d_1|pro_a_1|pro_b_1|pro_d_1|pro_c_1|pro_c_1|pro_b_2|pro_a_2|pro_d_2|pro_a_2|pro_b_2|pro_d_2|pro_c_2|pro_c_2|act18d0_01_perm|act18d0_05_perm|act11d0_06_perm|main_03-03|wk_armor_2|wk_armor_3|wk_armor_5|main_08-13|main_08-13|main_10-15|main_09-17|main_02-03|act11d0_05_perm|tough_11-06|main_03-03|act12side_04_perm|sub_03-1-2|act18d0_06_perm|main_03-08|main_12-04|tough_10-02|main_09-14|main_07-13|act14side_05_perm|main_03-07|main_03-01|main_03-01|a001_05_perm|main_02-10|main_10-14|main_10-14|sub_02-05|main_01-07|main_01-07|main_01-07|act17side_05_perm|sub_03-2-1|sub_03-2-1|tough_10-10|main_09-17|main_01-07|tough_11-03|main_09-16|wk_fly_2|wk_fly_3|wk_fly_5|main_12-09|main_12-09|a001_04_perm|sub_03-1-1|act15d0_06_perm|main_11-05'''
'''CE-6|LS-6|WD-8|10-3|10-7|12-17|1-7|0-2|WR-3|12-9|LS-6|PR-B-1|PR-A-1|PR-D-1|PR-A-1|PR-B-1|PR-D-1|PR-C-1|PR-C-1|PR-B-2|PR-A-2|PR-D-2|PR-A-2|PR-B-2|PR-D-2|PR-C-2|PR-C-2|WD-1|WD-5|TW-6|3-3|SK-2|SK-3|SK-5|R8-11|R8-11|10-17|9-19|2-3|TW-5|11-7|3-3|DH-4|S3-2|WD-6|3-8|12-5|10-3|9-16|7-15|BI-5|3-7|3-1|3-1|GT-5|2-10|10-16|10-16|S2-5|1-7|1-7|1-7|SN-5|S3-3|S3-3|10-11|9-19|1-7|11-3|9-18|CA-2|CA-3|CA-5|12-10|12-10|GT-4|S3-1|MB-6|11-6'''

"Grani and the Knights' Treasure"     # GT-1 GT-2 GT-3 GT-4 GT-5 GT-6 GT-EX-1 GT-EX-3 GT-HX-1 GT-HX-3
"Heart of Surging Flame"              # ENTRY OF-ST1 OF-1 OF-ST2 OF-2 OF-3 OF-4 OF-ST3 OF-5 OF-6 OF-ST4 OF-7 OF-8 OF-ST5 OF-ST6 OF-EX1 OF-EX3 OF-EX6
"Code of Brawl"                       # ENTRY CB-1 CB-2 CB-3 CB-4 CB-5 CB-ST1 CB-6 CB-7 CB-8 CB-ST2 CB-9 CB-10 CB-ST3 CB-EX1 CB-EX2 CB-EX3
"Twilight of Wolumonde"               # TW-ST-1 TW-1 TW-2 TW-3 TW-4 TW-5 TW-6 TW-7 TW-8 TW-ST-2 TW-S-1 TW-S-2
"Darknights Memoir"                   # DM-1 DM-2 DM-3 DM-5 DM-6 DM-7 DM-8 DM-ST-1
"The Great Chief Returns"             # RI-1 RI-2 RI-3 RI-4 RI-ST-1 RI-5 RI-6 RI-ST-2 RI-7 RI-8 RI-9 RI-EX-1
"Maria Nearl"                         # MN-ST-1 MN-1 MN-2 MN-3 MN-4 MN-5 MN-6 MN-7 MN-ST-2 MN-8 MN-ST-3
"Mansfield Break"                     # MB-1 MB-2 MB-3 MB-ST-1 MB-4 MB-5 MB-6 MB-7 MB-8 MB-ST-2
"Who Is Real"                         # WR-ST-1 WR-1 WR-2 WR-4 WR-5 WR-ST-2 WR-6 WR-8 WR-10 WR-ST-3
"Operation Originium Dust"            # OD-ST-1 OD-1 OD-2 OD-3 OD-5 OD-6 OD-ST-2 OD-7 OD-8 OD-ST-3
"A Walk in the Dust"                  # WD-1 WD-2 WD-3 WD-ST-1 WD-5 WD-7 WD-8 WD-ST-2
"Under Tides"                         # SV-1 SV-2 SV-3 SV-4 SV-5 SV-6 SV-7 SV-ST-1 SV-8 SV-9 SV-ST-2
"Dossoles Holiday"                    # DH-ST-1 DH-1 DH-2 DH-3 DH-ST-2 DH-4 DH-5 DH-6 DH-ST-3 DH-7 DH-8 DH-9 DH-ST-4
"Near Light"                          # NL-ST-1 NL-1 NL-2 NL-3 NL-4 NL-ST-2 NL-5 NL-6 NL-ST-3 NL-7 NL-8 NL-9 NL-10 NL-ST-4
"Break the Ice"                       # BI-1 BI-ST-1 BI-2 BI-3 BI-ST-2 BI-4 BI-5 BI-ST-3 BI-6 BI-7 BI-8 BI-ST-4
"Invitation to Wine"                  # IW-ST-1 IW-1 IW-2 IW-3 IW-4 IW-ST-2 IW-5 IW-6 IW-7 IW-9 IW-ST-3
"Guide Ahead"                         # GA-ST-1 GA-1 GA-2 GA-3 GA-4 GA-5 GA-6 GA-7 GA-8 GA-ST-2
"Stultifera Navis"                    # SN-ST-1 SN-1 SN-ST-2 SN-2 SN-ST-3 SN-3 SN-ST-4 SN-ST-5 SN-4 SN-5 SN-6 SN-ST-6 SN-ST-7 SN-7 SN-ST-8 SN-ST-9 SN-8 SN-ST-10 SN-ST-11 SN-10 SN-ST-12
"Lingering Echoes"                    # LE-ST-1 LE-1 LE-2 LE-3 LE-4 LE-ST-2 LE-5 LE-6 LE-7 LE-8 LE-ST-3
"Ideal City: Endless Carnival"        # IC-ST-1 IC-1 IC-2 IC-3 IC-4 IC-5 IC-6 IC-7 IC-8 IC-9 IC-ST-2
"Dorothy's Vision"                    # DV-ST-1 DV-1 DV-2 DV-3 DV-4 DV-5 DV-S-1 DV-6 DV-7 DV-S-2 DV-8 DV-ST-2
"IL Siracusano"                       # IS-ST-1 IS-1 IS-2 IS-3 IS-4 IS-ST-2 IS-5 IS-6 IS-7 IS-8 IS-ST-3 IS-9 IS-10 IS-ST-4
"What the Firelight Casts"            # FC-ST-1 FC-1 FC-2 FC-3 FC-4 FC-5 FC-6 FC-7 FC-ST-2 FC-8 FC-ST-3
"Where Vernal Winds Will Never Blow"  # WB-ST-1 WB-1 WB-2 WB-3 WB-4 WB-ST-2 WB-5 WB-6 WB-7 WB-8 WB-9 WB-ST-3
"A Flurry to the Flame"               # CF-ST-1 CF-TR-1 CF-2 CF-3 CF-4 CF-ST-2 CF-5 CF-6 CF-7 CF-8 CF-9 CF-ST-3
"Lone Trail"                          # CW-ST-1 CW-1 CW-2 CW-3 CW-ST-2 CW-4 CW-5 CW-6 CW-7 CW-8 CW-9 CW-10 CW-ST-3 CW-ST-4
"Hortus de Escapismo"                 # HE-ST-1 HE-1 HE-2 HE-3 HE-4 HE-5 HE-6 HE-ST-2 HE-7 HE-8 HE-ST-3
"So Long, Adele: Home Away From Home" # SL-ST-1 SL-1 SL-2 SL-3 SL-4 SL-5 SL-ST-2 SL-6 SL-7 SL-8 SL-ST-3
"Evil Time Part 1"                    # 0-1 0-2 0-4 0-6 0-7 0-8 0-9 0-10 0-11
"Evil Time Part 2"                    # 1-1 1-3 1-4 1-6 1-7 1-8 1-10 1-12
"Separated Hearts"                    # 2-1 2-2 2-3 2-4 2-5 2-6 2-7 2-8 2-9 2-10
"Stinging Shock"                      # 3-1 3-2 3-3 3-4 3-5 3-6 3-7 3-8
"Burning Run"                         # 4-1 4-2 4-3 4-4 4-5 4-6 4-7 4-8 4-9 4-10
"Necessary Solutions"                 # 5-1 5-2 5-3 5-4 5-6 5-7 5-9 5-10 5-11
"Partial Necrosis"                    # 6-1 6-2 6-3 6-4 6-5 6-6 6-7 6-8 6-9 6-10 6-11 6-12 6-13 6-14 6-15 6-16 6-17 6-18
"The Birth of Tragedy"                # 7-1 7-2 7-3 7-4 7-5 7-6 7-7 7-8 7-9 7-10 7-13 7-17 7-18 7-19 7-20
"Roaring Flare"                       # R8-1 M8-1 R8-3 M8-2 R8-4 M8-3 R8-5 M8-4 R8-6 M8-5 R8-8 M8-6 R8-9 M8-7 R8-11 M8-8 JT8-1 JT8-2 JT8-3 END8-1 EG-1 EG-2 EG-3 EG-4 EG-5
"Stormwatch"                          # 9-1 9-2 9-3 9-4 9-5 9-6 9-7 9-8 9-9 9-10 9-12 9-13 9-14 9-18 9-19 9-20 9-21
"Shatterpoint"                        # 10-1 10-2 10-3 10-4 10-5 10-6 10-7 10-8 10-9 10-10 10-11 10-12 10-13 10-14 10-15 10-16 10-17 10-18 10-19
"Return To Mist"                      # 11-1 11-2 11-3 11-4 11-5 11-6 11-7 11-8 11-9 11-10 11-11 11-12 11-14 11-15 11-16 11-17 11-19 11-21
"All Quiet Under the Thunder"         # 12-1 12-2 12-3 12-4 12-5 12-6 12-7 12-8 12-9 12-10 12-11 12-12 12-13 12-14 12-15 12-16 12-17 12-18 12-19 12-20 12-21


''' best_stages
gold  CE-6   wk_melee_6        10000.0 36.0 #gold
exp   LS-6   wk_kc_6           10000.0 36.0 #exp

2001  0-2    main_00-02        0.2 1.4 #Drill Battle Record
2002  WR-3   act16d5_03_perm   0.2 3.0 #Frontline Battle Record
2003  12-9   tough_12-08       0.3 5.9 #Tactical Battle Record
2004  LS-6   wk_kc_6           0.2 9.0 #Strategic Battle Record
3251  PR-B-1 pro_b_1           2.0 35.9 #Caster Chip
3231  PR-A-1 pro_a_1           2.0 36.0 #Defender Chip
3221  PR-D-1 pro_d_1           2.0 36.0 #Guard Chip
3261  PR-A-1 pro_a_1           2.0 36.0 #Medic Chip
3241  PR-B-1 pro_b_1           2.0 36.1 #Sniper Chip
3281  PR-D-1 pro_d_1           2.0 36.0 #Specialist Chip
3271  PR-C-1 pro_c_1           2.0 36.0 #Supporter Chip
3211  PR-C-1 pro_c_1           2.0 36.0 #Vanguard Chip
3252  PR-B-2 pro_b_2           2.0 72.0 #Caster Chip Pack
3232  PR-A-2 pro_a_2           2.0 71.9 #Defender Chip Pack
3222  PR-D-2 pro_d_2           2.0 72.0 #Guard Chip Pack
3262  PR-A-2 pro_a_2           2.0 72.1 #Medic Chip Pack
3242  PR-B-2 pro_b_2           2.0 72.0 #Sniper Chip Pack
3282  PR-D-2 pro_d_2           2.0 72.0 #Specialist Chip Pack
3272  PR-C-2 pro_c_2           2.0 71.9 #Supporter Chip Pack
3212  PR-C-2 pro_c_2           2.0 72.1 #Vanguard Chip Pack
furni WD-1   act18d0_01_perm   1.5 18.0 #Furniture
3003  WD-5   act18d0_05_perm   1.5 18.0 #Pure Gold
31023 TW-6   act11d0_06_perm   2.5 37.8 #Incandescent Alloy
3112  SK-2   wk_armor_2        0.2 3.8 #Carbon Stick
3113  SK-3   wk_armor_3        0.4 8.0 #Carbon Brick
3114  SK-5   wk_armor_5        0.3 10.0 #Carbon Brick
31033 R8-11  main_08-13        1.7 36.1 #Crystalline Component
31053 10-17  main_10-15        1.9 44.6 #Compound Cutting Fluid
30061 2-3    main_02-03        0.7 8.0 #Damaged Device
30062 TW-5   act11d0_05_perm   1.0 15.6 #Device
30063 11-7   tough_11-06       2.2 46.9 #Integrated Device
30031 DH-4   act12side_04_perm 0.4 4.7 #Ester
30032 S3-2   sub_03-1-2        0.6 9.5 #Polyester
30033 WD-6   act18d0_06_perm   1.9 29.2 #Polyester Pack
31013 12-5   main_12-04        2.8 59.8 #Coagulating Gel
30093 9-16   main_09-14        2.5 45.1 #Grindstone
30051 BI-5   act14side_05_perm 0.5 6.2 #Diketon
30052 3-7    main_03-07        0.8 12.2 #Polyketon
30053 3-1    main_03-01        2.5 36.9 #Aketon
30073 GT-5   a001_05_perm      2.3 33.9 #Loxic Kohl
30083 10-16  main_10-14        1.8 38.2 #Manganese Ore
30011 S2-5   sub_02-05         0.3 3.2 #Orirock
30012 1-7    main_01-07        0.8 4.7 #Orirock Cube
30013 1-7    main_01-07        3.9 23.3 #Orirock Cluster
30014 1-7    main_01-07        15.5 93.3 #Orirock Concentration
30041 SN-5   act17side_05_perm 0.5 6.1 #Oriron Shard
30042 S3-3   sub_03-2-1        0.8 11.9 #Oriron
30043 S3-3   sub_03-2-1        3.2 47.7 #Oriron Cluster
30103 9-19   main_09-17        2.5 52.4 #RMA70-12
31063 11-3   tough_11-03       3.2 66.5 #Transmuted Salt
3301  CA-2   wk_fly_2          0.2 3.0 #Skill Summary - 1
3302  CA-3   wk_fly_3          0.3 6.7 #Skill Summary - 2
3303  CA-5   wk_fly_5          0.5 15.0 #Skill Summary - 3
31043 12-10  main_12-09        2.9 60.1 #Semi-Synthetic Solvent
30021 GT-4   a001_04_perm      0.4 4.9 #Sugar Substitute
30022 S3-1   sub_03-1-1        0.6 9.5 #Sugar
30023 MB-6   act15d0_06_perm   2.0 29.4 #Sugar Pack
'''

'''
stage:GT-4|0: 12San = 2.427Sugar Substitute + 0.228Oriron Shard + 0.270Diketon + 0.019Sugar + 0.015Oriron + 0.022Polyketon + 0.064Frontline Battle Record + 1.401Drill Battle Record
stage:GT-5|0: 15San = 0.442Loxic Kohl + 0.218Orirock + 0.141Ester + 0.085Damaged Device + 0.118Pure Gold + 0.213Orirock Cube + 0.142Polyester + 0.086Device + 0.000Furniture
stage:TW-5|0: 15San = 0.216Orirock + 0.146Ester + 0.087Damaged Device + 0.117Pure Gold + 0.204Orirock Cube + 0.136Polyester + 0.932Device
stage:TW-6|0: 15San = 0.396Incandescent Alloy + 0.156Sugar Substitute + 0.123Oriron Shard + 0.122Diketon + 0.099Drill Battle Record + 0.131Sugar + 0.105Oriron + 0.104Polyketon + 0.161Frontline Battle Record
stage:DH-4|0: 12San = 2.559Ester + 0.079Pure Gold + 0.401Orirock + 0.030Orirock Cube + 0.163Damaged Device + 0.010Polyester
stage:BI-5|0: 12San = 1.927Diketon + 0.239Drill Battle Record + 0.054Frontline Battle Record + 0.260Sugar Substitute + 0.021Sugar + 0.254Oriron Shard + 0.015Oriron + 0.015Polyketon
stage:MB-6|0: 15San = 0.464Sugar Pack + 0.156Sugar Substitute + 0.122Oriron Shard + 0.122Diketon + 0.097Drill Battle Record + 0.132Sugar + 0.103Oriron + 0.106Polyketon + 0.163Frontline Battle Record
stage:WR-3|0: 12San = 4.012Frontline Battle Record + 0.397Orirock + 0.304Ester + 0.166Damaged Device + 0.080Pure Gold + 0.033Orirock Cube + 0.014Polyester + 0.005Device
stage:SN-5|0: 12San = 1.966Oriron Shard + 0.240Drill Battle Record + 0.040Frontline Battle Record + 0.263Sugar Substitute + 0.023Sugar + 0.020Oriron + 0.203Diketon + 0.014Polyketon
stage:WD-1|0: 12San = 0.333Ester + 0.667Drill Battle Record + 0.667Furniture
stage:WD-5|0: 12San = 0.667Pure Gold + 0.333Device
stage:WD-6|0: 15San = 0.466Polyester Pack + 0.212Orirock + 0.145Ester + 0.083Damaged Device + 0.121Pure Gold + 0.208Orirock Cube + 0.146Polyester + 0.085Device + 0.000Furniture
stage:WD-8|0: 18San = 0.332RMA70-12 + 0.289Orirock + 0.112Damaged Device + 0.315Orirock Cube + 0.126Device + 0.019Orirock Cluster + 0.009Integrated Device + 0.016Loxic Kohl + 0.012Coagulating Gel + 0.101Pure Gold
stage:0-2|0: 6San = 4.264Drill Battle Record + 0.026Orirock + 0.017Sugar Substitute + 0.016Ester + 0.014Oriron Shard + 0.016Diketon + 0.011Damaged Device + 0.100Pure Gold + 0.003Furniture
stage:1-7|0: 6San = 1.245Orirock Cube + 0.119Orirock + 0.059Sugar Substitute + 0.059Ester + 0.047Diketon + 0.047Oriron Shard + 0.035Damaged Device + 0.090Pure Gold + 1.240Drill Battle Record + 0.005Furniture
stage:1-7|0: 6San = 1.245Orirock Cube + 0.119Orirock + 0.059Sugar Substitute + 0.059Ester + 0.047Diketon + 0.047Oriron Shard + 0.035Damaged Device + 0.090Pure Gold + 1.240Drill Battle Record + 0.005Furniture
stage:1-7|0: 6San = 1.245Orirock Cube + 0.119Orirock + 0.059Sugar Substitute + 0.059Ester + 0.047Diketon + 0.047Oriron Shard + 0.035Damaged Device + 0.090Pure Gold + 1.240Drill Battle Record + 0.005Furniture
stage:1-7|0: 6San = 1.245Orirock Cube + 0.119Orirock + 0.059Sugar Substitute + 0.059Ester + 0.047Diketon + 0.047Oriron Shard + 0.035Damaged Device + 0.090Pure Gold + 1.240Drill Battle Record + 0.005Furniture
stage:1-7|0: 6San = 1.245Orirock Cube + 0.119Orirock + 0.059Sugar Substitute + 0.059Ester + 0.047Diketon + 0.047Oriron Shard + 0.035Damaged Device + 0.090Pure Gold + 1.240Drill Battle Record + 0.005Furniture
stage:2-3|0: 12San = 1.495Damaged Device + 0.413Orirock + 0.273Ester + 0.097Pure Gold + 0.026Orirock Cube + 0.010Device + 1.250Drill Battle Record + 0.009Furniture + 0.017Polyester
stage:3-1|0: 15San = 0.370Aketon + 0.156Sugar Substitute + 0.123Oriron Shard + 0.123Diketon + 0.101Drill Battle Record + 0.128Sugar + 0.104Oriron + 0.106Polyketon + 0.161Frontline Battle Record + 0.015Furniture
stage:3-1|0: 15San = 0.370Aketon + 0.156Sugar Substitute + 0.123Oriron Shard + 0.123Diketon + 0.101Drill Battle Record + 0.128Sugar + 0.104Oriron + 0.106Polyketon + 0.161Frontline Battle Record + 0.015Furniture
stage:PR-A-1|0: 18San = 0.000Furniture + 0.500Defender Chip + 0.500Medic Chip
stage:PR-A-1|0: 18San = 0.000Furniture + 0.500Defender Chip + 0.500Medic Chip
stage:PR-B-1|0: 18San = 0.000Furniture + 0.499Sniper Chip + 0.501Caster Chip
stage:PR-B-1|0: 18San = 0.000Furniture + 0.499Sniper Chip + 0.501Caster Chip
stage:PR-C-1|0: 18San = 0.000Furniture + 0.500Vanguard Chip + 0.500Supporter Chip
stage:PR-C-1|0: 18San = 0.000Furniture + 0.500Vanguard Chip + 0.500Supporter Chip
stage:PR-D-1|0: 18San = 0.000Furniture + 0.500Guard Chip + 0.500Specialist Chip
stage:PR-D-1|0: 18San = 0.000Furniture + 0.500Guard Chip + 0.500Specialist Chip
stage:S2-5|0: 12San = 3.748Orirock + 0.170Damaged Device + 0.097Pure Gold + 0.024Orirock Cube + 0.018Polyester + 0.010Device + 1.252Drill Battle Record + 0.011Furniture + 0.260Ester
stage:10-3|0: 21San = 0.332Coagulating Gel + 0.051Polymerized Gel + 0.099Drill Battle Record + 0.160Frontline Battle Record + 0.071Tactical Battle Record + 0.114Sugar Substitute + 0.201Sugar + 0.025Sugar Pack + 0.087Oriron Shard + 0.163Oriron + 0.020Oriron Cluster + 0.020Manganese Ore + 0.020Incandescent Alloy + 0.015Furniture + 0.020Transmuted Salt
stage:10-3|0: 21San = 0.332Coagulating Gel + 0.051Polymerized Gel + 0.099Drill Battle Record + 0.160Frontline Battle Record + 0.071Tactical Battle Record + 0.114Sugar Substitute + 0.201Sugar + 0.025Sugar Pack + 0.087Oriron Shard + 0.163Oriron + 0.020Oriron Cluster + 0.020Manganese Ore + 0.020Incandescent Alloy + 0.015Furniture + 0.020Transmuted Salt
stage:10-7|0: 24San = 0.430Manganese Ore + 0.048Manganese Trihydrate + 0.098Pure Gold + 0.214Orirock + 0.331Orirock Cube + 0.046Orirock Cluster + 0.085Damaged Device + 0.133Device + 0.024Integrated Device + 0.038Loxic Kohl + 0.028Coagulating Gel + 0.019Furniture
stage:10-11|0: 24San = 0.457Oriron Cluster + 0.043Oriron Block + 0.199Drill Battle Record + 0.321Frontline Battle Record + 0.070Tactical Battle Record + 0.113Sugar Substitute + 0.183Sugar + 0.030Sugar Pack + 0.088Oriron Shard + 0.148Oriron + 0.028Manganese Ore + 0.028Incandescent Alloy + 0.018Furniture + 0.025Transmuted Salt
stage:11-3|0: 21San = 0.316Transmuted Salt + 0.053Transmuted Salt Agglomerate + 0.102Drill Battle Record + 0.158Frontline Battle Record + 0.069Tactical Battle Record + 0.112Sugar Substitute + 0.201Sugar + 0.024Sugar Pack + 0.086Oriron Shard + 0.162Oriron + 0.019Oriron Cluster + 0.020Manganese Ore + 0.020Incandescent Alloy + 0.018Furniture
stage:11-7|0: 21San = 0.404Integrated Device + 0.100Pure Gold + 0.215Orirock + 0.363Orirock Cube + 0.030Orirock Cluster + 0.085Damaged Device + 0.145Device + 0.024Loxic Kohl + 0.019Coagulating Gel + 0.016Furniture
stage:12-9|0: 21San = 3.542Tactical Battle Record + 0.102Drill Battle Record + 0.157Frontline Battle Record + 0.112Sugar Substitute + 0.212Sugar + 0.026Sugar Pack + 0.082Oriron Shard + 0.161Oriron + 0.021Oriron Cluster + 0.025Manganese Ore + 0.021Incandescent Alloy + 0.019Transmuted Salt + 0.021Furniture
stage:SK-2|0: 15San = 0.013Furniture + 4.000Carbon Stick
stage:CA-2|0: 15San = 5.000Skill Summary - 1 + 0.012Furniture
stage:CA-3|0: 20San = 3.000Skill Summary - 2 + 1.000Skill Summary - 1 + 0.020Furniture

stage:2-10|1.1: 15San = 0.278RMA70-12 + 0.157Sugar Substitute + 0.123Oriron Shard + 0.124Diketon + 0.130Sugar + 0.100Drill Battle Record + 0.104Oriron + 0.159Frontline Battle Record + 0.103Polyketon + 0.012Furniture
stage:3-3|1.1: 15San = 0.321Grindstone + 0.217Orirock + 0.141Ester + 0.085Damaged Device + 0.213Orirock Cube + 0.120Pure Gold + 0.140Polyester + 0.085Device + 0.013Furniture
stage:3-3|1.1: 15San = 0.321Grindstone + 0.217Orirock + 0.141Ester + 0.085Damaged Device + 0.213Orirock Cube + 0.120Pure Gold + 0.140Polyester + 0.085Device + 0.013Furniture
stage:S3-1|1.1: 15San = 1.518Sugar + 0.157Sugar Substitute + 0.123Oriron Shard + 0.121Diketon + 0.100Drill Battle Record + 0.102Oriron + 0.103Polyketon + 0.159Frontline Battle Record + 0.013Furniture
stage:SK-3|1.1: 20San = 0.699Carbon Stick + 2.499Carbon Brick + 0.017Furniture
stage:S3-2|1.15: 15San = 0.214Orirock + 1.529Polyester + 0.138Ester + 0.085Damaged Device + 0.123Pure Gold + 0.209Orirock Cube + 0.088Device + 0.014Furniture
stage:3-7|1.25: 15San = 1.183Polyketon + 0.159Sugar Substitute + 0.126Oriron Shard + 0.137Diketon + 0.103Drill Battle Record + 0.133Sugar + 0.107Oriron + 0.164Frontline Battle Record + 0.013Furniture
stage:S3-3|1.3: 15San = 0.157Sugar Substitute + 0.123Oriron Shard + 0.123Diketon + 1.215Oriron + 0.100Drill Battle Record + 0.104Polyketon + 0.129Sugar + 0.014Furniture + 0.161Frontline Battle Record
stage:S3-3|1.3: 15San = 0.157Sugar Substitute + 0.123Oriron Shard + 0.123Diketon + 1.215Oriron + 0.100Drill Battle Record + 0.104Polyketon + 0.129Sugar + 0.014Furniture + 0.161Frontline Battle Record
stage:3-8|1.35: 18San = 0.386Polyester Pack + 0.032Polyester Lump + 0.332Diketon + 0.105Polyester + 0.088Polyketon + 0.013Aketon + 0.010Grindstone + 0.008RMA70-12 + 0.016Furniture + 0.414Ester + 0.008Crystalline Component + 0.007Compound Cutting Fluid
stage:PR-A-2|1.5: 36San = 0.000Furniture + 0.501Defender Chip Pack + 0.499Medic Chip Pack
stage:PR-A-2|1.5: 36San = 0.000Furniture + 0.501Defender Chip Pack + 0.499Medic Chip Pack
stage:PR-B-2|1.5: 36San = 0.000Furniture + 0.500Sniper Chip Pack + 0.500Caster Chip Pack
stage:PR-B-2|1.5: 36San = 0.000Furniture + 0.500Sniper Chip Pack + 0.500Caster Chip Pack
stage:PR-C-2|1.5: 36San = 0.000Furniture + 0.500Vanguard Chip Pack + 0.500Supporter Chip Pack
stage:PR-C-2|1.5: 36San = 0.000Furniture + 0.500Vanguard Chip Pack + 0.500Supporter Chip Pack
stage:PR-D-2|1.5: 36San = 0.000Furniture + 0.500Guard Chip Pack + 0.500Specialist Chip Pack
stage:PR-D-2|1.5: 36San = 0.000Furniture + 0.500Guard Chip Pack + 0.500Specialist Chip Pack
stage:CA-5|1.6: 30San = 2.000Skill Summary - 3 + 1.500Skill Summary - 1 + 0.024Furniture + 1.501Skill Summary - 2
stage:7-15|2.1: 18San = 0.333Integrated Device + 0.167Sugar Substitute + 0.133Oriron Shard + 0.100Drill Battle Record + 0.194Sugar + 0.157Oriron + 0.100Frontline Battle Record + 0.015Sugar Pack + 0.012Oriron Cluster + 0.012Incandescent Alloy + 0.012Manganese Ore + 0.087Tactical Battle Record + 0.018Furniture + 0.012Transmuted Salt
stage:9-16|2.1: 18San = 0.400Grindstone + 0.481Oriron + 0.014Furniture
stage:9-18|2.1: 21San = 0.330Semi-Synthetic Solvent + 0.049Refined Solvent + 0.113Sugar Substitute + 0.094Oriron Shard + 0.099Drill Battle Record + 0.197Sugar + 0.161Oriron + 0.159Frontline Battle Record + 0.029Sugar Pack + 0.022Oriron Cluster + 0.025Manganese Ore + 0.023Incandescent Alloy + 0.069Tactical Battle Record + 0.017Furniture + 0.021Transmuted Salt
stage:10-16|2.1: 21San = 0.771Polyester + 0.549Manganese Ore + 0.020Furniture
stage:10-16|2.1: 21San = 0.771Polyester + 0.549Manganese Ore + 0.020Furniture
stage:12-5|2.1: 21San = 0.351Coagulating Gel + 0.049Polymerized Gel + 0.099Pure Gold + 0.213Orirock + 0.368Orirock Cube + 0.028Orirock Cluster + 0.086Damaged Device + 0.144Device + 0.013Integrated Device + 0.023Loxic Kohl + 0.017Furniture
stage:SK-5|2.1: 30San = 3.000Carbon Brick + 0.501Carbon Brick + 0.028Furniture
stage:11-6|2.15: 21San = 0.501Sugar Pack + 1.064Oriron + 0.020Furniture
stage:LS-6|2.2: 36San = 2.000Tactical Battle Record + 4.000Strategic Battle Record + 0.029Furniture
stage:LS-6|2.2: 36San = 2.000Tactical Battle Record + 4.000Strategic Battle Record + 0.029Furniture
stage:CE-6|2.2: 36San = 0.029Furniture
stage:R8-11|2.25: 21San = 0.582Crystalline Component + 0.039Crystalline Circuit + 0.216Orirock + 0.085Damaged Device + 0.364Orirock Cube + 0.144Device + 0.029Orirock Cluster + 0.014Integrated Device + 0.023Loxic Kohl + 0.018Coagulating Gel + 0.100Pure Gold + 0.016Furniture
stage:R8-11|2.25: 21San = 0.582Crystalline Component + 0.039Crystalline Circuit + 0.216Orirock + 0.085Damaged Device + 0.364Orirock Cube + 0.144Device + 0.029Orirock Cluster + 0.014Integrated Device + 0.023Loxic Kohl + 0.018Coagulating Gel + 0.100Pure Gold + 0.016Furniture
stage:9-19|2.25: 21San = 0.401RMA70-12 + 0.414Ester + 0.331Diketon + 0.084Polyester + 0.067Polyketon + 0.022Polyester Pack + 0.018Aketon + 0.014Grindstone + 0.013Crystalline Component + 0.010Compound Cutting Fluid + 0.010Semi-Synthetic Solvent + 0.017Furniture
stage:9-19|2.25: 21San = 0.401RMA70-12 + 0.414Ester + 0.331Diketon + 0.084Polyester + 0.067Polyketon + 0.022Polyester Pack + 0.018Aketon + 0.014Grindstone + 0.013Crystalline Component + 0.010Compound Cutting Fluid + 0.010Semi-Synthetic Solvent + 0.017Furniture
stage:10-17|2.3: 24San = 0.538Compound Cutting Fluid + 0.101Pure Gold + 0.221Orirock + 0.320Orirock Cube + 0.046Orirock Cluster + 0.083Damaged Device + 0.130Device + 0.024Integrated Device + 0.040Loxic Kohl + 0.030Coagulating Gel + 0.020Furniture
stage:12-10|2.3: 21San = 0.349Semi-Synthetic Solvent + 0.056Refined Solvent + 0.434Ester + 0.080Polyester + 0.020Polyester Pack + 0.298Diketon + 0.074Polyketon + 0.021Aketon + 0.018Grindstone + 0.012RMA70-12 + 0.017Crystalline Component + 0.011Compound Cutting Fluid + 0.019Furniture
stage:12-10|2.3: 21San = 0.349Semi-Synthetic Solvent + 0.056Refined Solvent + 0.434Ester + 0.080Polyester + 0.020Polyester Pack + 0.298Diketon + 0.074Polyketon + 0.021Aketon + 0.018Grindstone + 0.012RMA70-12 + 0.017Crystalline Component + 0.011Compound Cutting Fluid + 0.019Furniture
stage:12-17|2.3: 21San = 0.465Compound Cutting Fluid + 0.051Cutting Fluid Solution + 0.097Pure Gold + 0.215Orirock + 0.362Orirock Cube + 0.029Orirock Cluster + 0.086Damaged Device + 0.147Device + 0.014Integrated Device + 0.024Loxic Kohl + 0.019Coagulating Gel + 0.016Furniture
'''

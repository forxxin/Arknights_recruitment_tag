
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
    # server='CN' #US CN JP KR
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
    def _penguin_stats(name,query,server=''):
        data=get_json(query,update)
        file=f'./tmp/{name}{server}.json'
        if (not os.path.isfile(file)) or update:
            save_json(file,data)
        return data
    stages = _penguin_stats('stages',f'stages?server={Gv.server}',Gv.server)
    items = _penguin_stats('items','items')
    stageitems = _penguin_stats('stageitems','result/matrix?show_closed_zone=false')
    stageitems_all = _penguin_stats('stageitems_all','result/matrix?show_closed_zone=true')
    formulas = _penguin_stats('formulas','formula')
    return stages,items,stageitems,formulas

def str_itemlist(itemlist):
    return ' + '.join([str(i) for i in itemlist if str(i)])

@dataclass
class Stage:
    name:str
    id:str
    code:str
    san:int
    minClearTime:int
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
    minimize_stage_key=''
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
        dropInfos=stage.get('dropInfos',{})
        if stage.get('existence').get(Gv.server).get('exist')==True:
            if (stageId:=stage.get('stageId')) not in Data.except_stageId:
                normal_drop = [dropInfo.get('itemId') for dropInfo in dropInfos if dropInfo.get('dropType')=='NORMAL_DROP' and dropInfo.get('itemId')]
                stageinfo=stageinfos.get(stageId,{})
                obj=Stage(
                    name=f'stage:{stage.get('code_i18n').get(Gv.lang)}',
                    id=stageId,
                    code=stage.get('code'),
                    san=stage.get('apCost'),
                    minClearTime=int(stage.get('minClearTime') or 999999999),
                    normal_drop=normal_drop,
                    outs=[],
                    danger_level=dangerLevel(stageinfo),
                )
                itemIds=set()
                Data.stages[stageId]=obj

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
            if Data.stages.get(stageId):
                if Data.items.get(itemId):
                    out = Item(
                        item=Data.items[itemId],
                        n=n,
                    )
                    if out not in Data.stages[stageId].outs:
                        Data.stages[stageId].outs.append(out)

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

def calc(req,test=False,minimize_stage_key='san'):
    '''
        x=[?]
        minimize: san(Stages+formulas,x)
        subject to: -loot(stages+formulas,x) <= -req
        
        x=[?]
        minimize: minClearTime(Stages+formulas,x)
        subject to: -loot(stages+formulas,x) <= -req
    '''
    ex=0.18
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
        'c':np.array([getattr(stage,minimize_stage_key) for stage in Data.stages.values()] + [0 for formula in Data.formulas.values()]),
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
def best_stages(minimize_stage_key='san'):
    s4=[]
    s5=[]
    count=1234321
    for itemid,v in req.items():
        lp,args,req_=calc({itemid:count},test=True,minimize_stage_key=minimize_stage_key)
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
        return s4,s5,minimize_stage_key

loaded=False
def init(minimize_stage_key='san'):
    global loaded
    if not loaded:
        loaded=True
        stages,items,stageitems,formulas = penguin_stats()
        prep_items(items)
        prep_stages(stages)
        prep_stageitems(stageitems)
        prep_formula(formulas)
        s4,s5,minimize_stage_key = best_stages(minimize_stage_key=minimize_stage_key)
        Data.minimize_stage_key=minimize_stage_key

init(minimize_stage_key='san')
# init(minimize_stage_key='minClearTime')
if __name__ == '__main__':
    # print(*[str(i) for i in Data.items.values()],sep='\n')
    # print(*[str(i) for i in Data.stages.values()],sep='\n')
    # print(*[str(i) for i in Data.formulas.values()],sep='\n')
    # res=calc(req,minimize_stage_key='minClearTime')
    res=calc(req,minimize_stage_key='san')
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

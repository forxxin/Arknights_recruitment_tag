
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
    outs:list #list of Item
    danger_level:float
    def __str__(self):
        return f'{self.name}|{self.danger_level}: {self.san}San = {str_itemlist(self.outs)}'
    
@dataclass
class ItemType():
    name:str
    id:str
    rarity:int
    itemType:str
    groupID:str
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
            )
            Data.items[itemId]=obj
            # print(obj)

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
            stageinfo=stageinfos.get(stageId,{})
            obj=Stage(
                name=f'stage:{stage.get('code_i18n').get(Gv.lang)}',
                id=stageId,
                code=stage.get('code'),
                san=stage.get('apCost'),
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


def print_lp(lp,args,req_):
    if not lp.success:
        print(lp.message)
        return
    x=lp.x
    san = np.dot(args.get('c'),x)
    print(req_)
    print(f'    {san=}')
    res_stage=[]
    res_formula=[]
    for idx,(n,obj) in enumerate(zip(list(x),list(Data.stages.values())+list(Data.formulas.values()))):
        if n>0:
            if isinstance(obj,Stage):
                res_stage.append((obj,n))
            elif isinstance(obj,Formula):
                # print(f'    {obj.name}:{n:.1f}')
                res_formula.append((obj,n))
    res_stage=sorted(res_stage,key=lambda i:-i[1])
    res_formula=sorted(res_formula,key=lambda i:-i[1])
    for obj,n in res_stage:
        print(f'    {obj.name}:{n:.1f}')
    for obj,n in res_formula:
        print(f'    {obj.name}:{n:.1f}')
        
    return res_stage,res_formula,san

def calc(req,test=False):
    '''
        x=[?]
        minimize: san(Stages+formulas,x)
        subject to: -loot(stages+formulas,x) <= -req
    '''
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
    ex=0.018
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
    items=sorted(list(Data.items.values()),key=lambda i:(i.itemType,i.groupID,i.rarity,i.name,i.id))
    print(*[f"""{' '*8}'{i.id}':100,{' '*(28-len(i.id))}#{i.name:<37}#{i.rarity} #{i.itemType}:{i.groupID}""" for i in items],sep='\n')
    
if __name__ == '__main__':
    stages,items,stageitems,formulas = penguin_stats()
    prep_items(items)
    prep_stages(stages)
    prep_stageitems(stageitems)
    prep_formula(formulas)
    # print(*[str(i) for i in Data.items.values()],sep='\n')
    # print(*[str(i) for i in Data.stages.values()],sep='\n')
    # print(*[str(i) for i in Data.formulas.values()],sep='\n')
    
    best_stages='wk_melee_6|wk_kc_6|act18d0_08_perm|tough_10-02|tough_10-06|main_12-15|main_01-07|main_00-02|act16d5_03_perm|tough_12-08|wk_kc_6|pro_b_1|pro_a_1|pro_d_1|pro_a_1|pro_b_1|pro_d_1|pro_c_1|pro_c_1|pro_b_2|pro_a_2|pro_d_2|pro_a_2|pro_b_2|pro_d_2|pro_c_2|pro_c_2|act18d0_01_perm|act18d0_05_perm|act11d0_06_perm|main_03-03|wk_armor_2|wk_armor_3|wk_armor_5|main_08-13|main_08-13|main_10-15|main_09-17|main_02-03|act11d0_05_perm|tough_11-06|main_03-03|act12side_04_perm|sub_03-1-2|act18d0_06_perm|main_03-08|main_12-04|tough_10-02|main_09-14|main_07-13|act14side_05_perm|main_03-07|main_03-01|main_03-01|a001_05_perm|main_02-10|main_10-14|main_10-14|sub_02-05|main_01-07|main_01-07|main_01-07|act17side_05_perm|sub_03-2-1|sub_03-2-1|tough_10-10|main_09-17|main_01-07|tough_11-03|main_09-16|wk_fly_2|wk_fly_3|wk_fly_5|main_12-09|main_12-09|a001_04_perm|sub_03-1-1|act15d0_06_perm|main_11-05'
    best_stages = [Data.stages[i] for i in best_stages.split('|')]
    best_stages=sorted(best_stages,key=lambda i:(i.danger_level,i.id,i.name))
    # print(*best_stages,sep='\n')
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

    # print_items()
    req={
        # 'gold':180000,
        # 'exp':100000,
        '30125':0,                       #Bipolar Nanoflake                    #4 #ARKPLANNER:
        '30145':0,                       #Crystalline Electronic Unit          #4 #ARKPLANNER:
        '30135':0,                       #D32 Steel                            #4 #ARKPLANNER:
        '30155':0,                       #Nucleic Crystal Sinter               #4 #ARKPLANNER:
        '30115':4,                       #Polymerization Preparation           #4 #ARKPLANNER:
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
        '30061':0,                       #Damaged Device                       #0 #MATERIAL:device
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
        '30054':5,                       #Keton Colloid                        #3 #MATERIAL:keton
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
        
        
        # 'recruit_tag_aoe':1,             #AoE                                  #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_caster':1,          #Caster                               #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_crowd_control':1,   #Crowd-Control                        #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_dp_recovery':1,     #DP-Recovery                          #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_dps':1,             #DPS                                  #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_debuff':1,          #Debuff                               #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_defender':1,        #Defender                             #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_defense':1,         #Defense                              #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_fast_redeploy':1,   #Fast-Redeploy                        #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_guard':1,           #Guard                                #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_healing':1,         #Healing                              #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_medic':1,           #Medic                                #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_melee':1,           #Melee                                #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_nuker':1,           #Nuker                                #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_ranged':1,          #Ranged                               #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_robot':1,           #Robot                                #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_senior_operator':1, #Senior Operator                      #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_shift':1,           #Shift                                #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_slow':1,            #Slow                                 #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_sniper':1,          #Sniper                               #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_specialist':1,      #Specialist                           #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_starter':1,         #Starter                              #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_summon':1,          #Summon                               #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_support':1,         #Support                              #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_supporter':1,       #Supporter                            #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_survival':1,        #Survival                             #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_top_operator':1,    #Top Operator                         #0 #RECRUIT_TAG:recruit_tag
        # 'recruit_tag_vanguard':1,        #Vanguard                             #0 #RECRUIT_TAG:recruit_tag
        # 'token_ObsidianCoin':1,          #Obsidian Festival Token              #3 #ACTIVITY_ITEM:
        # 'token_Obsidian':1,              #Siesta Obsidian                      #3 #ACTIVITY_ITEM:
        # 'randomMaterial_3':1,            #32-hour Strategic Ration             #4 #ACTIVITY_ITEM:
        # 'ap_supply_lt_010':1,            #Emergency Sanity Sampler             #4 #ACTIVITY_ITEM:
        # 'randomMaterial_4':1,            #Fan Appreciation Supplies            #4 #ACTIVITY_ITEM:
        # 'randomMaterial_2':1,            #New Year's Lantern                   #4 #ACTIVITY_ITEM:
        # 'et_ObsidianPass':1,             #Obsidian Festival Ticket             #4 #ACTIVITY_ITEM:
        # 'randomMaterial_1':1,            #Rhodes Island Supplies               #4 #ACTIVITY_ITEM:
        # 'randomMaterial_5':1,            #Rhodes Island Supplies II            #4 #ACTIVITY_ITEM:
        # 'randomMaterial_6':1,            #Rhodes Island Supplies III           #4 #ACTIVITY_ITEM:
        # 'randomMaterial_7':1,            #Rhodes Island Supplies IV            #4 #ACTIVITY_ITEM:
        # 'randomMaterial_8':1,            #Rhodes Island Supplies V             #4 #ACTIVITY_ITEM:
        # 'charm_coin_3':1,                #Dossoles Big Lottery                 #0 #ACTIVITY_ITEM:charm
        # 'charm_coin_2':1,                #Error Coin                           #0 #ACTIVITY_ITEM:charm
        # 'charm_coin_1':1,                #Gold Chip                            #0 #ACTIVITY_ITEM:charm
        # 'charm_r1':1,                    #Sticker - 20 Voucher                 #1 #ACTIVITY_ITEM:charm
        # 'charm_r2':1,                    #Sticker - 40 Voucher                 #2 #ACTIVITY_ITEM:charm
        # 'charm_coin_4':1,                #Court Emeraldia Premium              #3 #ACTIVITY_ITEM:charm
        # 'trap_oxygen_3':1,               #Scharzhof Coating Device Starter Pack#3 #ACTIVITY_ITEM:charm
        # 'act24side_melding_1':1,         #破碎的骨片                                #0 #ACTIVITY_ITEM:melding
        # 'act24side_melding_2':1,         #源石虫的硬壳                               #1 #ACTIVITY_ITEM:melding
        # 'act24side_melding_3':1,         #鬣犄兽的尖锐齿                              #2 #ACTIVITY_ITEM:melding
        # 'act24side_melding_4':1,         #凶豕兽的厚实皮                              #3 #ACTIVITY_ITEM:melding
        # 'act24side_melding_5':1,         #“兽之泪”                                #4 #ACTIVITY_ITEM:melding
        # '4001_1000':1,                   #LMD1000                              #3 #TEMP:
        # '4001_1500':1,                   #LMD1500                              #3 #TEMP:
        # '4001_2000':1,                   #LMD2000                              #3 #TEMP:
        # '4005':1,                        #Commendation Certificate             #2 #LGG_SHD:
    }
    def test():
        s=''
        s1=[]
        s2=''
        s3=''
        count=100000
        for k,v in req.items():
            lp,args,req_=calc({k:count},test=True)
            if lp.success:
                res_stage,res_formula,san=print_lp(lp,args,req_)
                if len(res_stage)==1:
                    s1.append((req_,res_stage[0],san))
                if len(res_stage)>=1:
                    s2+=res_stage[0][0].name[6:]+'|'
                    s3+=res_stage[0][0].id+'|'
            else:
                s+=k+'|'
        print()
        if s1:
            r=[]
            for req_,(obj,n),san in s1:
                if req_.reqs:
                    r.append((req_.reqs[0].item.id,req_.reqs[0].item.name,obj,n/count,san/count))
                elif req_.exp:
                    r.append(('exp','exp',obj,count/n,san/n))
                elif req_.gold:
                    r.append(('gold','gold',obj,count/n,san/n))
            for itemid,name,stag,times,san in r:
                print(f'{itemid: <5} {stag.name[6:]: <6} {stag.id: <17} {times:.1f} {san:.1f} #{name}')
                '''
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
        if s:
            print('infeasible:',s[:-1])
        if s2:
            print('best_stages:',s2[:-1])
            print('best_stages:',s3[:-1])
            # CE-6|LS-6|WD-8|10-3|10-7|12-17|1-7|0-2|WR-3|12-9|LS-6|PR-B-1|PR-A-1|PR-D-1|PR-A-1|PR-B-1|PR-D-1|PR-C-1|PR-C-1|PR-B-2|PR-A-2|PR-D-2|PR-A-2|PR-B-2|PR-D-2|PR-C-2|PR-C-2|WD-1|WD-5|TW-6|3-3|SK-2|SK-3|SK-5|R8-11|R8-11|10-17|9-19|2-3|TW-5|11-7|3-3|DH-4|S3-2|WD-6|3-8|12-5|10-3|9-16|7-15|BI-5|3-7|3-1|3-1|GT-5|2-10|10-16|10-16|S2-5|1-7|1-7|1-7|SN-5|S3-3|S3-3|10-11|9-19|1-7|11-3|9-18|CA-2|CA-3|CA-5|12-10|12-10|GT-4|S3-1|MB-6|11-6
    if 1:
        res=calc(req)
        print_lp(*res)
    else:
        test()

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

'''
Req: 100000LMD
    san=360.0
    stage:CE-6:10.0
Req: 100000Exp
    san=360.0
    stage:LS-6:10.0
Req: 100000.000Bipolar Nanoflake
    san=30527619.43631654
    stage:WD-8:547081.0
    stage:OF-F3:386107.2
    stage:11-13:361342.0
    stage:3-3:310578.4
    stage:10-6:64139.6
    stage:11-7:61655.4
    formula:White Horse Kohl:181628.0
    formula:Orirock Cube:138005.9
    formula:Orirock Cluster:127446.1
    formula:Bipolar Nanoflake:100000.0
    formula:Optimized Device:99924.2
    formula:Integrated Device:63163.4
    formula:Device:54077.1
    formula:Polyester Pack:33100.8
    formula:Polyester:32870.7
    formula:Refined Solvent:285.2
    formula:Sugar:237.4
    formula:Sugar Pack:236.5
    formula:Polyketon:190.0
    formula:Oriron:190.0
    formula:Aketon:189.2
    formula:Oriron Cluster:189.2
    formula:Polymerized Gel:158.5
    formula:Crystalline Circuit:158.5
    formula:Nucleic Crystal Sinter:113.7
    formula:Crystalline Electronic Unit:113.7
    formula:D32 Steel:101.0
    formula:Polymerization Preparation:101.0
Req: 100000.000Crystalline Electronic Unit
    san=43682445.592604086
    stage:10-3:735803.0
    stage:11-14:717786.9
    stage:R8-11:302564.7
    stage:5-7:190989.0
    stage:7-15:146712.1
    stage:10-11:6317.2
    formula:Polymerized Gel:162096.4
    formula:Oriron Cluster:127925.0
    formula:Crystalline Electronic Unit:100000.0
    formula:Sugar Pack:96689.0
    formula:Crystalline Circuit:88204.5
    formula:Incandescent Alloy Block:66610.6
    formula:Sugar:63327.9
    formula:Oriron:49316.0
    formula:Orirock Cluster:26682.4
    formula:Orirock Cube:22051.2
    formula:Integrated Device:13219.3
    formula:Orirock Concentration:8982.8
    formula:Device:8663.4
    formula:Manganese Trihydrate:706.8
    formula:Polymerization Preparation:374.2
    formula:Transmuted Salt Agglomerate:331.1
    formula:Keton Colloid:276.4
    formula:White Horse Kohl:263.2
    formula:Polyester Pack:247.0
    formula:Aketon:197.6
    formula:Polyester:151.2
    formula:Polyketon:121.0
    formula:D32 Steel:113.9
    formula:Bipolar Nanoflake:75.9
    formula:Nucleic Crystal Sinter:56.9
    formula:RMA70-24:12.7
Req: 100000.000D32 Steel
    san=32790916.3953983
    stage:10-7:379540.4
    stage:4-8:250907.2
    stage:7-18:224592.5
    stage:4-9:215501.4
    stage:GT-5:136593.3
    stage:10-6:118903.2
    stage:11-7:105221.0
    stage:WD-8:73596.7
    stage:WD-6:72711.7
    formula:D32 Steel:100000.0
    formula:RMA70-24:90617.1
    formula:Grindstone Pentahydrate:88556.2
    formula:Manganese Trihydrate:81699.6
    formula:Aketon:80884.2
    formula:Polyester:74800.0
    formula:Orirock Cluster:68199.0
    formula:Orirock Cube:65749.9
    formula:Polyketon:51518.6
    formula:Polyester Pack:35812.7
    formula:Integrated Device:34034.3
    formula:Device:25875.8
    formula:Refined Solvent:4681.9
    formula:Crystalline Circuit:298.9
    formula:Transmuted Salt Agglomerate:239.1
    formula:Sugar Pack:230.6
    formula:Sugar:229.9
    formula:Oriron Cluster:184.5
    formula:Oriron:183.9
    formula:Nucleic Crystal Sinter:113.6
    formula:Polymerization Preparation:100.9
    formula:Crystalline Electronic Unit:64.9
    formula:Bipolar Nanoflake:64.9
Req: 100000.000Nucleic Crystal Sinter
    san=45791067.17256103
    stage:12-17:494558.9
    stage:10-3:446242.2
    stage:11-8:395111.8
    stage:12-10:280368.9
    stage:11-3:215307.9
    stage:9-19:176769.7
    stage:9-14:115723.2
    formula:Refined Solvent:160566.7
    formula:Nucleic Crystal Sinter:100000.0
    formula:Transmuted Salt Agglomerate:88464.5
    formula:Cutting Fluid Solution:74541.5
    formula:Polyester:65192.6
    formula:Sugar Pack:61320.6
    formula:Orirock Cluster:53225.9
    formula:Oriron Cluster:48883.2
    formula:Polyketon:47509.9
    formula:Orirock Cube:44135.5
    formula:Sugar:38790.5
    formula:Oriron:30979.4
    formula:Oriron Block:28122.3
    formula:Integrated Device:26866.6
    formula:Polyester Pack:25780.5
    formula:Aketon:20166.9
    formula:Orirock Concentration:17905.4
    formula:Device:17456.6
    formula:Grindstone Pentahydrate:7981.5
    formula:Manganese Trihydrate:7608.1
    formula:Crystalline Electronic Unit:101.0
    formula:D32 Steel:101.0
    formula:Polymerization Preparation:101.0
    formula:Bipolar Nanoflake:64.9
Req: 100000.000Polymerization Preparation
    san=32319282.26433238
    stage:1-7:1480267.4
    stage:10-4:350488.7
    stage:10-11:328664.7
    stage:10-16:164571.9
    stage:OF-F3:136035.6
    stage:3-4:113397.4
    stage:WD-6:66130.6
    formula:Orirock Cluster:398912.7
    formula:Polymerization Preparation:100000.0
    formula:Keton Colloid:99899.0
    formula:Orirock Concentration:99848.6
    formula:Oriron Block:85696.4
    formula:Orirock Cube:81630.5
    formula:Polyester Pack:54496.3
    formula:Integrated Device:53991.8
    formula:Polyester:44241.9
    formula:Sugar:41737.5
    formula:Oriron:33050.2
    formula:Device:26336.3
    formula:Sugar Pack:25892.1
    formula:Polyketon:23381.6
    formula:Oriron Cluster:20739.2
    formula:Aketon:6199.2
    formula:Refined Solvent:181.9
    formula:Nucleic Crystal Sinter:120.8
    formula:Crystalline Circuit:107.0
    formula:Cutting Fluid Solution:107.0
    formula:D32 Steel:101.0
    formula:Bipolar Nanoflake:64.9
    formula:Crystalline Electronic Unit:64.9
Req: 100000.000Drill Battle Record
    san=140726.4690882303
    stage:0-2:23454.4
Req: 100000.000Frontline Battle Record
    san=299117.9353152565
    stage:WR-3:24926.5
Req: 100000.000Tactical Battle Record
    san=592829.4573643411
    stage:12-9:28230.0
Req: 100000.000Strategic Battle Record
    san=900000.0
    stage:LS-6:25000.0
Req: 100000.000Caster Chip
    san=3594735.9230390685
    stage:PR-B-1:199707.6
Req: 100000.000Defender Chip
    san=3598038.3909452427
    stage:PR-A-1:199891.0
Req: 100000.000Guard Chip
    san=3601809.185650392
    stage:PR-D-1:200100.5
Req: 100000.000Medic Chip
    san=3601968.6734831985
    stage:PR-A-1:200109.4
Req: 100000.000Sniper Chip
    san=3605279.516840357
    stage:PR-B-1:200293.3
Req: 100000.000Specialist Chip
    san=3598192.630941922
    stage:PR-D-1:199899.6
Req: 100000.000Supporter Chip
    san=3598684.924933054
    stage:PR-C-1:199926.9
Req: 100000.000Vanguard Chip
    san=3601316.0365596497
    stage:PR-C-1:200073.1
Req: 100000.000Caster Chip Pack
    san=7202929.541932183
    stage:PR-B-2:200081.4
Req: 100000.000Defender Chip Pack
    san=7190394.555230863
    stage:PR-A-2:199733.2
Req: 100000.000Guard Chip Pack
    san=7201053.306211163
    stage:PR-D-2:200029.3
Req: 100000.000Medic Chip Pack
    san=7209631.142381973
    stage:PR-A-2:200267.5
Req: 100000.000Sniper Chip Pack
    san=7197072.840078296
    stage:PR-B-2:199918.7
Req: 100000.000Specialist Chip Pack
    san=7198947.001880353
    stage:PR-D-2:199970.8
Req: 100000.000Supporter Chip Pack
    san=7194518.210910887
    stage:PR-C-2:199847.7
Req: 100000.000Vanguard Chip Pack
    san=7205490.149044428
    stage:PR-C-2:200152.5
Req: 100000.000Furniture
    san=1800000.0
    stage:WD-1:150000.0
Req: 100000.000Pure Gold
    san=1800000.0
    stage:WD-5:150000.0
Req: 100000.000Incandescent Alloy
    san=3783496.739529074
    stage:TW-6:252233.1
    formula:Sugar:13169.9
    formula:Sugar Pack:11556.2
    formula:Oriron:10343.8
    formula:Polyketon:10313.8
    formula:Oriron Cluster:9201.6
    formula:Aketon:9127.8
    formula:Orirock Cube:53.6
    formula:Orirock Cluster:39.1
    formula:Polyester:35.7
    formula:Polyester Pack:32.6
    formula:Device:21.4
    formula:Integrated Device:19.6
    formula:Oriron Block:19.6
    formula:Orirock Concentration:9.8
    formula:Polyester Lump:0.0
    formula:Keton Colloid:0.0
    formula:Grindstone Pentahydrate:0.0
    formula:Transmuted Salt Agglomerate:0.0
    formula:Cutting Fluid Solution:0.0
    formula:Refined Solvent:0.0
Req: 100000.000Incandescent Alloy Block
    san=12261132.26146644
    stage:3-3:280262.5
    stage:12-12:229878.7
    stage:11-7:153797.2
    formula:Incandescent Alloy Block:90020.0
    formula:Orirock Cluster:49409.4
    formula:Orirock Cube:48056.6
    formula:Integrated Device:24418.4
    formula:Device:18585.0
    formula:Orirock Concentration:15223.7
    formula:Polyester:13261.1
    formula:Polyester Pack:13194.0
    formula:Polyester Lump:190.7
    formula:Sugar Pack:90.0
    formula:Sugar:84.3
    formula:Sugar Lump:74.7
    formula:Aketon:72.0
    formula:Oriron Cluster:72.0
    formula:Refined Solvent:71.3
    formula:Oriron:67.5
    formula:Polyketon:67.5
    formula:White Horse Kohl:53.5
    formula:Nucleic Crystal Sinter:35.7
    formula:Cutting Fluid Solution:35.6
    formula:Transmuted Salt Agglomerate:35.6
    formula:Manganese Trihydrate:22.0
    formula:D32 Steel:0.0
    formula:Polymerization Preparation:0.0
    formula:Bipolar Nanoflake:0.0
Req: 100000.000Carbon Stick
    san=375000.0
    stage:SK-2:25000.0
Req: 100000.000Carbon Brick
    san=800366.6698830691
    stage:SK-3:40018.3
Req: 100000.000Carbon Brick
    san=1000004.0253435631
    stage:SK-5:33333.5
Req: 100000.000Crystalline Component
    san=3609100.1883151955
    stage:R8-11:171861.9
    formula:Orirock Cluster:15014.5
    formula:Orirock Cube:12424.1
    formula:Integrated Device:7438.0
    formula:Orirock Concentration:4994.3
    formula:Device:4880.4
    formula:Polyester Pack:22.4
    formula:Sugar Pack:22.4
    formula:Polyester:18.3
    formula:Sugar:18.3
    formula:Aketon:17.9
    formula:Oriron Cluster:17.9
    formula:Polyketon:14.6
    formula:Oriron:14.6
    formula:Polyester Lump:11.5
    formula:Oriron Block:6.4
    formula:Keton Colloid:5.7
    formula:Polymerized Gel:5.7
    formula:Grindstone Pentahydrate:5.1
    formula:Transmuted Salt Agglomerate:4.5
    formula:White Horse Kohl:4.2
    formula:Refined Solvent:0.6
Req: 100000.000Crystalline Circuit
    san=14650392.516579673
    stage:R8-11:303251.1
    stage:12-5:235549.1
    stage:TW-6:222372.5
    formula:Crystalline Circuit:88279.0
    formula:Orirock Cluster:47231.0
    formula:Orirock Cube:38706.3
    formula:Integrated Device:23313.4
    formula:Orirock Concentration:15682.5
    formula:Device:15372.1
    formula:Sugar:11667.9
    formula:Sugar Pack:10258.2
    formula:Oriron:9164.9
    formula:Polyketon:9138.5
    formula:Oriron Cluster:8168.3
    formula:Aketon:8103.3
    formula:Oriron Block:245.7
    formula:Polymerization Preparation:117.7
    formula:Keton Colloid:117.5
    formula:Polyester Pack:98.9
    formula:Transmuted Salt Agglomerate:94.0
    formula:Polyester:88.6
    formula:White Horse Kohl:88.1
    formula:Grindstone Pentahydrate:61.7
    formula:Bipolar Nanoflake:44.2
    formula:Optimized Device:44.0
    formula:D32 Steel:0.2
    formula:Nucleic Crystal Sinter:0.1
    formula:RMA70-24:0.0
Req: 100000.000Compound Cutting Fluid
    san=4461583.776633726
    stage:10-17:185899.3
    formula:Orirock Cluster:14665.5
    formula:Orirock Cube:13704.8
    formula:Integrated Device:7314.9
    formula:Orirock Concentration:5812.2
    formula:Device:5130.8
    formula:Sugar Pack:22.4
    formula:Polyester Pack:22.4
    formula:Polyester:19.9
    formula:Sugar:19.9
    formula:Oriron Cluster:17.9
    formula:Aketon:17.9
    formula:Polyketon:15.9
    formula:Oriron:15.9
    formula:Polyester Lump:11.5
    formula:Oriron Block:7.6
    formula:Keton Colloid:6.5
    formula:Grindstone Pentahydrate:5.9
    formula:Transmuted Salt Agglomerate:5.3
    formula:White Horse Kohl:4.9
    formula:Crystalline Circuit:3.3
    formula:Polymerized Gel:3.3
    formula:Sugar Lump:0.1
Req: 100000.000Cutting Fluid Solution
    san=11852036.966936398
    stage:9-19:225216.6
    stage:12-17:189244.7
    stage:R8-11:149921.5
    formula:Cutting Fluid Solution:90301.6
    formula:Polyester:31167.2
    formula:Orirock Cluster:29569.5
    formula:Polyketon:24894.5
    formula:Orirock Cube:24492.9
    formula:Integrated Device:14844.2
    formula:Polyester Pack:12571.8
    formula:Aketon:10064.4
    formula:Device:9709.8
    formula:Orirock Concentration:8264.9
    formula:Polyester Lump:8204.0
    formula:Optimized Device:3219.6
    formula:Keton Colloid:124.0
    formula:Transmuted Salt Agglomerate:99.2
    formula:Sugar:95.2
    formula:Polymerized Gel:82.7
    formula:Sugar Pack:76.8
    formula:Oriron:76.2
    formula:Oriron Cluster:61.5
    formula:Polymerization Preparation:51.5
    formula:Oriron Block:51.4
    formula:Crystalline Electronic Unit:41.4
    formula:Incandescent Alloy Block:41.3
    formula:D32 Steel:0.1
    formula:Bipolar Nanoflake:0.1
Req: 100000.000Damaged Device
    san=802395.4539147695
    stage:2-3:66866.3
    formula:Orirock Cube:9230.2
    formula:Polyester:6100.8
    formula:Sugar:16.2
    formula:Oriron:12.9
    formula:Polyketon:12.9
Req: 100000.000Device
    san=1559961.9104449446
    stage:TW-5:103997.5
    formula:Orirock Cube:7498.7
    formula:Orirock Cluster:5758.0
    formula:Polyester:5083.1
    formula:Polyester Pack:4822.5
    formula:Device:3030.5
    formula:Sugar:16.5
    formula:Polyketon:13.2
    formula:Oriron:13.2
    formula:Sugar Pack:12.5
    formula:Aketon:10.0
    formula:Oriron Cluster:10.0
Req: 100000.000Integrated Device
    san=4693428.076926968
    stage:11-7:223496.6
    formula:Orirock Cluster:19467.5
    formula:Orirock Cube:16083.6
    formula:Integrated Device:9707.8
    formula:Orirock Concentration:6524.4
    formula:Device:6352.2
    formula:Polyester Pack:29.0
    formula:Sugar Pack:29.0
    formula:Polyester:23.7
    formula:Sugar:23.7
    formula:Aketon:23.2
    formula:Oriron Cluster:23.2
    formula:Polyester Lump:19.1
    formula:Polyketon:19.0
    formula:Oriron:19.0
    formula:Polymerized Gel:7.4
    formula:Transmuted Salt Agglomerate:5.9
    formula:Keton Colloid:5.7
    formula:Cutting Fluid Solution:5.5
    formula:Sugar Lump:1.6
    formula:Refined Solvent:0.7
Req: 100000.000Optimized Device
    san=12350016.28790176
    stage:3-3:311386.5
    stage:5-10:268216.0
    stage:10-6:97461.1
    formula:Orirock Cluster:125713.6
    formula:Optimized Device:100000.0
    formula:Orirock Cube:29655.5
    formula:Polyester:14699.1
    formula:Polyester Pack:14695.5
    formula:Integrated Device:13067.9
    formula:Device:11626.5
    formula:Polyester Lump:222.0
    formula:Sugar Pack:136.2
    formula:Aketon:109.0
    formula:Oriron Cluster:109.0
    formula:Sugar Lump:96.4
    formula:Polymerized Gel:73.5
    formula:Refined Solvent:67.8
    formula:Sugar:59.1
    formula:White Horse Kohl:50.9
    formula:Polyketon:47.3
    formula:Oriron:47.3
    formula:Crystalline Circuit:39.6
    formula:Nucleic Crystal Sinter:33.9
    formula:Cutting Fluid Solution:33.9
    formula:Transmuted Salt Agglomerate:33.9
    formula:Manganese Trihydrate:8.3
    formula:Crystalline Electronic Unit:0.0
    formula:D32 Steel:0.0
    formula:Polymerization Preparation:0.0
Req: 100000.000Ester
    san=468749.459172345
    stage:DH-4:39062.5
    formula:Orirock Cube:5232.9
    formula:Device:2131.8
    formula:Sugar:7.8
    formula:Polyketon:6.2
    formula:Oriron:6.2
Req: 100000.000Polyester
    san=952306.464711725
    stage:S3-2:63487.1
    formula:Orirock Cube:4542.1
    formula:Orirock Cluster:3570.7
    formula:Polyester:2935.3
    formula:Integrated Device:1856.4
    formula:Device:1811.6
    formula:Sugar:9.8
    formula:Polyketon:7.8
    formula:Oriron:7.8
    formula:Sugar Pack:6.7
    formula:Oriron Cluster:5.4
    formula:Aketon:5.4
Req: 100000.000Polyester Pack
    san=2915377.7544088773
    stage:WD-6:194358.5
    formula:Orirock Cube:13756.6
    formula:Orirock Cluster:10874.4
    formula:Polyester Pack:9478.2
    formula:Polyester:9407.5
    formula:Integrated Device:5485.3
    formula:Device:5421.0
    formula:Orirock Concentration:2719.7
    formula:Sugar:30.2
    formula:Sugar Pack:28.0
    formula:Oriron:24.1
    formula:Polyketon:24.1
    formula:Aketon:22.4
    formula:Oriron Cluster:22.4
    formula:Keton Colloid:3.1
    formula:Transmuted Salt Agglomerate:2.5
    formula:Cutting Fluid Solution:2.3
    formula:Grindstone Pentahydrate:2.1
    formula:Polymerized Gel:2.1
    formula:Incandescent Alloy Block:0.6
    formula:Crystalline Circuit:0.4
    formula:Refined Solvent:0.3
Req: 100000.000Polyester Lump
    san=12058171.14359337
    stage:3-8:372413.8
    stage:GT-5:198772.7
    stage:3-1:158208.8
    formula:Polyester Lump:87955.9
    formula:Polyester:60819.6
    formula:Polyketon:47861.7
    formula:Polyester Pack:32058.8
    formula:Aketon:24342.4
    formula:Orirock Cube:14639.3
    formula:Orirock Cluster:11468.0
    formula:Sugar:8387.4
    formula:Sugar Pack:7229.4
    formula:Oriron:6585.5
    formula:Oriron Cluster:5800.5
    formula:Integrated Device:5716.2
    formula:Device:5699.3
    formula:Grindstone Pentahydrate:3836.8
    formula:Orirock Concentration:2908.1
    formula:Cutting Fluid Solution:2631.0
    formula:Sugar Lump:109.7
    formula:Transmuted Salt Agglomerate:87.7
    formula:Polymerized Gel:54.9
    formula:Crystalline Electronic Unit:27.4
    formula:Crystalline Circuit:27.4
    formula:Incandescent Alloy Block:27.4
    formula:Refined Solvent:11.0
    formula:Nucleic Crystal Sinter:5.5
    formula:Polymerization Preparation:0.0
    formula:D32 Steel:0.0
    formula:Bipolar Nanoflake:0.0
Req: 100000.000Coagulating Gel
    san=5983595.17810713
    stage:12-5:284933.1
    formula:Orirock Cluster:25043.8
    formula:Orirock Cube:20245.6
    formula:Integrated Device:12304.3
    formula:Orirock Concentration:8281.2
    formula:Device:8155.1
    formula:Sugar Pack:37.1
    formula:Polyester Pack:37.1
    formula:Polyester:30.0
    formula:Sugar:30.0
    formula:Oriron Cluster:29.7
    formula:Aketon:29.7
    formula:Polyketon:24.0
    formula:Oriron:24.0
    formula:Oriron Block:19.5
    formula:Polyester Lump:14.6
    formula:Keton Colloid:9.4
    formula:Incandescent Alloy Block:8.4
    formula:Transmuted Salt Agglomerate:7.5
    formula:White Horse Kohl:7.0
Req: 100000.000Polymerized Gel
    san=11363263.778216204
    stage:10-3:260458.8
    stage:TW-6:196430.8
    stage:10-11:122798.7
    formula:Polymerized Gel:86628.9
    formula:Sugar Pack:31363.8
    formula:Oriron Cluster:25130.0
    formula:Sugar:24788.5
    formula:Oriron:19265.3
    formula:Polyketon:8053.8
    formula:Aketon:7139.4
    formula:Keton Colloid:3620.6
    formula:Manganese Trihydrate:114.5
    formula:Transmuted Salt Agglomerate:91.6
    formula:Orirock Cube:82.5
    formula:Orirock Cluster:77.0
    formula:Cutting Fluid Solution:76.3
    formula:Polyester Pack:64.1
    formula:Polymerization Preparation:57.5
    formula:Orirock Concentration:57.4
    formula:Polyester:55.0
    formula:Integrated Device:38.5
    formula:Device:33.0
    formula:D32 Steel:0.1
    formula:Bipolar Nanoflake:0.0
    formula:Nucleic Crystal Sinter:0.0
Req: 100000.000Grindstone
    san=4505217.901214403
    stage:9-16:250289.9
    formula:Oriron Cluster:30107.3
    formula:Orirock Cluster:28.6
    formula:Polyester Pack:23.9
    formula:Sugar Pack:23.9
    formula:Aketon:19.1
    formula:Oriron Block:14.3
    formula:Integrated Device:14.3
    formula:Orirock Concentration:7.2
    formula:Polyester Lump:0.0
    formula:Keton Colloid:0.0
    formula:Transmuted Salt Agglomerate:0.0
    formula:Cutting Fluid Solution:0.0
    formula:Polymerized Gel:0.0
    formula:Crystalline Circuit:0.0
    formula:Refined Solvent:0.0
Req: 100000.000Grindstone Pentahydrate
    san=11674222.32235432
    stage:7-15:299778.5
    stage:5-7:287863.2
    stage:S3-3:15538.8
    formula:Grindstone Pentahydrate:100000.0
    formula:Oriron Cluster:96178.2
    formula:Sugar Pack:19520.4
    formula:Sugar:17566.6
    formula:Oriron:13990.8
    formula:Polyketon:661.7
    formula:Aketon:643.5
    formula:Keton Colloid:354.7
    formula:Manganese Trihydrate:127.3
    formula:Orirock Cluster:120.7
    formula:Polyester Pack:100.6
    formula:Refined Solvent:64.1
    formula:Integrated Device:60.3
    formula:Orirock Cube:51.0
    formula:Orirock Concentration:49.0
    formula:RMA70-24:47.1
    formula:Transmuted Salt Agglomerate:37.7
    formula:Crystalline Circuit:37.7
    formula:Cutting Fluid Solution:37.7
    formula:Polyester:34.0
    formula:Nucleic Crystal Sinter:32.1
    formula:Device:20.4
    formula:Polymerization Preparation:0.0
    formula:Bipolar Nanoflake:0.0
    formula:Crystalline Electronic Unit:0.0
    formula:White Horse Kohl:0.0
Req: 100000.000Diketon
    san=622749.7550756482
    stage:BI-5:51895.8
    formula:Sugar:4513.8
    formula:Oriron:4403.1
    formula:Orirock Cube:14.1
    formula:Polyester:9.4
    formula:Device:5.7
Req: 100000.000Polyketon
    san=1220459.6644791756
    stage:3-7:81364.0
    formula:Sugar:4336.8
    formula:Sugar Pack:3791.4
    formula:Polyketon:3715.7
    formula:Oriron:3422.5
    formula:Oriron Cluster:3032.8
    formula:Orirock Cube:18.2
    formula:Polyester:12.1
    formula:Orirock Cluster:10.1
    formula:Polyester Pack:8.4
    formula:Device:7.3
    formula:Integrated Device:5.1
Req: 100000.000Aketon
    san=3690264.0171330385
    stage:3-1:246017.6
    formula:Sugar:12841.7
    formula:Sugar Pack:11108.4
    formula:Polyketon:10128.5
    formula:Oriron:10079.9
    formula:Aketon:9043.2
    formula:Oriron Cluster:8913.0
    formula:Orirock Cube:52.4
    formula:Orirock Cluster:38.1
    formula:Polyester:34.9
    formula:Polyester Pack:31.7
    formula:Device:20.9
    formula:Oriron Block:19.1
    formula:Integrated Device:19.0
    formula:Orirock Concentration:9.5
    formula:Sugar Lump:0.0
    formula:Polymerized Gel:0.0
    formula:Transmuted Salt Agglomerate:0.0
    formula:Cutting Fluid Solution:0.0
    formula:Incandescent Alloy Block:0.0
    formula:Refined Solvent:0.0
Req: 100000.000Keton Colloid
    san=13166095.78137539
    stage:3-1:388701.1
    stage:7-12:195352.4
    stage:10-16:181868.3
    formula:Keton Colloid:100000.0
    formula:Aketon:56178.0
    formula:Polyester Pack:35169.1
    formula:Sugar:20289.6
    formula:Sugar Pack:17611.9
    formula:Polyketon:16002.7
    formula:Oriron:15926.0
    formula:Oriron Cluster:14131.1
    formula:Oriron Block:137.2
    formula:Orirock Cluster:133.3
    formula:Polymerized Gel:84.6
    formula:Cutting Fluid Solution:84.6
    formula:Orirock Cube:82.7
    formula:Orirock Concentration:75.6
    formula:Integrated Device:66.7
    formula:Polyester:55.1
    formula:Device:33.1
    formula:Crystalline Electronic Unit:14.1
    formula:Crystalline Circuit:14.1
    formula:Incandescent Alloy Block:14.1
    formula:Refined Solvent:2.8
    formula:Nucleic Crystal Sinter:0.0
    formula:D32 Steel:0.0
    formula:Bipolar Nanoflake:0.0
Req: 100000.000Loxic Kohl
    san=3394489.5707501466
    stage:GT-5:226299.3
    formula:Orirock Cube:16460.8
    formula:Orirock Cluster:12950.2
    formula:Polyester Pack:10690.2
    formula:Polyester:10639.3
    formula:Integrated Device:6454.8
    formula:Device:6406.3
    formula:Orirock Concentration:3237.6
    formula:Sugar:35.4
    formula:Sugar Pack:32.7
    formula:Polyketon:28.3
    formula:Oriron:28.3
    formula:Aketon:26.1
    formula:Oriron Cluster:26.1
    formula:Oriron Block:13.7
    formula:Keton Colloid:3.7
    formula:Transmuted Salt Agglomerate:2.9
    formula:Cutting Fluid Solution:2.8
    formula:Optimized Device:2.6
    formula:Polymerized Gel:2.5
    formula:Incandescent Alloy Block:0.7
    formula:Crystalline Circuit:0.5
    formula:Refined Solvent:0.4
Req: 100000.000White Horse Kohl
    san=10978810.61139343
    stage:2-10:320187.7
    stage:R8-2:253807.1
    stage:MB-6:107164.5
    formula:White Horse Kohl:89097.5
    formula:Sugar:36794.7
    formula:Sugar Pack:35259.9
    formula:Oriron:29118.4
    formula:Oriron Cluster:28148.4
    formula:Polyketon:17693.4
    formula:Aketon:15592.4
    formula:Orirock Cube:132.4
    formula:Orirock Cluster:101.6
    formula:Incandescent Alloy Block:90.4
    formula:Polyester:88.3
    formula:Polyester Pack:84.6
    formula:Orirock Concentration:63.0
    formula:Polymerized Gel:60.2
    formula:Device:53.0
    formula:Integrated Device:50.8
    formula:Oriron Block:35.7
    formula:Crystalline Electronic Unit:30.1
    formula:Crystalline Circuit:30.1
    formula:Refined Solvent:0.0
    formula:Nucleic Crystal Sinter:0.0
    formula:D32 Steel:0.0
    formula:Polymerization Preparation:0.0
Req: 100000.000Manganese Ore
    san=3823547.3875074806
    stage:10-16:182073.7
    formula:Polyester Pack:35125.4
    formula:Orirock Cluster:33.4
    formula:Sugar Pack:27.8
    formula:Aketon:22.3
    formula:Oriron Cluster:22.3
    formula:Integrated Device:16.7
    formula:Oriron Block:11.1
    formula:Orirock Concentration:8.3
    formula:Polyester Lump:0.0
    formula:Transmuted Salt Agglomerate:0.0
    formula:Cutting Fluid Solution:0.0
    formula:Optimized Device:0.0
    formula:Polymerized Gel:0.0
    formula:Incandescent Alloy Block:0.0
    formula:Crystalline Circuit:0.0
    formula:Refined Solvent:0.0
Req: 100000.000Manganese Trihydrate
    san=11585771.288052263
    stage:10-16:363934.2
    stage:GT-5:226010.6
    stage:WD-6:36866.2
    formula:Manganese Trihydrate:100000.0
    formula:Polyester Pack:82684.1
    formula:Orirock Cube:19049.1
    formula:Orirock Cluster:15063.0
    formula:Polyester:12410.1
    formula:Integrated Device:7520.4
    formula:Device:7426.4
    formula:Orirock Concentration:3800.9
    formula:Transmuted Salt Agglomerate:93.6
    formula:Sugar Pack:93.6
    formula:Grindstone Pentahydrate:81.9
    formula:Oriron Cluster:74.8
    formula:Aketon:74.8
    formula:Polymerized Gel:70.2
    formula:Cutting Fluid Solution:70.2
    formula:Sugar:41.0
    formula:Oriron:32.8
    formula:Polyketon:32.8
    formula:Crystalline Electronic Unit:23.4
    formula:Crystalline Circuit:23.4
    formula:Incandescent Alloy Block:23.4
    formula:RMA70-24:17.6
    formula:Refined Solvent:11.7
    formula:Nucleic Crystal Sinter:5.9
    formula:Polymerization Preparation:0.0
    formula:Bipolar Nanoflake:0.0
Req: 100000.000Orirock
    san=320128.2368058081
    stage:S2-5:26677.4
    formula:Polyester:2320.1
    formula:Device:1513.6
    formula:Sugar:4.0
    formula:Polyketon:3.2
    formula:Oriron:3.2
Req: 100000.000Orirock Cube
    san=466940.3278958952
    stage:1-7:77823.4
    formula:Orirock Cube:3100.5
    formula:Polyester:1539.9
    formula:Sugar:1539.3
    formula:Oriron:1226.4
    formula:Polyketon:1226.2
    formula:Device:913.4
    formula:Polyester Pack:386.2
    formula:Sugar Pack:386.1
    formula:Oriron Cluster:307.6
    formula:Aketon:307.6
    formula:Integrated Device:229.1
Req: 100000.000Orirock Cluster
    san=2332450.8306515436
    stage:1-7:388741.8
    formula:Orirock Cluster:99998.6
    formula:Orirock Cube:15487.8
    formula:Polyester:7692.0
    formula:Sugar:7689.2
    formula:Oriron:6126.3
    formula:Polyketon:6125.2
    formula:Device:4562.8
    formula:Polyester Pack:2008.6
    formula:Sugar Pack:2007.9
    formula:Oriron Cluster:1600.0
    formula:Aketon:1599.8
    formula:Integrated Device:1192.0
    formula:Oriron Block:799.8
    formula:Polyester Lump:1.0
    formula:Keton Colloid:0.9
    formula:Transmuted Salt Agglomerate:0.7
    formula:Cutting Fluid Solution:0.7
    formula:Grindstone Pentahydrate:0.6
    formula:Polymerized Gel:0.6
    formula:Incandescent Alloy Block:0.2
    formula:Crystalline Circuit:0.1
    formula:Refined Solvent:0.1
Req: 100000.000Orirock Concentration
    san=9325844.730591502
    stage:1-7:1554307.5
    formula:Orirock Cluster:399824.9
    formula:Orirock Concentration:99999.9
    formula:Orirock Cube:61924.9
    formula:Polyester:30755.1
    formula:Sugar:30743.6
    formula:Oriron:24494.7
    formula:Polyketon:24490.2
    formula:Device:18243.4
    formula:Polyester Pack:8031.0
    formula:Sugar Pack:8028.1
    formula:Oriron Cluster:6397.4
    formula:Aketon:6396.3
    formula:Integrated Device:4766.2
    formula:Oriron Block:3204.5
    formula:Keton Colloid:116.6
    formula:Polyester Lump:113.7
    formula:Transmuted Salt Agglomerate:70.0
    formula:Cutting Fluid Solution:70.0
    formula:Grindstone Pentahydrate:58.3
    formula:Polymerized Gel:46.7
    formula:Incandescent Alloy Block:46.6
    formula:Refined Solvent:35.0
    formula:Crystalline Electronic Unit:23.4
    formula:Crystalline Circuit:23.3
    formula:Nucleic Crystal Sinter:17.5
    formula:White Horse Kohl:17.5
    formula:D32 Steel:0.0
    formula:Bipolar Nanoflake:0.0
Req: 100000.000Oriron Shard
    san=610222.3730000654
    stage:SN-5:50851.9
    formula:Sugar:4461.5
    formula:Polyketon:3454.3
    formula:Orirock Cube:12.5
    formula:Polyester:8.4
    formula:Device:5.0
Req: 100000.000Oriron
    san=1193990.881210238
    stage:S3-3:79599.4
    formula:Sugar:4173.7
    formula:Sugar Pack:3621.1
    formula:Oriron:3259.6
    formula:Polyketon:3259.4
    formula:Aketon:2890.4
    formula:Orirock Cube:16.9
    formula:Polyester:11.3
    formula:Orirock Cluster:9.6
    formula:Polyester Pack:8.0
    formula:Device:6.8
    formula:Integrated Device:4.8
Req: 100000.000Oriron Cluster
    san=4772934.334657097
    stage:S3-3:318195.6
    formula:Oriron Cluster:100000.0
    formula:Sugar:16684.3
    formula:Sugar Pack:14554.4
    formula:Oriron:13030.1
    formula:Polyketon:13029.5
    formula:Aketon:11617.5
    formula:Orirock Cluster:133.4
    formula:Polyester Pack:111.1
    formula:Orirock Cube:67.7
    formula:Integrated Device:66.7
    formula:Polyester:45.1
    formula:Orirock Concentration:33.4
    formula:Device:27.1
    formula:Polyester Lump:0.0
    formula:Keton Colloid:0.0
    formula:Incandescent Alloy Block:0.0
    formula:Transmuted Salt Agglomerate:0.0
    formula:Cutting Fluid Solution:0.0
    formula:Crystalline Circuit:0.0
    formula:Refined Solvent:0.0
    formula:Optimized Device:0.0
Req: 100000.000Oriron Block
    san=14256121.52582112
    stage:10-11:339798.4
    stage:3-4:265459.8
    stage:WD-6:141270.9
    formula:Oriron Block:85316.2
    formula:Orirock Cube:29182.8
    formula:Orirock Cluster:23096.2
    formula:Polyester:19394.7
    formula:Polyester Pack:19394.3
    formula:Sugar Pack:18816.9
    formula:Oriron Cluster:15104.6
    formula:Sugar:12893.1
    formula:Integrated Device:11583.4
    formula:Device:11536.3
    formula:Oriron:10061.8
    formula:Orirock Concentration:5812.6
    formula:Keton Colloid:87.9
    formula:Aketon:73.1
    formula:Polyketon:70.0
    formula:Refined Solvent:54.8
    formula:White Horse Kohl:49.7
    formula:Transmuted Salt Agglomerate:37.7
    formula:Crystalline Circuit:37.7
    formula:Nucleic Crystal Sinter:27.4
    formula:Cutting Fluid Solution:27.4
    formula:D32 Steel:0.0
    formula:Bipolar Nanoflake:0.0
    formula:Crystalline Electronic Unit:0.0
    formula:RMA70-24:0.0
Req: 100000.000RMA70-12
    san=5242900.824685945
    stage:9-19:249661.9
    formula:Polyester:34510.2
    formula:Polyketon:27564.6
    formula:Polyester Pack:13887.4
    formula:Aketon:11117.7
    formula:Orirock Cube:98.4
    formula:Sugar:65.6
    formula:Oriron:52.5
    formula:Orirock Cluster:43.5
    formula:Device:39.4
    formula:Sugar Pack:36.2
    formula:Oriron Cluster:29.0
    formula:Integrated Device:21.7
    formula:Grindstone Pentahydrate:14.5
    formula:Orirock Concentration:10.9
    formula:Oriron Block:7.2
    formula:Polyester Lump:0.0
    formula:Sugar Lump:0.0
    formula:Crystalline Circuit:0.0
    formula:Transmuted Salt Agglomerate:0.0
    formula:Incandescent Alloy Block:0.0
Req: 100000.000RMA70-24
    san=12742245.038965289
    stage:1-7:676351.7
    stage:4-9:299384.9
    stage:3-1:159803.5
    formula:Orirock Cluster:174059.1
    formula:RMA70-24:87105.0
    formula:Polyester:55062.1
    formula:Polyketon:50118.4
    formula:Orirock Cube:27098.6
    formula:Aketon:21854.8
    formula:Sugar:21798.2
    formula:Polyester Pack:20037.2
    formula:Oriron:17269.3
    formula:Sugar Pack:10752.2
    formula:Oriron Cluster:8608.0
    formula:Device:7999.4
    formula:Oriron Block:2162.6
    formula:Integrated Device:2112.3
    formula:Sugar Lump:100.6
    formula:Transmuted Salt Agglomerate:80.5
    formula:Polymerized Gel:50.3
    formula:Crystalline Electronic Unit:25.2
    formula:Crystalline Circuit:25.1
    formula:Incandescent Alloy Block:25.1
    formula:Refined Solvent:15.1
    formula:Nucleic Crystal Sinter:0.0
    formula:Polymerization Preparation:0.0
    formula:Bipolar Nanoflake:0.0
Req: 100000.000Transmuted Salt
    san=6650491.484126349
    stage:11-3:316690.1
    formula:Sugar Pack:18887.1
    formula:Oriron Cluster:15118.1
    formula:Sugar:11872.1
    formula:Oriron:9105.0
    formula:Sugar Lump:6205.0
    formula:Orirock Cluster:39.0
    formula:Orirock Cube:33.3
    formula:Polyester Pack:32.5
    formula:Aketon:26.0
    formula:Polyester:22.2
    formula:Integrated Device:19.5
    formula:Oriron Block:18.4
    formula:Polyketon:17.7
    formula:Device:13.3
    formula:Keton Colloid:12.6
    formula:Orirock Concentration:12.4
    formula:Polyester Lump:7.9
    formula:Incandescent Alloy Block:6.3
    formula:Cutting Fluid Solution:5.3
    formula:Polymerized Gel:4.4
    formula:Refined Solvent:1.1
    formula:Crystalline Circuit:0.9
Req: 100000.000Transmuted Salt Agglomerate
    san=12100575.877398195
    stage:9-18:261065.6
    stage:11-3:257021.5
    stage:MB-6:81383.1
    formula:Transmuted Salt Agglomerate:86246.5
    formula:Sugar Pack:34544.4
    formula:Oriron Cluster:27830.7
    formula:Sugar:23709.3
    formula:Oriron:19695.5
    formula:Polyketon:3358.3
    formula:Aketon:3035.2
    formula:Orirock Cluster:77.0
    formula:Orirock Cube:74.1
    formula:Polyester Pack:64.1
    formula:D32 Steel:58.5
    formula:RMA70-24:58.4
    formula:Grindstone Pentahydrate:58.4
    formula:Manganese Trihydrate:58.4
    formula:Polymerized Gel:58.4
    formula:Polyester Lump:51.1
    formula:Polyester:49.4
    formula:Integrated Device:38.5
    formula:Device:29.6
    formula:Crystalline Electronic Unit:29.3
    formula:Crystalline Circuit:29.2
    formula:Incandescent Alloy Block:29.2
    formula:Orirock Concentration:26.5
    formula:Oriron Block:23.9
    formula:Cutting Fluid Solution:14.6
    formula:Polymerization Preparation:0.1
    formula:Bipolar Nanoflake:0.1
Req: 100000.000Skill Summary - 1
    san=300000.0
    stage:CA-2:20000.0
Req: 100000.000Skill Summary - 2
    san=666666.6666666667
    stage:CA-3:33333.3
Req: 100000.000Skill Summary - 3
    san=1500000.0
    stage:CA-5:50000.0
Req: 100000.000Semi-Synthetic Solvent
    san=6013590.753186569
    stage:12-10:286361.5
    formula:Polyester:41488.3
    formula:Polyketon:28478.7
    formula:Polyester Pack:16099.8
    formula:Aketon:12407.0
    formula:Cutting Fluid Solution:3172.7
    formula:Orirock Cube:110.9
    formula:Sugar:74.0
    formula:Oriron:59.2
    formula:Orirock Cluster:49.3
    formula:Device:44.4
    formula:Sugar Pack:41.1
    formula:Oriron Cluster:32.9
    formula:RMA70-24:27.4
    formula:Integrated Device:24.7
    formula:Grindstone Pentahydrate:24.4
    formula:White Horse Kohl:4.1
    formula:Sugar Lump:3.6
    formula:Polymerized Gel:3.3
    formula:Oriron Block:2.6
    formula:Incandescent Alloy Block:0.4
Req: 100000.000Refined Solvent
    san=13774361.545139674
    stage:12-10:246579.1
    stage:12-5:232195.5
    stage:10-17:155004.0
    formula:Refined Solvent:86217.6
    formula:Polyester:35765.7
    formula:Orirock Cluster:32679.2
    formula:Orirock Cube:28021.1
    formula:Polyketon:24555.2
    formula:Integrated Device:16147.4
    formula:Polyester Pack:13912.0
    formula:Device:10962.0
    formula:Aketon:10722.5
    formula:Polyester Lump:9459.2
    formula:Orirock Concentration:8070.9
    formula:Optimized Device:4297.9
    formula:RMA70-24:2855.1
    formula:White Horse Kohl:240.9
    formula:Grindstone Pentahydrate:192.7
    formula:Incandescent Alloy Block:125.3
    formula:Bipolar Nanoflake:120.6
    formula:Sugar:104.7
    formula:Sugar Pack:84.3
    formula:Oriron:83.8
    formula:Oriron Cluster:67.4
    formula:D32 Steel:62.8
    formula:Manganese Trihydrate:62.6
    formula:Polymerization Preparation:0.2
    formula:Crystalline Electronic Unit:0.2
Req: 100000.000Sugar Substitute
    san=494344.9435997545
    stage:GT-4:41195.4
    formula:Polyketon:3707.8
    formula:Oriron:3130.2
    formula:Orirock Cube:10.8
    formula:Polyester:7.2
    formula:Device:4.3
Req: 100000.000Sugar
    san=954751.7456862202
    stage:S3-1:63650.1
    formula:Sugar:3344.0
    formula:Oriron:2621.9
    formula:Polyketon:2575.4
    formula:Aketon:2285.7
    formula:Oriron Cluster:2281.1
    formula:Orirock Cube:13.5
    formula:Polyester:9.0
    formula:Orirock Cluster:7.0
    formula:Polyester Pack:5.9
    formula:Device:5.4
    formula:Integrated Device:3.5
Req: 100000.000Sugar Pack
    san=2940286.3307657256
    stage:MB-6:196019.1
    formula:Sugar:10208.3
    formula:Sugar Pack:9022.2
    formula:Polyketon:8015.9
    formula:Oriron:7992.3
    formula:Aketon:7207.2
    formula:Oriron Cluster:7060.0
    formula:Orirock Cube:41.5
    formula:Orirock Cluster:30.4
    formula:Polyester:27.7
    formula:Polyester Pack:25.4
    formula:Device:16.6
    formula:Integrated Device:15.2
    formula:Oriron Block:15.2
    formula:Orirock Concentration:7.6
    formula:Cutting Fluid Solution:0.0
    formula:Grindstone Pentahydrate:0.0
    formula:Polymerized Gel:0.0
    formula:Polyester Lump:0.0
    formula:Manganese Trihydrate:0.0
    formula:Incandescent Alloy Block:0.0
    formula:Refined Solvent:0.0
    formula:Crystalline Circuit:0.0
Req: 100000.000Sugar Lump
    san=11978425.028221162
    stage:11-6:361608.6
    stage:10-16:178493.8
    stage:4-2:35348.6
    formula:Sugar Lump:98663.5
    formula:Oriron Cluster:98066.3
    formula:Polyester Pack:34515.2
    formula:Sugar Pack:2326.1
    formula:Sugar:1989.6
    formula:Oriron:1554.1
    formula:Orirock Cluster:129.2
    formula:Polyester Lump:125.3
    formula:Incandescent Alloy Block:100.2
    formula:Aketon:86.1
    formula:Integrated Device:64.6
    formula:Refined Solvent:63.1
    formula:Orirock Concentration:50.9
    formula:RMA70-24:46.4
    formula:Crystalline Circuit:37.1
    formula:Cutting Fluid Solution:37.1
    formula:Orirock Cube:5.6
    formula:Polyester:3.7
    formula:Polyketon:3.0
    formula:Device:2.2
'''

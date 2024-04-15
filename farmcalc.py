
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
    def check():
        for item in stageitems_all.get('matrix'):
            if item not in stageitems.get('matrix'):
                return False
        return True
    assert check()
    return stages,items,stageitems,formulas

def str_itemlist(itemlist):
    return ' + '.join([str(i) for i in itemlist])

@dataclass
class Stage:
    name:str
    id:str
    san:int
    outs:list #list of Item
    danger_level:float
    def __str__(self):
        return f'{self.name}|{self.dangerLevel}: {self.san}San = {str_itemlist(self.outs)}'
    
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
    dropType:str
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

class Data:
    items={}
    stages={}
    formulas={}
    br_exp={
        '2001':200,
        '2002':400,
        '2003':1000,
        '2004':2000,
    }
    stage_gold={
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
    
def prep_items(items):
    for item in items:
        if item.get('existence').get(Gv.server).get('exist')==True:
            itemId=item.get('itemId')
            obj=ItemType(
                name=item.get('name_i18n').get(Gv.lang),
                id=itemId,
                rarity=item.get('rarity'),
                itemType=item.get('itemType'),
                groupID=item.get('groupID'),
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
        if (dropInfos:=stage.get('dropInfos')):
            if stage.get('existence').get(Gv.server).get('exist')==True:
                stageId=stage.get('stageId')
                stageinfo=stageinfos.get(stageId,{})
                obj=Stage(
                    name=f'stage:{stage.get('code_i18n').get(Gv.lang)}',
                    id=stageId,
                    san=stage.get('apCost'),
                    outs=[],
                    danger_level=dangerLevel(stageinfo),
                )
                for dropInfo in dropInfos:
                    if (itemId:=dropInfo.get('itemId')):
                        obj.outs.append(Item(
                                            item=Data.items[itemId],
                                            dropType=dropInfo.get('dropType'),
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
                            dropType='NOT_DROP',
                            n=1,
                        )],
            out_ex=[],
        )
        for cost in formula.get('costs'):
            itemId_cost=cost.get('id')
            obj.ins.append(Item(
                            item=Data.items[itemId_cost],
                            dropType='NOT_DROP',
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
                                dropType='NOT_DROP',
                                n=n,
                            ))
        Data.formulas[itemId]=obj
        assert totalWeight==weight_all


def res_linprog(nplist,args):
    res=[]
    for idx,(n,obj) in enumerate(zip(list(nplist),list(Data.stages.values())+list(Data.formulas.values()))):
        if n>0:
            if isinstance(obj,Stage):
                print(f'{obj.name}:{n:.1f}')
                res.append((obj.name,n))
            elif isinstance(obj,Formula):
                print(f'{obj.name}:{n:.1f}')
                res.append((obj.name,n))
    san = np.dot(args.get('c'),nplist)
    print(f'{san=}')
    return res,san

def calc():
    def items2array(items):
        d = {item.item.id:item.n for item in items}
        return np.array([n if (n:=d.get(itemtype.id)) else 0 for itemtype in Data.items.values()])
    # x=[]
    # minimize: san(Stages+formulas,x) 
    # subject to: -loot(stages+formulas,x) <= -req
    xkey0=list(Data.stages.keys())
    xkey1=list(Data.formulas.keys())
    xkey=xkey0+xkey1
    
    req={'30115':4}
    req=[Item(
            item=Data.items[itemId],
            dropType='NOT_DROP',
            n=n,
        ) for itemId,n in req.items()]
    ex=0.018
    # integrality=[1]*len(xkey)
    # integrality=3
    integrality=None
    args={
        'c':np.array([stage.san for stage in Data.stages.values()] + [0 for formula in Data.formulas.values()]),
        'A_ub':-np.array(
            [items2array(stage.outs) for stage in Data.stages.values()] + 
            [(items2array(formula.out)+items2array(formula.out_ex)*ex-items2array(formula.ins)) for formula in Data.formulas.values()]
        ).T,
        'b_ub':-items2array(req), 
        'integrality':integrality, #1,3: very slow
        'A_eq':None, 'b_eq':None, 'bounds':(0, None), 'method':'highs', 'callback':None, 'options':None, 'x0':None #default
        }
    res=linprog(**args)
    return res_linprog(res.x,args)

if __name__ == '__main__':
    stages,items,stageitems,formulas = penguin_stats()
    prep_items(items)
    prep_stages(stages)
    prep_stageitems(stageitems)
    prep_formula(formulas)
    # print(*[str(i) for i in Data.items.values()],sep='\n')
    # print(*[str(i) for i in Data.stages.values()],sep='\n')
    # print(*[str(i) for i in Data.formulas.values()],sep='\n')
    
    
    print(*[str(i.danger_level) for i in Data.stages.values()],sep='\n')
    
    
    # exit()
    
    calc()


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

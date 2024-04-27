
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
    from shelve_cache import shelve_cache,shelve_cache_clas
except:
    from mods.shelve_cache import shelve_cache,shelve_cache_clas

try:
    from saveobj import save_json,load_json
except:
    from mods.saveobj import save_json,load_json

import anhrtags

app_path = os.path.dirname(__file__)
os.chdir(app_path)

req={
    'gold':0,
    'exp':0,
    '30125':0,                       #Bipolar Nanoflake                    #4 #ARKPLANNER:
    '30145':0,                       #Crystalline Electronic Unit          #4 #ARKPLANNER:
    '30135':0,                       #D32 Steel                            #4 #ARKPLANNER:
    '30155':0,                       #Nucleic Crystal Sinter               #4 #ARKPLANNER:
    '30115':0,                       #Polymerization Preparation           #4 #ARKPLANNER:
    # '2001':0,                        #Drill Battle Record                  #1 #CARD_EXP:exp
    # '2002':0,                        #Frontline Battle Record              #2 #CARD_EXP:exp
    # '2003':0,                        #Tactical Battle Record               #3 #CARD_EXP:exp
    # '2004':0,                        #Strategic Battle Record              #4 #CARD_EXP:exp
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
    '30023':10,                       #Sugar Pack                           #2 #MATERIAL:sugar
    '30024':0,                       #Sugar Lump                           #3 #MATERIAL:sugar
}

# class Data:
    # server='US' #US CN JP KR
    # lang='en'
    # now = datetime.now().timestamp()*1000
    # minimize_stage_key=''
    # items={}
    # stages={}
    # formulas={}
    # item_exp={
        # '2001':200,
        # '2002':400,
        # '2003':1000,
        # '2004':2000,
    # }
    # stagecode_gold={
        # '1-1':660,
        # '2-7':1500,
        # '3-6':2040,
        # '4-1':2700,
        # '6-1':1216,
        # '7-3':1216,
        # 'R8-1':2700,
        # 'R8-4':1216,
        # '9-2':2700,
        # '9-3':1216,
        # '10-8':3480,
        # 'S2-2':1020,
        # 'S4-6':3480,
        # 'S5-2':2700,
        # 'S5-3':1216,
        # 'S5-5':1216,
        # 'S6-2':1216,
        # 'S6-4':2700,
        # 'S7-1':2700,
        # 'S7-2':1216,
        # 'CE-1':1700,
        # 'CE-2':2800,
        # 'CE-3':4100,
        # 'CE-4':5700,
        # 'CE-5':7500,
        # 'CE-6':10000,
    # }
    # except_itemType=['RECRUIT_TAG'] + ['TEMP','LGG_SHD','ACTIVITY_ITEM',]
    # except_stageId=['recruit',]
    # url_material = "https://raw.githubusercontent.com/Aceship/Arknight-Images/main/material/"
    # img_data={'30011': ('bg/item-1.png', '30.png'), '30012': ('bg/item-2.png', '24.png'), '30013': ('bg/item-3.png', '18.png'), '30014': ('bg/item-4.png', '12.png'), '30061': ('bg/item-1.png', '25.png'), '30062': ('bg/item-2.png', '19.png'), '30063': ('bg/item-3.png', '13.png'), '30064': ('bg/item-4.png', '7.png'), '30031': ('bg/item-1.png', '28.png'), '30032': ('bg/item-2.png', '22.png'), '30033': ('bg/item-3.png', '16.png'), '30034': ('bg/item-4.png', '10.png'), '30021': ('bg/item-1.png', '29.png'), '30022': ('bg/item-2.png', '23.png'), '30023': ('bg/item-3.png', '17.png'), '30024': ('bg/item-4.png', '11.png'), '30041': ('bg/item-1.png', '27.png'), '30042': ('bg/item-2.png', '21.png'), '30043': ('bg/item-3.png', '15.png'), '30044': ('bg/item-4.png', '9.png'), '30051': ('bg/item-1.png', '26.png'), '30052': ('bg/item-2.png', '20.png'), '30053': ('bg/item-3.png', '14.png'), '30054': ('bg/item-4.png', '8.png'), '30073': ('bg/item-3.png', '31.png'), '30074': ('bg/item-4.png', '6.png'), '30083': ('bg/item-3.png', '33.png'), '30084': ('bg/item-4.png', '5.png'), '30093': ('bg/item-3.png', '32.png'), '30094': ('bg/item-4.png', '4.png'), '30103': ('bg/item-3.png', '34.png'), '30104': ('bg/item-4.png', '3.png'), '31013': ('bg/item-3.png', '63.png'), '31014': ('bg/item-4.png', '64.png'), '31023': ('bg/item-3.png', '61.png'), '31024': ('bg/item-4.png', '62.png'), '30115': ('bg/item-5.png', '2.png'), '30125': ('bg/item-5.png', '1.png'), '30135': ('bg/item-5.png', '0.png'), '31033': ('bg/item-3.png', '67.png'), '31034': ('bg/item-4.png', '66.png')}

@shelve_cache('./tmp/farmcalc._get_json.cache')
def _get_json(key):
    penguin_api = 'https://penguin-stats.io/PenguinStats/api/v2/'
    url = penguin_api + key
    print(f'downloading {url}')
    response = requests.get(url)
    return response.json()

def get_json(key,update=False):
    if update:
        return _get_json(key,usecache=False)
    else:
        return _get_json(key)

def str_itemlist(itemlist):
    return ' + '.join([str(i) for i in itemlist if str(i)])

@dataclass
class Stage:
    name:str
    id:str
    zoneId:str
    code:str
    san:int
    minClearTime:int
    normal_drop:list #list of itemId
    outs:list #list of Item
    danger_level:float
    def __str__(self):
        return f'{self.name}|{self.danger_level}: {self.san}San = {str_itemlist(self.outs)}'
    def normaldrops(self):
        return [self.items[itemId] for itemId in self.normal_drop]

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

class FarmCalc():
    now = datetime.now().timestamp()*1000
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
    img_data={'30011': ('bg/item-1.png', '30.png'), '30012': ('bg/item-2.png', '24.png'), '30013': ('bg/item-3.png', '18.png'), '30014': ('bg/item-4.png', '12.png'), '30061': ('bg/item-1.png', '25.png'), '30062': ('bg/item-2.png', '19.png'), '30063': ('bg/item-3.png', '13.png'), '30064': ('bg/item-4.png', '7.png'), '30031': ('bg/item-1.png', '28.png'), '30032': ('bg/item-2.png', '22.png'), '30033': ('bg/item-3.png', '16.png'), '30034': ('bg/item-4.png', '10.png'), '30021': ('bg/item-1.png', '29.png'), '30022': ('bg/item-2.png', '23.png'), '30023': ('bg/item-3.png', '17.png'), '30024': ('bg/item-4.png', '11.png'), '30041': ('bg/item-1.png', '27.png'), '30042': ('bg/item-2.png', '21.png'), '30043': ('bg/item-3.png', '15.png'), '30044': ('bg/item-4.png', '9.png'), '30051': ('bg/item-1.png', '26.png'), '30052': ('bg/item-2.png', '20.png'), '30053': ('bg/item-3.png', '14.png'), '30054': ('bg/item-4.png', '8.png'), '30073': ('bg/item-3.png', '31.png'), '30074': ('bg/item-4.png', '6.png'), '30083': ('bg/item-3.png', '33.png'), '30084': ('bg/item-4.png', '5.png'), '30093': ('bg/item-3.png', '32.png'), '30094': ('bg/item-4.png', '4.png'), '30103': ('bg/item-3.png', '34.png'), '30104': ('bg/item-4.png', '3.png'), '31013': ('bg/item-3.png', '63.png'), '31014': ('bg/item-4.png', '64.png'), '31023': ('bg/item-3.png', '61.png'), '31024': ('bg/item-4.png', '62.png'), '30115': ('bg/item-5.png', '2.png'), '30125': ('bg/item-5.png', '1.png'), '30135': ('bg/item-5.png', '0.png'), '31033': ('bg/item-3.png', '67.png'), '31034': ('bg/item-4.png', '66.png')}

    def __init__(self,server='US',minimize_stage_key='',lang='en',update=False):
        self.server=server #US CN JP KR
        self.lang=lang #en ja ko zh
        self.items={}
        self.stages={}
        self.formulas={}
        print('FarmCalc.__init__',self.server,minimize_stage_key,self.lang)
        stages,items,stageitems,formulas = self.penguin_stats(update=update)
        self.prep_items(items)
        self.prep_stages(stages)
        self.prep_stages_stageitems(stageitems)
        self.prep_formulas(formulas)
        if minimize_stage_key: # san minClearTime
            result = self.best_stages(server=self.server,minimize_stage_key=minimize_stage_key)
            self.set_item_beststage(result)
            self.minimize_stage_key=minimize_stage_key
    def penguin_stats(self,update=False):
        def _penguin_stats(name,query,server=''):
            data=get_json(query,update)
            file=f'./tmp/{name}{server}.json'
            if (not os.path.isfile(file)) or update:
                save_json(file,data)
            return data
        stages = _penguin_stats('stages',f'stages?server={self.server}',self.server)
        items = _penguin_stats('items','items')
        stageitems = _penguin_stats('stageitems','result/matrix?show_closed_zone=false')
        stageitems_all = _penguin_stats('stageitems_all','result/matrix?show_closed_zone=true')
        formulas = _penguin_stats('formulas','formula')
        return stages,items,stageitems,formulas
    def prep_items(self,items):
        for item in items:
            if item.get('existence').get(self.server).get('exist')==True and (item.get('itemType') not in FarmCalc.except_itemType):
                itemId=item.get('itemId')
                obj=ItemType(
                    name=item.get('name_i18n').get(self.lang),
                    id=itemId,
                    rarity=item.get('rarity'),
                    itemType=item.get('itemType'),
                    groupID=item.get('groupID') or '',
                    img_data=[],
                    beststage=[],
                )
                if (img_data:=FarmCalc.img_data.get(obj.id)):
                    obj.img_data=img_data
                self.items[itemId]=obj

    def prep_stages(self,stages):
        stageinfos = anhrtags.GData.json_table('stage').get('stages',{})
        def dangerLevel(stageinfo):
            if (m:=re.match(r'Elite *(\d+) *Lv. *(\d+)',stageinfo.get('dangerLevel') or '')):
                return float(f'{m.group(1)}.{m.group(2)}')
            return 0
        for stage in stages:
            dropInfos=stage.get('dropInfos',{})
            if stage.get('existence').get(self.server).get('exist')==True:
                if (stageId:=stage.get('stageId')) not in FarmCalc.except_stageId:
                    normal_drop = [dropInfo.get('itemId') for dropInfo in dropInfos if dropInfo.get('dropType')=='NORMAL_DROP' and dropInfo.get('itemId')]
                    stageinfo=stageinfos.get(stageId,{})
                    obj=Stage(
                        name=f'stage:{stage.get('code_i18n').get(self.lang)}',
                        id=stageId,
                        zoneId=stage.get('zoneId'),
                        code=stage.get('code'),
                        san=stage.get('apCost'),
                        minClearTime=int(stage.get('minClearTime') or 999999999),
                        normal_drop=normal_drop,
                        outs=[],
                        danger_level=dangerLevel(stageinfo),
                    )
                    itemIds=set()
                    self.stages[stageId]=obj

    def prep_stages_stageitems(self,stageitems):
        for stageitem in stageitems.get('matrix',{}):
            stageId=stageitem.get('stageId')
            itemId=stageitem.get('itemId')
            times=stageitem.get('times')
            quantity=stageitem.get('quantity')
            start=stageitem.get('start')
            end=stageitem.get('end')
            n=quantity/times
            if FarmCalc.now>start and ((not end) or FarmCalc.now<end):
                if self.stages.get(stageId):
                    if self.items.get(itemId):
                        out = Item(
                            item=self.items[itemId],
                            n=n,
                        )
                        if out not in self.stages[stageId].outs:
                            self.stages[stageId].outs.append(out)

    def prep_formulas(self,formulas):
        for formula in formulas:
            itemId=formula.get('id')
            obj=Formula(
                name=f'formula:{self.items[itemId].name}',
                id=itemId,
                goldCost=formula.get('goldCost'),
                ins=[],
                out=[Item(
                                item=self.items[itemId],
                                n=1,
                            )],
                out_ex=[],
            )
            for cost in formula.get('costs'):
                itemId_cost=cost.get('id')
                obj.ins.append(Item(
                                item=self.items[itemId_cost],
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
                                    item=self.items[itemId_out],
                                    n=n,
                                ))
            self.formulas[itemId]=obj
            assert totalWeight==weight_all

    def print_lp(self,lp,args,req_,p=True):
        if not lp.success:
            if p: print(lp.message)
            return
        x=lp.x
        san = float(np.dot(args.get('c'),x))
        if p: print('print_lp:')
        if p: print(req_)
        if p: print(f'    {san=}')
        res_stage=[]
        res_formula=[]
        for idx,(n,obj) in enumerate(zip(list(x),list(self.stages.values())+list(self.formulas.values()))):
            if n>0:
                if isinstance(obj,Stage):
                    res_stage.append((obj,n))
                elif isinstance(obj,Formula):
                    res_formula.append((obj,n))
        res_stage=sorted(res_stage,key=lambda i:-i[1])
        res_formula=sorted(res_formula,key=lambda i:-i[1])
        for obj,n in res_stage:
            if p: print(f'    {obj.name}:{n:.1f}')
        for obj,n in res_formula:
            if p: print(f'    {obj.name}:{n:.1f}')
        return res_stage,res_formula,san

    def calc(self,req,test=False,minimize_stage_key='san'):
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
                    exp+=FarmCalc.item_exp.get(itemId,0)*n
                    d[itemId]=n
                return np.array([n if (n:=d.get(itemtype.id)) else 0 for itemtype in self.items.values()])
            if isinstance(obj,Stage):
                gold+=FarmCalc.stagecode_gold.get(obj.code,0)
                return np.append(item_array(obj.outs),[exp,gold])
            elif isinstance(obj,Formula):
                gold+=-obj.goldCost
                return np.append(item_array(obj.out)+item_array(obj.out_ex)*ex-item_array(obj.ins),[exp,gold])
            elif isinstance(obj,Req):
                return np.append(item_array(obj.reqs),[obj.exp,obj.gold])
        xkey0=list(self.stages.keys())
        xkey1=list(self.formulas.keys())
        xkey=xkey0+xkey1

        req_=Req(
            gold=req.get('gold',0),
            exp=req.get('exp',0),
            reqs=[Item(
                item=self.items[itemId],
                n=n,
            ) for itemId,n in req.items() if self.items.get(itemId)],
        )
        # integrality=[1]*len(xkey)
        # integrality=3
        integrality=None
        args={
            'c':np.array([getattr(stage,minimize_stage_key) for stage in self.stages.values()] + [0 for formula in self.formulas.values()]),
            'A_ub':-np.array(
                [to_array(stage) for stage in self.stages.values()] +
                [to_array(formula) for formula in self.formulas.values()]
            ).T,
            'b_ub':-to_array(req_),
            'integrality':integrality, #1,3: very slow
            'A_eq':None, 'b_eq':None, 'bounds':(0, None), 'method':'highs', 'callback':None, 'options':None, 'x0':None #default
        }
        lp=linprog(**args)
        return lp,args,req_

    def print_items(self):
        '''print req={}'''
        items=sorted(list(self.items.values()),key=lambda i:(i.itemType,i.groupID,i.rarity,i.name,i.id))
        print(*[f"""{' '*8}'{i.id}':100,{' '*(28-len(i.id))}#{i.name:<37}#{i.rarity} #{i.itemType}:{i.groupID}""" for i in items],sep='\n')

    @shelve_cache_clas('./tmp/farmcalc.calc_multi.cache')
    def calc_multi(self,key):
        server,minimize_stage_key,itemid = key.split()
        stages_all=[]
        min_san=None
        i=10
        while i>0:
            i-=1
            lp,args,req_=self.calc({itemid:1},test=True,minimize_stage_key=minimize_stage_key)
            if not lp.success:
                break
            res_stage,res_formula,san=self.print_lp(lp,args,req_,p=False)
            stages=[]
            if min_san==None:
                min_san=san
            if san >= min_san*2:
                break
            ce6=0
            for stage,count in res_stage:
                if stage.code!='CE-6':
                    stages.append(stage)
                    setattr(self.stages.get(stage.id),minimize_stage_key,getattr(self.stages.get(stage.id),minimize_stage_key)*1000)
                else:
                    ce6=1
            # if len(res_stage)>1+ce6:
                # i=0
            if stages:
                stages_all.append((stages,san))
        return stages_all

    @cache
    def best_stages(self,server,minimize_stage_key):
        d={}
        for stageId,stage in self.stages.items():
            d[stageId]=getattr(stage,minimize_stage_key)
        def restore():
            for stageId,stage in self.stages.items():
                setattr(stage,minimize_stage_key,d[stage.id])
        result={}
        count=1
        for itemid,v in self.items.items():
            if v.itemType in ['CHIP','CARD_EXP','FURN','CHIP',] or itemid in ['3003',]:
                continue
            restore()
            stages_all=self.calc_multi(' '.join((server,minimize_stage_key,itemid)))
            if stages_all:
                result[itemid]=stages_all
        return result

    # @cache
    # def best_stages(server=self.server,minimize_stage_key='san'):
        # result={}
        # s4=[]
        # s5=[]
        # count=1
        # for itemid,v in self.items.items():
            # lp,args,req_=calc({itemid:count},test=True,minimize_stage_key=minimize_stage_key)
            # if lp.success:
                # res_stage,res_formula,san=print_lp(lp,args,req_,p=False)
                # beststage=[]
                # for stage,n in res_stage:
                    # if stage.id not in s4:
                        # s4.append(stage.id)
                        # s5.append(stage.id.replace('_perm',''))
                    # if stage.code!='CE-6':
                        # beststage.append(stage)
                # if (item:=self.items.get(itemid)):
                    # item.beststage=beststage
                # result[itemid]=beststage
            # else:
                # print(itemid,lp)
        # return s4,s5,minimize_stage_key,result

    def set_item_beststage(self,result):
        for itemid,beststage in result.items():
            if (item:=self.items.get(itemid)):
                item.beststage=beststage

if __name__ == '__main__':
    data=FarmCalc(server='US',minimize_stage_key='san',lang='en',update=False)

    # print(*[str(i) for i in self.items.values()],sep='\n')
    # print(*[str(i) for i in self.stages.values()],sep='\n')
    # print(*[str(i) for i in self.formulas.values()],sep='\n')
    # print_items()

    stages_all=[]
    min_san=None
    i=1
    while i:
        lp,args,req_=data.calc(req,minimize_stage_key='san')
        if not lp.success:
            break
        res_stage,res_formula,san = data.print_lp(lp,args,req_,p=False)
        stages=[]
        if min_san==None:
            min_san=san
        if san >= min_san*2:
            break
        if res_stage:
            for stage,n in res_stage:
                if stage.code!='CE-6':
                    if stage in stages:
                        i=0
                        break
                    else:
                        stages.append(stage)
                    data.stages.get(stage.id).san*=1000
            stages.append(san)
            stages_all.append(stages)
    print(req_)
    for stages in stages_all:
        print([getattr(stage,'name',stage) for stage in stages])

    print()
    lp,args,req_=data.calc(req,minimize_stage_key='san')
    res_stage,res_formula,san = data.print_lp(lp,args,req_)

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

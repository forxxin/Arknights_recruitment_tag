from dataclasses import dataclass
from functools import cache
import re
import os

try:
    import pandas as pd 
except Exception as e:
    print('import',type(e),e)

import resource
import farmcalc

app_path = os.path.dirname(__file__)
os.chdir(app_path)

class Data:
    data={}
    stages={}

@dataclass
class Stage:
    id:str
    code:str
    stageType:str
    levelId:str
    zoneId:str
    activity_name:str
    san:int
    danger_level:float
    normaldrops:list
    bestdrop:str
    def __str__(self):
        return f'{self.code}|{self.id}|{self.danger_level}|{self.levelId}: {self.san}San'

def prep_stages():
    def danger_level(dangerLevel):
        if (m:=re.match(r'Elite *(\d+) *Lv. *(\d+)',dangerLevel or '')):
            return float(f'{m.group(1)}.{m.group(2).zfill(2)}')
        if (m:=re.match(r'LV. *(\d+)',dangerLevel or '')):
            return float(f'0.{m.group(1).zfill(2)}')
        if dangerLevel=='-' or dangerLevel==None:
            return 3
        return 0
    res = {stageId:Stage(
            id=d.get('stageId'),
            code=d.get('code'),
            stageType=d.get('stageType'),
            levelId=d.get('levelId'),
            activity_name='',
            zoneId=d.get('zoneId'),
            san=d.get('apCost'),
            danger_level=danger_level(d.get('dangerLevel')),
            normaldrops=[],
            bestdrop='',
        ) for stageId,d in resource.GameData.json_table('stage').get('stages',{}).items()}
    stageid_tran={}
    bestdrop={}
    for itemid,stages_all in Data.data.result.items():
        for beststages,san in stages_all:
            for stage in beststages:
                stageid_tran[stage.id.replace('_perm','')] = stage.id
                bestdrop[stage.id.replace('_perm','')]=Data.data.items.get(itemid)
            break
    for stageId,stage in res.items():
        activityId = zoneId2activityId().get(stage.zoneId)
        if activityId:
            activity = activitys().get(activityId)
            stage.activity_name=activity.name.replace(' - Rerun','')
        best_stages = [d for s,d in res.items() if d.id in stageid_tran]
        for stage in best_stages:
            stage_id = stageid_tran.get(stage.id)
            stage.normaldrops = [Data.data.items[itemid].name for itemid in Data.data.stages[stage_id].normaldrops()]
            stage.bestdrop = bestdrop[stage.id]
    return res

@cache
def zoneId2activityId():
    return {stageId:activityId for stageId,activityId in resource.GameData.json_table('activity').get('zoneToActivity',{}).items()}

@dataclass
class Activity:
    id:str
    name:str
    displayType:str
    def __str__(self):
        return f'{self.name}'

@cache
def activitys():
    return {activityId:Activity(
        id = d.get('id'),
        name = d.get('name'),
        displayType = d.get('displayType'),
    ) for activityId,d in resource.GameData.json_table('activity').get('basicInfo',{}).items()}

def print_best(minimize_stage_key='san'):
    stageid_tran={}
    for itemid,stages_all in Data.data.result.items():
        for beststages,san in stages_all:
            for stage in beststages:
                stageid_tran[stage.id.replace('_perm','')] = stage.id
            break
    print(f'minimize_stage_key: {minimize_stage_key}')
    def stage_str(stage):
        stage_id = stageid_tran.get(stage.id)
        normaldrops = [Data.data.items[itemid] for itemid in Data.data.stages[stage_id].normaldrops()]
        bestdrop = stage.bestdrop
        if bestdrop in normaldrops:
            return stage.code+f'[{bestdrop.name}]{bestdrop.rarity}'
        elif len(normaldrops)==1:
            return stage.code+f"""[{normaldrops[0].name}->{bestdrop.name}]{bestdrop.rarity}"""
        else:
            names=[f'{item.name}' for item in normaldrops] 
            return stage.code+f"""[{' '.join(names)}->{bestdrop.name}]{bestdrop.rarity}"""
    best_stages = [d for s,d in Data.stages.items() if d.id in stageid_tran]
    activity_stages={activity.get('name'):[] for activityId, activity in resource.GameData.json_table('story_review').items()}
    stageType_stages={}
    for stage in best_stages:
        activityId = zoneId2activityId().get(stage.zoneId)
        if activityId:
            activity = activitys().get(activityId)
            activity_name = activity.name.replace(' - Rerun','')
            activity_stages.get(activity_name).append(stage)
        else:
            stageType_stages.setdefault(stage.stageType,[]).append(stage)
    for activity_name,stages_ in activity_stages.items():
        if stages_:
            print(f'"{activity_name}"{' '*(36-len(activity_name))}# {' '.join([stage_str(stage) for stage in stages_])}')
    for stageType,stages_ in stageType_stages.items():
        print(f'"{stageType}"{' '*(36-len(stageType))}# {' '.join([stage_str(stage) for stage in stages_])}')
    return {activity_name:stages_ for activity_name,stages_ in activity_stages.items() if stages_}, stageType_stages

if __name__ == '__main__':
    Data.data=farmcalc.FarmCalc(server='US',minimize_stage_key='san',lang='en',update=False)
    # farmcalc.init(server='US',minimize_stage_key='san',lang='en',update=False)
    Data.stages=prep_stages()
    print_best()

    df = pd.DataFrame(Data.stages.values())
    df.to_excel('stages.xlsx')
    # print(df)

# minimize_stage_key: san
"Grani and the Knights' Treasure"     # GT-4[Sugar Substitute]0 GT-5[Loxic Kohl->D32 Steel]4
"Heart of Surging Flame"              # OF-F3[Sugar Pack->Bipolar Nanoflake]4
"Twilight of Wolumonde"               # TW-5[Device]1 TW-6[Incandescent Alloy->Crystalline Circuit]3
"Mansfield Break"                     # MB-6[Sugar Pack->Transmuted Salt Agglomerate]3
"A Walk in the Dust"                  # WD-6[Polyester Pack->D32 Steel]4 WD-8[RMA70-12->D32 Steel]4
"Dossoles Holiday"                    # DH-4[Ester]0
"Break the Ice"                       # BI-5[Diketon]0
"Stultifera Navis"                    # SN-5[Oriron Shard]0
"MAIN"                                # 1-7[Orirock Cube->D32 Steel]4 2-3[Damaged Device]0 S2-5[Orirock]0 2-10[RMA70-12->White Horse Kohl]3 3-1[Aketon->RMA70-24]3 3-3[Grindstone->Bipolar Nanoflake]4 3-4[Integrated Device->Polymerization Preparation]4 3-7[Polyketon]1 4-2[Sugar Pack->Sugar Lump]3 4-8[Grindstone->D32 Steel]4 4-9[RMA70-12->RMA70-24]3 5-7[Grindstone Oriron->Crystalline Electronic Unit]4 5-10[Integrated Device Orirock Cube->Optimized Device]3 7-12[Sugar Pack Polyketon->Keton Colloid]3 7-15[Integrated Device->Crystalline Electronic Unit]4 7-18[Oriron Cluster Polyketon->D32 Steel]4 R8-11[Crystalline Component->Nucleic Crystal Sinter]4 9-3[Device]1 9-16[Grindstone]2 9-19[RMA70-12->Nucleic Crystal Sinter]4 10-3[Coagulating Gel->Nucleic Crystal Sinter]4 10-3[Coagulating Gel->Crystalline Electronic Unit]4 10-4[Device Aketon->D32 Steel]4 10-6[Orirock Cluster->Bipolar Nanoflake]4 10-7[Manganese Ore->D32 Steel]4 10-11[Oriron Cluster->Crystalline Electronic Unit]4 10-16[Polyester Manganese Ore->Polymerization Preparation]4 10-17[Compound Cutting Fluid]2 11-3[Transmuted Salt->Transmuted Salt Agglomerate]3 11-3[Transmuted Salt->Nucleic Crystal Sinter]4 11-6[Sugar Pack Oriron->Sugar Lump]3 11-7[Integrated Device->Incandescent Alloy Block]3 11-7[Integrated Device->D32 Steel]4 11-13[Loxic Kohl->Bipolar Nanoflake]4 11-14[Incandescent Alloy->Crystalline Electronic Unit]4 12-5[Coagulating Gel->Refined Solvent]3 12-10[Semi-Synthetic Solvent->Nucleic Crystal Sinter]4 12-12[Incandescent Alloy->Incandescent Alloy Block]3 12-17[Compound Cutting Fluid->Nucleic Crystal Sinter]4 13-5[Fuscous Fiber]2 13-5[Fuscous Fiber->Solidified Fiber Board]3 13-12[Polyester Pack->Polyester Lump]3 13-14[Semi-Synthetic Solvent->Nucleic Crystal Sinter]4 13-14[Semi-Synthetic Solvent->Transmuted Salt Agglomerate]3 13-15[Aggregate Cyclicene]2 13-15[Aggregate Cyclicene->Cyclicene Prefab]3 13-19[Loxic Kohl->White Horse Kohl]3
"SUB"                                 # S3-1[Sugar]1 S3-2[Polyester]1 S3-3[Oriron]1
"DAILY"                               # SK-2[Carbon Stick]1 SK-3[Carbon Brick]2 SK-5[Carbon Brick]3 CA-2[Skill Summary - 1]1 CA-3[Skill Summary - 2]2 CA-5[Skill Summary - 3]3

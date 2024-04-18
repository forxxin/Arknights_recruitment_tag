from dataclasses import dataclass
from functools import cache
import re

try:
    import matplotlib.pyplot as plt
    import matplotlib
    import pandas as pd 
except Exception as e:
    print(e)

import anhrtags
import farmcalc

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
    def __str__(self):
        return f'{self.code}|{self.id}|{self.danger_level}|{self.levelId}: {self.san}San'

@cache
def stages():
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
        ) for stageId,d in anhrtags.GData.json_table('stage').get('stages',{}).items()}
    for stageId,stage in res.items():
        activityId = zoneId2activityId().get(stage.zoneId)
        if activityId:
            activity = activitys().get(activityId)
            stage.activity_name=activity.name.replace(' - Rerun','')
        liststageIds_,liststageIds = farmcalc.best_stages()
        stageid_tran={b:a for a,b in zip(liststageIds_,liststageIds)}
        best_stages = [d for s,d in res.items() if d.id in liststageIds]
        for stage in best_stages:
            stage_id = stageid_tran.get(stage.id)
            stage.normaldrops = [item.name for item in farmcalc.Data.stages[stage_id].normaldrops()]
    return res

@cache
def zoneId2activityId():
    return {stageId:activityId for stageId,activityId in anhrtags.GData.json_table('activity').get('zoneToActivity',{}).items()}

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
    ) for activityId,d in anhrtags.GData.json_table('activity').get('basicInfo',{}).items()}

def print_best():
    liststageIds_,liststageIds = farmcalc.best_stages()
    stageid_tran={b:a for a,b in zip(liststageIds_,liststageIds)}
    def stage_str(stage):
        stage_id = stageid_tran.get(stage.id)
        return stage.code+str([item.name for item in farmcalc.Data.stages[stage_id].normaldrops()])
    best_stages = [d for s,d in stages().items() if d.id in liststageIds]
    activity_stages={}
    stageType_stages={}
    for stage in best_stages:
        activityId = zoneId2activityId().get(stage.zoneId)
        if activityId:
            activity = activitys().get(activityId)
            activity_name = activity.name.replace(' - Rerun','')
            activity_stages.setdefault(activity_name,[]).append(stage)
        else:
            stageType_stages.setdefault(stage.stageType,[]).append(stage)
    for activity_name,stages_ in activity_stages.items():
        print(f'"{activity_name}"{' '*(36-len(activity_name))}# {' '.join([stage_str(stage) for stage in stages_])}')
    for stageType,stages_ in stageType_stages.items():
        print(f'"{stageType}"{' '*(36-len(stageType))}# {' '.join([stage_str(stage) for stage in stages_])}')

if __name__ == '__main__':
    # print_best()
    df = pd.DataFrame(stages().values())
    df.to_excel('stages.xlsx')
    print(df)
    
"Stultifera Navis"                    # SN-5
"Break the Ice"                       # BI-5
"Dossoles Holiday"                    # DH-4
"A Walk in the Dust"                  # WD-1 WD-5 WD-6 WD-8
"Who Is Real"                         # WR-3
"Mansfield Break"                     # MB-6
"Twilight of Wolumonde"               # TW-5 TW-6
"Heart of Surging Flame"              # OF-F3
"Grani and the Knights' Treasure"     # GT-4 GT-5
"MAIN"                                # 0-2 1-7 2-3 S2-5 2-10 3-1 3-3 3-4 3-7 3-8 4-2 4-8 4-9 5-7 5-10 7-12 7-15 7-18 R8-2 R8-11 9-14 9-16 9-18 9-19 10-3 10-3 10-4 10-6 10-7 10-11 10-16 10-17 11-3 11-3 11-6 11-7 11-8 11-13 11-14 12-5 12-9 12-10 12-12 12-17
"SUB"                                 # S3-1 S3-2 S3-3
"DAILY"                               # SK-2 SK-3 SK-5 LS-6 CA-2 CA-3 CA-5 PR-A-1 PR-A-2 PR-B-1 PR-B-2 PR-C-1 PR-C-2 PR-D-1 PR-D-2

"Stultifera Navis"                    # SN-5['Oriron Shard']
"Break the Ice"                       # BI-5['Diketon']
"Dossoles Holiday"                    # DH-4['Ester']
"A Walk in the Dust"                  # WD-1['Oriron Shard'] WD-5[] WD-6['Polyester Pack'] WD-8['RMA70-12']
"Who Is Real"                         # WR-3['Frontline Battle Record']
"Mansfield Break"                     # MB-6['Sugar Pack']
"Twilight of Wolumonde"               # TW-5['Device'] TW-6['Incandescent Alloy']
"Heart of Surging Flame"              # OF-F3['Sugar Pack']
"Grani and the Knights' Treasure"     # GT-4['Sugar Substitute'] GT-5['Loxic Kohl']
"MAIN"                                # 0-2['Drill Battle Record'] 1-7['Orirock Cube'] 2-3['Damaged Device'] S2-5['Orirock'] 2-10['RMA70-12'] 3-1['Aketon'] 3-3['Grindstone'] 3-4['Integrated Device'] 3-7['Polyketon'] 3-8['Polyester Pack'] 4-2['Sugar Pack'] 4-8['Grindstone'] 4-9['RMA70-12'] 5-7['Grindstone', 'Oriron'] 5-10['Integrated Device', 'Orirock Cube'] 7-12['Sugar Pack', 'Polyketon'] 7-15['Integrated Device'] 7-18['Oriron Cluster', 'Polyketon'] R8-2['Loxic Kohl'] R8-11['Crystalline Component'] 9-14['Crystalline Component'] 9-16['Grindstone', 'Oriron'] 9-18['Semi-Synthetic Solvent'] 9-19['RMA70-12'] 10-3['Coagulating Gel'] 10-3['Coagulating Gel'] 10-4['Device', 'Aketon'] 10-6['Orirock Cluster'] 10-7['Manganese Ore'] 10-11['Oriron Cluster'] 10-16['Polyester', 'Manganese Ore'] 10-17['Compound Cutting Fluid'] 11-3['Transmuted Salt'] 11-3['Transmuted Salt'] 11-6['Sugar Pack', 'Oriron'] 11-7['Integrated Device'] 11-8['Semi-Synthetic Solvent'] 11-13['Loxic Kohl'] 11-14['Incandescent Alloy'] 12-5['Coagulating Gel'] 12-9['Tactical Battle Record'] 12-10['Semi-Synthetic Solvent'] 12-12['Incandescent Alloy'] 12-17['Compound Cutting Fluid']
"SUB"                                 # S3-1['Sugar'] S3-2['Polyester'] S3-3['Oriron']
"DAILY"                               # SK-2['Carbon Stick'] SK-3['Carbon Stick', 'Carbon Brick'] SK-5['Carbon Brick', 'Carbon Brick'] LS-6['Tactical Battle Record', 'Strategic Battle Record'] CA-2['Skill Summary - 1'] CA-3['Skill Summary - 2', 'Skill Summary - 1'] CA-5['Skill Summary - 3', 'Skill Summary - 1', 'Skill Summary - 2'] PR-A-1['Defender Chip', 'Medic Chip'] PR-A-2['Defender Chip Pack', 'Medic Chip Pack'] PR-B-1['Sniper Chip', 'Caster Chip'] PR-B-2['Sniper Chip Pack', 'Caster Chip Pack'] PR-C-1['Vanguard Chip', 'Supporter Chip'] PR-C-2['Vanguard Chip Pack', 'Supporter Chip Pack'] PR-D-1['Guard Chip', 'Specialist Chip'] PR-D-2['Guard Chip Pack', 'Specialist Chip Pack']

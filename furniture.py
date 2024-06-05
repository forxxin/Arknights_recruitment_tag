import re
import pprint
from dataclasses import dataclass

import pandas as pd

import resource
from char import Chars

# item_table = resource.GameData.json_table('item', lang='en_US')
retro_table = resource.GameData.json_table('retro', lang='en_US')
building_data = resource.GameData.json_data('building', lang='en_US')
activity_table = resource.GameData.json_table('activity', lang='en_US')
chardata=Chars(server='US',lang='en')


@dataclass
class Retro:
    id:str
    name:str

class Data:
    def __init__(self):
        self.retro_table = resource.GameData.json_table('retro', lang='en_US')
        self.building_data = resource.GameData.json_data('building', lang='en_US')
        self.activity_table = resource.GameData.json_table('activity', lang='en_US')
        self.chardata=Chars(server='US',lang='en')
        self.prep_retros()
    def prep_rewards(self):
        self.retros={}
        rewards_char=[]
        rewards_funi=[]
        def gen_(retro_id):
            retro=retro_table.get('retroTrailList').get(retro_id)
            for trailReward in retro.get('trailRewardList'):
                rewardItem=trailReward.get('rewardItem',{})
                if rewardItem.get('type')=='CHAR':
                    charid = rewardItem.get('id')
                    char=chardata.chars.get(charid)
                    rewards_char.append(char)
                if rewardItem.get('type')=='UNI_COLLECTION':
                    unisetid = rewardItem.get('id')
                    starCount=trailReward.get('starCount')
                    unisetid_starCount[unisetid]=starCount
                    unisetid_retroId[unisetid]=retroId
        for retro_id,retro in self.retro_table.get('retroActList').items():
            self.retros[retro_id]=Retro(
                id=retro_id,
                name=retro.get('name'),
            )

retroId_retroname={}
for retroId,retro in retro_table.get('retroActList').items():
    retroname = retro.get('name')
    retroId_retroname[retroId]=retroname
retroname_char={}
unisetid_retroId={}
unisetid_starCount={}
for retroId,retro in retro_table.get('retroTrailList').items():
    retroname=retroId_retroname[retroId]
    for trailReward in retro.get('trailRewardList'):
        rewardItem=trailReward.get('rewardItem',{})
        if rewardItem.get('type')=='CHAR':
            charid = rewardItem.get('id')
            char=chardata.chars.get(charid)
            retroname_char[retroname]=char
        if rewardItem.get('type')=='UNI_COLLECTION':
            unisetid = rewardItem.get('id')
            starCount=trailReward.get('starCount')
            unisetid_starCount[unisetid]=starCount
            unisetid_retroId[unisetid]=retroId
unisetid_retroname={}
for unisetid,retroId in unisetid_retroId.items():
    retroname=retroId_retroname[retroId]
    unisetid_retroname[unisetid]=retroname
furnisetname_retroname={}
furnisetname_retroId={}
furnisetid_furni={}
furni_furnisetid={}
furni_furnisetname={}
furnisetnames=[]
retroname_starCount={}
for furnisetid,furniset in building_data.get('customData',{}).get('themes').items():
    furnisetname=furniset.get('name')
    furnisetnames.append(furnisetname)
    unisetid=furnisetid.replace('furni_set_','uni_set_')
    m=re.match(r'furni_set_(?P<furni>[^_]+)(_[^_]+)?',furnisetid)
    if m:
        furni=m.group('furni')
        furnisetid_furni[furnisetid]=furni
        furni_furnisetname[furni]=furnisetname
        furni_furnisetid[furni]=furnisetid
    else:
        raise Exception(furnisetid)
    # print((furnisetid,furnisetname,))
    if unisetid in unisetid_retroId:
        retroname=unisetid_retroname[unisetid]
        retroId=unisetid_retroId[unisetid]
        starCount=unisetid_starCount[unisetid]
        furnisetname_retroname[furnisetname]=retroname
        retroname_starCount[retroname]=starCount
        furnisetname_retroId[furnisetname]=retroId
    else:
        retroname=''
# pprint.pprint(furnisetid_furni)
missionid_furni={}
for missionData in activity_table.get('missionData'):
    missionid = missionData.get('id') #14sreActivity_12
    furnis=set()
    for reward in missionData.get('rewards') or []:
        if reward.get('type')=='FURN':
            rewardid=reward.get('id') #furni_stage_floor_01
            m=re.match(r'furni_(?P<furni>[^_]+)_.*',rewardid)
            if m:
                furni=m.group('furni')
                if furni in furni_furnisetid:
                    furnis.add(furni)
                # else:
                    # not theme
                    # raise Exception((furni,'not in furni_furnisetid',rewardid))
            else:
                raise Exception(('not match',rewardid))
    if len(furnis)>1:
        raise Exception(('len(furnis)>1',furnis,missionid))
    if len(furnis)==1:
        furni=list(furnis)[0]
        missionid_furni[missionid]=furni
# pprint.pprint(missionid_furni)
activityid_activityname={}
for activityid,activity in activity_table.get('basicInfo').items():
    activityid_activityname[activityid]=activity.get('name')
# pprint.pprint(activityid_activityname)
activityname_furnisetname={}
furnisetname_activityname={}
for missionGroup in activity_table.get('missionGroup'):
    activityid = missionGroup.get('id') #act14sre
    furnis=set()
    for missionid in missionGroup.get('missionIds'):
        # if missionid in missionid_furni:
        if (furni:=missionid_furni.get(missionid)):
            furnis.add(furni)
    if len(furnis)>1:
        raise Exception(('len(furnis)>1',furnis,activityid))
    if len(furnis)==1:
        furni=list(furnis)[0]
        furnisetname=furni_furnisetname[furni]
        activityname=activityid_activityname[activityid]
        activityname_furnisetname[activityname]=furnisetname
        furnisetname_activityname[furnisetname]=activityname
for activityname,furnisetname in list(activityname_furnisetname.items()):
    if activityname.endswith(' - Rerun'):
        activityname_ = activityname.replace(' - Rerun','')
        furnisetname_ = activityname_furnisetname.get(activityname_)
        if furnisetname_==furnisetname:
            pass
        else:
            raise Exception((activityname_,furnisetname_,activityname,furnisetname,))
# pprint.pprint(activityname_furnisetname)


table='''
| side story                                    | furniture store                             | in store   | full   | amb   | cost   | amb/cost   |
|-----------------------------------------------|---------------------------------------------|------------|--------|-------|--------|------------|
| Mansfield Break[Robin.T6][36]                 | Mansfield Prison Cell                       | 1          | 0      | 5000  | 1225   | 4.082      |
| # Break the Ice                               | Kjerag-Style Inn                            |            |        | 5000  | 1380   | 3.623      |
| # Lingering Echoes                            | Afterglow-Styled Music Room                 |            |        | 5000  | 1515   | 3.3        |
|                                               | Stultifera Navis Reception Room             |            |        | 5000  | 1520   | 3.289      |
| # Invitation to Wine                          | Shan-Ch'eng Teahouse                        |            |        | 5000  | 1620   | 3.086      |
| # Dorothy's Vision                            | Rhine Experimental Culture Pod              |            |        | 5000  | 1650   | 3.03       |
| Near Light[Wild Mane.T7][46]                  | Kazimierz Broadcast Center                  | 1          | 0      | 5000  | 1700   | 2.941      |
| Who is Real[Lava the Purgatory.T9][36]        | Tan-Ch'ing Court                            | 1          | 0      | 5000  | 1795   | 2.786      |
| Under Tides[Gladiia.T3][35]                   | Iberian Resort Town                         | 1          | 0      | 5000  | 1810   | 2.762      |
| Darknights Memoir[Sideroca.T9][31]            | Seven Cities-style Restaurant               | 1          | 0      | 5000  | 1875   | 2.667      |
| Maria Nearl[Whislash.T10][40]                 | Nearls' Living Room Replica                 | 1          | 0      | 5000  | 1885   | 2.653      |
| A Walk in the Dust[Heavyrain.T7][32]          | Critical Response Team Office               | 1          | 0      | 5000  | 2015   | 2.481      |
| # Guide Ahead                                 | Laterano Notarial Hall Lounge               |            |        | 5000  | 2045   | 2.445      |
| # Operation Originium Dust                    | Special Equipment Exhibition Room           |            |        | 5000  | 2045   | 2.445      |
| Grani and the Knights' Treasure[Grani.T9][24] | Express Chain Pizzeria                      |            |        | 5000  | 2120   | 2.358      |
| Twilight of Wolumonde[Folinic.T8][40]         | Leithanian Nights                           | 1          | 0      | 5000  | 2190   | 2.283      |
| Dossoles Holiday[Tequila.T5][39]              | Dossoles Private Spa                        | 1          | 0      | 5000  | 2240   | 2.232      |
| # Ideal City: Endless Carnival                | Great Aquapit Funtastic Experientorium      |            |        | 5000  | 2250   | 2.222      |
| Heart of Surging Flame[Ceylon.T11][40]        | Modern Music Rehearsal Room                 | 1          | 0      | 5300  | 2520   | 2.103      |
| The Great Chief Returns[Tomimi.T11][36]       | Tribal-Style Inn                            | 1          | 0      | 5000  | 2415   | 2.07       |
| Code of Brawl[Bison.T8][45]                   | Penguin Logistics Safehouse                 | 1          | 0      | 5000  | 3500   | 1.429      |
|                                               | No.12 Life Cycle Cabin                      |            |        | 3045  | 2825   | 1.078      |
|                                               | Side Line/ Simple Orange Furniture          |            |        | 2035  | 1945   | 1.046      |
|                                               | Side Line/ Simple Black-and-white Furniture |            |        | 2035  | 1945   | 1.046      |
|                                               | Ch'en's Office                              |            |        | 4915  | 5095   | 0.965      |
|                                               | Fantastic Bio-documentary                   |            |        | 3195  | 3320   | 0.962      |
|                                               | Columbian Café                              | 1          | 1      | 4420  | 4775   | 0.926      |
|                                               | Secret Occult Society                       |            |        | 4800  | 5380   | 0.892      |
|                                               | Caladon Light Store                         | 1          | 1      | 5000  | 5700   | 0.877      |
|                                               | Victorian Royal Guard Academy Dormitory     |            |        | 5000  | 5705   | 0.876      |
|                                               | Instrument Repair Workshop                  | 1          | 1      | 5000  | 5730   | 0.873      |
|                                               | The Photography Hobbyist's Studio           | 1          | 1      | 5000  | 5735   | 0.872      |
|                                               | The Zen Garden                              |            |        | 4800  | 5605   | 0.856      |
|                                               | Modern Columbian Hotel                      | 1          | 1      | 4555  | 5330   | 0.855      |
|                                               | Siesta Beach Hut                            | 1          | 1      | 4800  | 5650   | 0.85       |
|                                               | Walter Interior Sensations                  | 1          | 1      | 4500  | 5300   | 0.849      |
| # Come Catastrophes or Wakes of Vultures      | BSW Safehouse                               |            |        |       |        |            |
| # IL Siracusano                               | Siracusan Court of Justice                  |            |        |       |        |            |
| # What the Firelight Casts                    | Reed's Cabin                                |            |        |       |        |            |
| # Where Vernal Winds Will Never Blow          | Yumen Clinic                                |            |        |       |        |            |
| # Lone Trail                                  | Rhine Tech Eco-Garden                       |            |        |       |        |            |
| # Hortus de Escapismo                         | Ambulacrum Ambrosii                         |            |        |       |        |            |
| # So Long, Adele: Home Away From Home         | Trip to the 'White Volcano'                 |            |        |       |        |            |
| # Zwillingstürme im Herbst                    | Ludwigs-Universität Lecture Hall            |            |        | 5000  |        |            |
'''
def load_table():
    pattern = r'''\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|\s*([^\|]+?)\s*\|'''
    matches = re.findall(pattern, table)
    header = matches[0]
    data = matches[2:]
    # print(header) #('side story', 'furniture store', 'in store', 'full', 'amb', 'cost', 'amb/cost')
    df = pd.DataFrame(data, columns=header)
    # for key in ('in store', 'full', 'amb', 'cost'):
        # df[key] = df[key].astype(int)
    # for key in ('amb/cost'):
        # df[key] = df[key].astype(float)

    return df
def save_table(df):
    def formula(x, y):
        try:
            return round(int(x)/int(y),3)
        except:
            return ''
    df['amb/cost'] = df.apply(lambda row: formula(row['amb'], row['cost']), axis='columns')
    def particular_sort(series):
        def index(x):
            try:
                return -float(x)
            except:
                return 0
        return series.apply(index)
    df = df.sort_values(by=["amb/cost"], key=particular_sort)
    return df.to_markdown(tablefmt="github", index=False)
# pprint.pprint(furnisetname_activityname) # # furniture part
# print()
# pprint.pprint(furnisetname_retroname) # furniture set

df=load_table()

furnisetname_sidestory={}
retronames_=[]
for furnisetname in furnisetnames:
    activityname=furnisetname_activityname.get(furnisetname)
    retroname=furnisetname_retroname.get(furnisetname)
    retroId=furnisetname_retroId.get(furnisetname)
    if retroname:
        sidestory=retroname
        starCount=retroname_starCount[retroname]
        if retroname in retroname_char:
            retronames_.append(retroname)
            char=retroname_char[retroname]
            char_s=f'{char.name}.R{char.rarity}.T{char.tier}'
            sidestory=f'{sidestory}[{char_s}][{starCount}]'
        else:
            sidestory=f'{sidestory}[{starCount}]'
    elif activityname:
        sidestory=f'# {activityname}'
    else:
        sidestory=''
    if sidestory:
        furnisetname_sidestory[furnisetname]=sidestory
        if furnisetname in df['furniture store'].values:
            df.loc[df['furniture store']==furnisetname, 'side story'] = sidestory
        else:
            data=[sidestory,furnisetname]+['']*5
            df.loc[df.index.max() + 1] = data
for retroname,char in retroname_char.items():
    if retroname not in retronames_:
        char=retroname_char[retroname]
        char_s=f'{char.name}.R{char.rarity}.T{char.tier}'
        sidestory=f'{sidestory}[{char_s}][{starCount}]'
        print(sidestory)
s=save_table(df)
print(s)

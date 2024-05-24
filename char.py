from dataclasses import dataclass
from itertools import combinations
import pprint
import os
import threading
import re

import pandas as pd

import resource
from tier import char_tier
# from levelplot import (
    # max_level,
    # max_e,
    # max_elevel,
    # cost2,
# )



app_path = os.path.dirname(__file__)
os.chdir(app_path)

try:
    from test import dump
except:
    def dump(**a):
        pass

@dataclass
class Character:
    characterId:str
    name:str
    profession:str
    subProfessionId:str
    position:str
    tags:frozenset
    rarity:int
    avatar:str
    # avatar2:str
    # portrait:str
    # portrait2:str
    itemObtainApproach:str
    recruitable:bool
    # description:str
    # potentialItemId:str
    # nationId:str
    # displayNumber:str
    # appellation:str
    # itemUsage:str
    # itemDesc:str
    # groupId:str
    # teamId:str
    # classicPotentialItemId:str
    # activityPotentialItemId:str
    # canUseGeneralPotentialItem:bool
    # canUseActivityPotentialItem:bool
    # isNotObtainable:bool
    # isSpChar:bool
    # canUseGeneralPotentialItem:int
    # canUseActivityPotentialItem:int
    # isNotObtainable:int
    # isSpChar:int
    # maxPotentialLevel:int
    # phases:list
    # skills:list
    # talents:list
    # potentialRanks:list
    # favorKeyFrames:list
    # allSkillLvlup:list
    # trait:dict
    # displayTokenDict:dict
    evolveCost:list
    tier:int
    def __repr__(self):
        s=f'Character({self.name})'
        return s
    def __str__(self):
        s=f'{self.name}'
        return s

@dataclass
class CharacterExcel:
    characterId:str
    profession:str
    subProfessionId:str
    position:str
    name:str
    tier:int
    rarity:int
    evolveCost:str
    tags:str
    recruitable:int
    @classmethod
    def from_character(cls, char):
        return cls(
            characterId=char.characterId,
            name=char.name,
            profession=char.profession.title(),
            subProfessionId=char.subProfessionId.title(),
            position=char.position.title(),
            rarity=char.rarity,
            tags=str(sorted(list(char.tags))),
            evolveCost=str(char.evolveCost),
            tier=char.tier,
            recruitable=1 if char.recruitable else '',
        )

def subset(items,maxtag=5,self=0):
    for i in range(1,min(maxtag+1,len(items)+self)):
        for s in combinations(items, i):
            yield frozenset(s)

class CacheInstType(type):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.instances={}
        self.locks={}
    # def __call__(self,server='US',lang='en'):
        # key=(server,lang)
        # with self.lock:
            # if key in self.instances:
                # return self.instances[key]
            # else:
                # instance = super().__call__(server=server,lang=lang)
                # self.instances[key]=instance
                # return instance
    def __call__(self, server='US',lang='en'):
        key=(server,lang)
        with self.lock:
            if key in self.locks:
                lock=self.locks[key]
            else:
                lock=threading.Lock()
                self.locks[key]=lock
        with lock:
            with self.lock:
                if key in self.instances:
                    return self.instances[key]
            instance = super().__call__(server=server,lang=lang)
            with self.lock:
                self.instances[key]=instance
                return instance

class Chars(metaclass=CacheInstType):
    # url_agr = 'https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/'
    # name_avatar = 'avatar/{charid}.png'
    # name_avatar2 = 'avatar/{charid}_2.png'
    # name_portrait = 'portrait/{charid}_1.png'
    # name_portrait2 = 'portrait/{charid}_2.png'
    position_tagId = {
            "RANGED": 10,
            "MELEE": 9,
    }
    profession_tagId = {
            "WARRIOR": 1,
            "SNIPER": 2,
            "TANK": 3,
            "MEDIC": 4,
            "SUPPORT": 5,
            "CASTER": 6,
            "SPECIAL": 7,
            "PIONEER": 8,
    }
    rarity_color={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }
    def __init__(self,server='US',lang='en'):
        self.server=server #US CN JP KR
        self.lang=lang #en ja ko zh
        self.lang2=resource.lang2(self.lang)
        # self.server='CN' #US CN JP KR
        # self.lang='zh' #en ja ko zh
        print('Chars.__init__',id(self),server,lang)
        self.chars={}
        self.tag_rarity={}
        self.tags_result={}
        self.tags_result5={}
        self.tags_result6={}
        self.all_tags=[]
        # self.itemObtainApproach_recruit='Recruitment & Headhunting'
        self.prep_chars()
        self.prep_tags_char()
        self.prep_chars_excel()
    def prep_chars(self):
        self.chars={}
        character_table = resource.GameData.json_table('character', lang=self.lang2)  # 'zh_CN'
        gacha_table = resource.GameData.json_table('gacha', lang=self.lang2)  # 'zh_CN'
        tagsid_name = {tag.get('tagId'):tag.get('tagName') for tag in gacha_table.get('gachaTags')}
        tag_profession = set()
        tag_position = set()
        tag_tagList = set()
        tiers=char_tier()
        def recruits():
            recruitDetail=gacha_table.get('recruitDetail')
            details=recruitDetail[recruitDetail.find('★'):].split('--------------------')
            cleaner = re.compile('<.*?>')
            res={}
            for rarity,detail in enumerate(details, start=1):
                detail=detail.strip().splitlines()
                assert detail[0].startswith('★'*rarity)
                assert len(detail)==2
                detail = re.sub(cleaner, '', detail[1])
                detail=detail.split('/')
                detail=[("'Justice Knight'" if name.strip()=='Justice Knight' else name.strip()) for name in detail]
                # print(rarity,detail)
                res[rarity]=detail
            return res
        recruits = recruits()
        def gen_tags(char_data,rarity,name):
            tags=char_data.get('tagList') or []
            profession=char_data.get('profession')
            position=char_data.get('position')
            profession_name=tagsid_name.get(Chars.profession_tagId.get(profession))
            position_name=tagsid_name.get(Chars.position_tagId.get(position))
            if recruitable(rarity,name):
                tag_profession.add(profession_name)
                tag_position.add(position_name)
                tag_tagList.update(tags)
            tags.append(profession_name)
            tags.append(position_name)
            return frozenset(tags)
        def gen_rarity(char_data):
            return resource.rarity_int(char_data.get('rarity'))
        def gen_img(name_url,char_id):
            return resource.CharImg.img(char_id,name_url)
        def recruitable(rarity,name):
            return name in recruits[rarity]
        def recruitable1(char_id):
            '''deprecated'''
            if self.server=='CN':
                if resource.json_tl('akhr').get(char_id) and resource.json_tl('akhr').get(char_id,{}).get('hidden')!=True:
                    return True
            else:
                if resource.json_tl('akhr').get(char_id) and resource.json_tl('akhr').get(char_id,{}).get('globalHidden')!=True:
                    return True
            return False
        def evolve_cost(char_data):
            # rarity=gen_rarity(char_data)
                # max_level(rarity)
                # max_e(rarity)
                # e,level=max_elevel(rarity)
                # cost2()
            # for e,maxlevel in max_level(rarity):
                # for level in range(1,maxlevel+1): 
            cost=[]
            for e,phase in enumerate(char_data.get('phases')):
                assert phase.get('evolveCost')==None if e==0 else True
                cost.append([(item.get('id'), item.get('count')) for item in (phase.get('evolveCost') or [])])
            assert cost[0]==[]
            return cost[1:]
        def dorm_skill(char_id):
            building_data = resource.GameData.json_data('building', lang=self.lang2)  # 'zh_CN'
            buffs = building_data.get('buffs',{})
            for buffChar in building_data.get('chars',{}).get(char_id,{}).get('buffChar',[]):
                for buffData in buffChar.get('buffData',[]):
                    buffId = buffData.get('buffId')
                    e = int(buffData.get('cond',{}).get('phase','0')[-1:]) # PHASE_0
                    level = int(buffData.get('cond',{}).get('level',1)) # 30
                    buff=buffs.get(buffId)
                    skillIcon=buff.get('skillIcon')
                    roomType=buff.get('roomType')
                    description=buff.get('description')
        def gen_tier(name):
            return tiers.get(name)
        for char_id,char_data in character_table.items():
            if (
                'notchar' in char_data.get('subProfessionId')
                or char_data.get('profession') in ['TOKEN','TRAP']
            ):
                continue
            name=char_data.get('name')
            rarity=gen_rarity(char_data)
            # assert recruitable(rarity,name)==recruitable1(char_id)
            char=Character(
                characterId=char_id,
                name=name,
                profession=char_data.get('profession'),
                subProfessionId=char_data.get('subProfessionId'),
                position=char_data.get('position'),
                tags=gen_tags(char_data,rarity,name),
                rarity=rarity,
                avatar=gen_img(resource.CharImg.name_avatar,char_id),
                # avatar2=gen_img(resource.CharImg.name_avatar2,char_id),
                # portrait=gen_img(resource.CharImg.name_portrait,char_id),
                # portrait2=gen_img(resource.CharImg.name_portrait2,char_id),
                itemObtainApproach=char_data.get('itemObtainApproach') or '',
                recruitable=recruitable(rarity,name),
                evolveCost=evolve_cost(char_data),
                tier=gen_tier(name),
            )
            # print(char.evolveCost)
            self.chars[char_id]=char
        self.chars = {k:v for k,v in sorted(self.chars.items(), key=lambda item:(-item[1].rarity,item[1].tier==None,item[1].tier,item[1].name))}
        self.all_tags = [tag_profession,tag_position,tag_tagList]
        
    def prep_tags_char(self):
        self.tags_result={}
        # self.tags_result5={}
        # self.tags_result6={}
        self.tag_rarity={}
        for char_id,char in self.chars.items():
            # if self.itemObtainApproach_recruit in char.itemObtainApproach:
            if char.recruitable==True:
                for tags_ in subset(char.tags,self=1):
                    self.tags_result.setdefault(tags_,{}).setdefault(char.rarity,[]).append(char)
                    # if char.rarity<6:
                        # self.tags_result.setdefault(tags_,{}).setdefault(char.rarity,[]).append(char)
                        # if char.rarity==5:
                            # self.tags_result5.setdefault(tags_,{}).setdefault(char.rarity,[]).append(char)
                    # if char.rarity==6:
                        # self.tags_result6.setdefault(tags_,{}).setdefault(char.rarity,[]).append(char)
        for tags,rarity_char in self.tags_result.items():
            m3 = min([r for r in rarity_char if r>=3 and r<=5] or [0])
            m2 = min([r for r in rarity_char if r>=2 and r<=5] or [0])
            m1 = min([r for r in rarity_char if r>=1 and r<=4] or [0])
            m=max(m3,m2,m1)
            rarity_char['rarity']=m
            if len(tags)==1:
                self.tag_rarity[next(iter(tags))]=m
        # for tags,rarity_char in self.tags_result5.items():
            # m3 = min([r for r in rarity_char if r>=3] or [0])
            # m2 = min([r for r in rarity_char if r>=2] or [0])
            # m1 = min([r for r in rarity_char if r>=1] or [0])
            # m=max(m3,m2,m1)
            # rarity_char['rarity']=m
        # for tags,rarity_char in self.tags_result6.items():
            # m3 = min([r for r in rarity_char if r>=3] or [0])
            # m2 = min([r for r in rarity_char if r>=2] or [0])
            # m1 = min([r for r in rarity_char if r>=1] or [0])
            # m=max(m3,m2,m1)
            # rarity_char['rarity']=m
        self.tag_rarity['Top Operator']=6
        self.tag_rarity['Senior Operator']=5
        self.all_tags=[sorted(list(tag_sub),key=lambda tag:(self.tag_rarity.get(tag),tag)) for tag_sub in self.all_tags]
        self.all_tags+=[['Senior Operator','Top Operator']]
    def sort_result(self,res):
        def sort(item):
            tags_,d=item
            rarity=d['rarity']
            tier=d[rarity][0].tier
            return -rarity,tier,
        return {k:v for k,v in sorted(res.items(), key=sort)}
    def recruit(self,tags):
        res={}
        for tags_ in subset(tags,self=1):
            if tags_ in self.tags_result:
                d=self.tags_result.get(tags_).copy()
                if 'Top Operator' in tags:
                    if 6 in d:
                        t=frozenset(['Top Operator']+list(tags_))
                        res[t]={6:d[6],'rarity':6}
                if 'Senior Operator' in tags:
                    if 5 in d:
                        t=frozenset(['Senior Operator']+list(tags_))
                        res[t]={5:d[5],'rarity':5}
                if 6 in d:
                    del d[6]
                if len(d)>1:
                    res[tags_]=d
        return self.sort_result(res)
        # if 'Top Operator' in tags:
            # return self.recruit6(tags)
        # elif 'Senior Operator' in tags:
            # return self.recruit5(tags)
        # else:
            # return self.sort_result({tags_:self.tags_result.get(tags_) for tags_ in subset(tags,self=1) if tags_ in self.tags_result})
    # def recruit5(self,tags):
        # return self.sort_result({tags_:self.tags_result5.get(tags_) for tags_ in subset(tags,self=1) if tags_ in self.tags_result5})
    # def recruit6(self,tags):
        # return self.sort_result({tags_:self.tags_result6.get(tags_) for tags_ in subset(tags,self=1) if tags_ in self.tags_result6})

    def prep_chars_excel(self):
        Chars.chars_excel={}
        Chars.chars_excel = {characterId:CharacterExcel.from_character(char) for characterId,char in self.chars.items()}

    def save_excel(self):
        df = pd.DataFrame(Chars.chars_excel.values())
        df.to_excel('char.xlsx')
        print(df)

if __name__ == "__main__":
    data=Chars(server='US',lang='en')
    data.save_excel()
    
    # tags = ['减速','控场','费用回复','特种','远程位',]
    tags = ['Vanguard', 'Crowd-Control', 'DP-Recovery', 'Debuff', 'Healing']
    res = data.recruit(tags)
    pprint.pprint(res)
        
    gacha_table = resource.GameData.json_table('gacha', lang='en_US')  # 'zh_CN'
    for gachaPool in gacha_table.get('gachaPoolClient'):
        gachaPoolSummary = gachaPool.get('gachaPoolSummary')
        if gachaPoolSummary=='Ends June 4 03:59':
            rarityPickCharDict = gachaPool.get('dynMeta').get('rarityPickCharDict',{})
            if rarityPickCharDict:
                char_t5=[]
                char_t6=[]
                for charid in rarityPickCharDict.get('TIER_5'):
                    char=data.chars.get(charid)
                    char_t5.append(char)
                for charid in rarityPickCharDict.get('TIER_6'):
                    char=data.chars.get(charid)
                    char_t6.append(char)
                print(gachaPoolSummary)
                print('\tTIER_5')
                for char in sorted(char_t5,key=lambda char:(char.tier==None,char.tier)):
                    print('\t\t',char.name,char.tier)
                print('\tTIER_6')
                for char in sorted(char_t6,key=lambda char:(char.tier==None,char.tier)):
                    print('\t\t',char.name,char.tier)
                
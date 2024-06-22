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
    dorm_skills:list
    attributes:str
    blockCnt:int
    def __repr__(self):
        s=f'Character({self.name})'
        return s
    def __str__(self):
        s=f'{self.name}'
        return s

@dataclass
class DormSkill:
    charid:str
    charname:str
    elevel:tuple
    roomType:str
    icon:str
    description:str

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
    blockCnt:int
    # dorm_skill_0:str
    # dorm_skill_1:str
    @classmethod
    def from_character(cls, char):
        # dorm_skills=['','']
        # for idx,skill in enumerate(char.dorm_skills):
            # for (e,level),(roomType,icon,description) in skill.items():
                # dorm_skills[idx]+=f'E{e}L{level} {roomType} {description}\n'
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
            blockCnt=char.blockCnt,
            # dorm_skill_0=dorm_skills[0],
            # dorm_skill_1=dorm_skills[1],
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


def clean_html(s):
    return re.sub(clean_html.cleaner, '', s)
clean_html.cleaner = re.compile('<.*?>')

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
        self.dskills=[]
        character_table = resource.GameData.json_table('character', lang=self.lang2)  # 'zh_CN'
        gacha_table = resource.GameData.json_table('gacha', lang=self.lang2)  # 'zh_CN'
        tagsid_name = {tag.get('tagId'):tag.get('tagName') for tag in gacha_table.get('gachaTags')}
        building_data = resource.GameData.json_data('building', lang=self.lang2)  # 'zh_CN'
        tag_profession = set()
        tag_position = set()
        tag_tagList = set()
        tiers=char_tier()
        def recruits():
            recruitDetail=gacha_table.get('recruitDetail')
            details=recruitDetail[recruitDetail.find('★'):].split('--------------------')
            # cleaner = re.compile('<.*?>')
            res={}
            for rarity,detail in enumerate(details, start=1):
                detail=detail.strip().splitlines()
                assert detail[0].startswith('★'*rarity)
                assert len(detail)==2
                # detail = re.sub(cleaner, '', detail[1])
                detail=clean_html(detail[1])
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
        def attributes(char_data):
            blockCnt=None
            for e,phase in enumerate(char_data.get('phases')):
                for attributesKeyFrame in (phase.get('attributesKeyFrames') or []):
                    level=attributesKeyFrame.get('level')
                    attributes=attributesKeyFrame.get('data')
                    blockCnt=attributes.get('blockCnt')
            # print(blockCnt)
            return blockCnt
        def gen_blockCnt(char_data):
            blockCnt=None
            for e,phase in enumerate(char_data.get('phases')):
                for attributesKeyFrame in (phase.get('attributesKeyFrames') or []):
                    level=attributesKeyFrame.get('level')
                    attributes=attributesKeyFrame.get('data')
                    blockCnt=attributes.get('blockCnt')
            return blockCnt
        # dss=set()
        def dorm_skill(char_id,name):
            buffs = building_data.get('buffs',{})
            dorm_skills=[]
            for idx,buffChar in enumerate(building_data.get('chars',{}).get(char_id,{}).get('buffChar',[])):
                skill={}
                for buffData in buffChar.get('buffData',[]):
                    buffId = buffData.get('buffId')
                    e = int(buffData.get('cond',{}).get('phase','0')[-1:]) # PHASE_0
                    level = int(buffData.get('cond',{}).get('level',1)) # 30
                    buff=buffs.get(buffId)
                    skillIcon=buff.get('skillIcon')
                    icon=resource.Img.dorm_skill(skillIcon)
                    roomType=buff.get('roomType')
                    description=clean_html(buff.get('description'))
                    skill[(e,level)]=(roomType,icon,description)
                    ds=DormSkill(
                        charid=char_id,
                        charname=name,
                        elevel=(e,level),
                        roomType=roomType,
                        icon=icon,
                        description=description,
                    )
                    self.dskills.append(ds)
                    # dss.add((e,level))
                dorm_skills.append(skill)
            # print(dorm_skills)
            assert len(dorm_skills) in [2,0], char_id
            return dorm_skills
        def gen_tier(name):
            # if name not in tiers:
                # print('notier',name)
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
                avatar=resource.Img.avatar(char_id),
                # avatar2=resource.Img.avatar2(char_id),
                # portrait=resource.Img.portrait(char_id),
                # portrait2=resource.Img.portrait2(char_id),
                itemObtainApproach=char_data.get('itemObtainApproach') or '',
                recruitable=recruitable(rarity,name),
                evolveCost=evolve_cost(char_data),
                tier=gen_tier(name),
                dorm_skills=dorm_skill(char_id,name),
                attributes=attributes(char_data),
                blockCnt=gen_blockCnt(char_data),
            )
            # print(char.evolveCost)
            self.chars[char_id]=char
        self.chars = {k:v for k,v in sorted(self.chars.items(), key=lambda item:(-item[1].rarity,item[1].tier==None,item[1].tier,item[1].name))}
        self.all_tags = [tag_profession,tag_position,tag_tagList]
        # print(dss) #{(0, 1), (0, 30), (1, 1), (2, 1)}
    def prep_subtier(self):
        for char_id,char in self.chars.items():
            char.rarity
            char.tier
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
            tiers = [char.tier for char in d[rarity] if isinstance(char.tier,int)]
            hastier=len(tiers)>0
            return -rarity,hastier and tiers[0],hastier and tiers[-1]
        # print(res)
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
        self.chars_excel={}
        self.chars_excel = {characterId:CharacterExcel.from_character(char) for characterId,char in self.chars.items()}

    def save_excel(self):
        df = pd.DataFrame(self.chars_excel.values())
        df.to_excel('char.xlsx')
        print(df)
        df1 = pd.DataFrame(self.dskills)
        df1.to_excel('dormskills.xlsx')

import datetime
@dataclass
class GACHAPool:
    gachaPoolId:str
    openTime:datetime.datetime
    endTime:datetime.datetime
    strtime:str
    char_t5:list
    char_t6:list
    strchar:str
    def __str__(self):
        return f'{self.gachaPoolId}: {self.strtime}\n{self.strchar}'
if __name__ == "__main__":
    data=Chars(server='US',lang='en')
    data.save_excel()
    
    # tags = ['减速','控场','费用回复','特种','远程位',]
    # tags = ['Vanguard', 'Crowd-Control', 'DP-Recovery', 'Debuff', 'Healing']
    # res = data.recruit(tags)
    # pprint.pprint(res)
    now=datetime.datetime.now()
    gacha_table = resource.GameData.json_table('gacha', lang='en_US')  # 'zh_CN'
    gs=[]
    gs1=[]
    for gachaPool in gacha_table.get('gachaPoolClient'):
        openTime=datetime.datetime.fromtimestamp(gachaPool.get('openTime'))
        endTime=datetime.datetime.fromtimestamp(gachaPool.get('endTime'))
        if (isopen:=openTime<now<endTime) or (now<openTime):
            gachaPoolId=gachaPool.get('gachaPoolId')
            strtime=f'{openTime.strftime(r"%Y-%m %d_%H:%M")}~{endTime.strftime(r"%d_%H:%M")}'
            char_t5=[]
            char_t6=[]
            strchar=''
            if (dynMeta:=gachaPool.get('dynMeta')):
                if (main6RarityCharId:=dynMeta.get('main6RarityCharId')):
                    char_t6.append(data.chars.get(main6RarityCharId))
                if (sub6RarityCharId:=dynMeta.get('sub6RarityCharId')):
                    char_t6.append(data.chars.get(sub6RarityCharId))
                if (rare5CharList:=dynMeta.get('rare5CharList')):
                    char_t5+=[data.chars.get(charid) for charid in rare5CharList]
                # chooseRuleConst = dynMeta.get('chooseRuleConst')
                # homeDescConst = dynMeta.get('homeDescConst')
                # star5ChooseRuleConst = dynMeta.get('star5ChooseRuleConst')
                # star6ChooseRuleConst = dynMeta.get('star6ChooseRuleConst')
                # gachaPoolSummary = gachaPool.get('gachaPoolSummary') #'Ends June 4 03:59'
                if (rarityPickCharDict := dynMeta.get('rarityPickCharDict') or {}):
                    char_t5+=[data.chars.get(charid) for charid in rarityPickCharDict.get('TIER_5') or []]
                    char_t6+=[data.chars.get(charid) for charid in rarityPickCharDict.get('TIER_6') or []]
                strchar+='\tR5:\n'
                for char in sorted(char_t5,key=lambda char:(char.tier==None,char.tier)):
                    strchar+=f'\t\t{char.name}.T{char.tier}\n'
                strchar+='\tR6:\n'
                for char in sorted(char_t6,key=lambda char:(char.tier==None,char.tier)):
                    strchar+=f'\t\t{char.name}.T{char.tier}\n'
            g=GACHAPool(
                gachaPoolId=gachaPoolId,
                openTime=openTime,
                endTime=endTime,
                strtime=strtime,
                char_t5=char_t5,
                char_t6=char_t6,
                strchar=strchar,
            )
            if isopen:
                gs.append(g)
            else:
                gs1.append(g)
            # if gachaPoolSummary=='Ends June 4 03:59':
                # break
    for g in gs:
        print(g)
    print('-'*44)
    for g in gs1:
        print(g)

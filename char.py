from dataclasses import dataclass
from itertools import combinations
import json
import pprint
import os
import re

import pandas as pd

import anhrtags
from anhrtags import GData,TimeCost
try:
    import mods.shellcmd1 as shellcmd
except:
    import shellcmd1 as shellcmd

app_path = os.path.dirname(__file__)
os.chdir(app_path)

try:
    from test import dump
except:
    def dump(**a):
        pass

# class Data:
    # server='US'
    # lang='en'
    # lang2={'en':'en_US','ja':'ja_JP','ko':'ko_KR','zh':'zh_CN','ch':'zh_TW',}
    # rarity_color={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }
    # itemObtainApproach_recruit='Recruitment & Headhunting'
    # chars={}
    # tag_rarity={}
    # tags_result={}
    # all_tags=[]
    # url_agr = 'https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/'
    # name_avatar = 'avatar/{charid}.png'
    # name_avatar2 = 'avatar/{charid}_2.png'
    # name_portrait = 'portrait/{charid}_1.png'
    # name_portrait2 = 'portrait/{charid}_2.png'

    # position_tagId = {
            # "RANGED": 10,
            # "MELEE": 9,
    # }
    # profession_tagId = {
            # "WARRIOR": 1,
            # "SNIPER": 2,
            # "TANK": 3,
            # "MEDIC": 4,
            # "SUPPORT": 5,
            # "CASTER": 6,
            # "SPECIAL": 7,
            # "PIONEER": 8,
    # }

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
    def __repr__(self):
        s=f'Character({self.name})'
        return s
    def __str__(self):
        s=f'{self.name}'
        return s

@dataclass
class CharacterExcel:
    characterId:str
    name:str
    profession:str
    subProfessionId:str
    position:str
    rarity:str
    tags:frozenset
    @classmethod
    def from_character(cls, char):
        return cls(
            characterId=char.characterId,
            name=char.name,
            profession=char.profession.title(),
            subProfessionId=char.subProfessionId.title(),
            position=char.position.title(),
            rarity=char.rarity,
            tags=char.tags,
        )

def subset(items,maxtag=5,self=0):
    for i in range(1,min(maxtag+1,len(items)+self)):
        for s in combinations(items, i):
            yield frozenset(s)

class Chars:
    url_agr = 'https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/'
    name_avatar = 'avatar/{charid}.png'
    name_avatar2 = 'avatar/{charid}_2.png'
    name_portrait = 'portrait/{charid}_1.png'
    name_portrait2 = 'portrait/{charid}_2.png'
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
    lang2={'en':'en_US','ja':'ja_JP','ko':'ko_KR','zh':'zh_CN','ch':'zh_TW',}
    rarity_color={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }
    def __init__(self,server='US',lang='en'):
        self.server=server #US CN JP KR
        self.lang=lang #en ja ko zh
        # self.server='CN' #US CN JP KR
        # self.lang='zh' #en ja ko zh
        print('Chars.__init__',server,lang)
        self.chars={}
        self.tag_rarity={}
        self.tags_result={}
        self.all_tags=[]
        # self.itemObtainApproach_recruit='Recruitment & Headhunting'
        self.prep_chars()
        self.prep_tags_char()
        self.prep_chars_excel()
    def prep_chars(self):
        self.chars={}
        lang2=Chars.lang2.get(self.lang)
        character_table = GData.json_table('character', lang=lang2)  # 'zh_CN'
        gacha_table = GData.json_table('gacha', lang=lang2)  # 'zh_CN'
        tagsid_name = {tag.get('tagId'):tag.get('tagName') for tag in gacha_table.get('gachaTags')}
        tag_profession = set()
        tag_position = set()
        tag_tagList = set()
        def gen_tags(char_data):
            tags=char_data.get('tagList') or []
            profession=char_data.get('profession')
            position=char_data.get('position')
            profession_name=tagsid_name.get(Chars.profession_tagId.get(profession))
            position_name=tagsid_name.get(Chars.position_tagId.get(position))
            if recruitable(char_id):
                tag_profession.add(profession_name)
                tag_position.add(position_name)
                tag_tagList.update(tags)
            tags.append(profession_name)
            tags.append(position_name)
            return frozenset(tags)
        def gen_rarity(char_data):
            return int(char_data.get('rarity')[-1:])
        def gen_img(url_raw,char_id):
            file = url_raw.format(charid=char_id)
            url = Chars.url_agr + file
            return GData.img(file,url)
        def recruitable(char_id):
            if self.server=='CN':
                if GData.json_tl('akhr').get(char_id) and GData.json_tl('akhr').get(char_id,{}).get('hidden')!=True:
                    return True
            else:
                if GData.json_tl('akhr').get(char_id) and GData.json_tl('akhr').get(char_id,{}).get('globalHidden')!=True:
                    return True
            return False
        for char_id,char_data in character_table.items():
            if (
                'notchar' in char_data.get('subProfessionId')
                or char_data.get('profession') in ['TOKEN','TRAP']
            ):
                continue
            char=Character(
                characterId=char_id,
                name=char_data.get('name'),
                profession=char_data.get('profession'),
                subProfessionId=char_data.get('subProfessionId'),
                position=char_data.get('position'),
                tags=gen_tags(char_data),
                rarity=gen_rarity(char_data),
                avatar=gen_img(Chars.name_avatar,char_id),
                # avatar2=gen_img(Chars.name_avatar2,char_id),
                # portrait=gen_img(Chars.name_portrait,char_id),
                # portrait2=gen_img(Chars.name_portrait2,char_id),
                itemObtainApproach=char_data.get('itemObtainApproach') or '',
                recruitable=recruitable(char_id),
            )
            self.chars[char_id]=char
        self.chars = {k:v for k,v in sorted(self.chars.items(), key=lambda item:(-item[1].rarity,item[1].name))}
        self.all_tags = [tag_profession,tag_position,tag_tagList]
        
    def prep_tags_char(self):
        self.tags_result={}
        self.tag_rarity={}
        for char_id,char in self.chars.items():
            # if self.itemObtainApproach_recruit in char.itemObtainApproach:
            if char.recruitable==True:
                if char.rarity<6:
                    for tags_ in subset(char.tags,self=1):
                        self.tags_result.setdefault(tags_,{}).setdefault(char.rarity,[]).append(char)
        for tags,rarity_char in self.tags_result.items():
            m3 = min([r for r in rarity_char if r>=3] or [0])
            m2 = min([r for r in rarity_char if r>=2] or [0])
            m1 = min([r for r in rarity_char if r>=1] or [0])
            m=max(m3,m2,m1)
            rarity_char['rarity']=m
            if len(tags)==1:
                self.tag_rarity[next(iter(tags))]=m
        self.all_tags=[sorted(list(tag_sub),key=lambda tag:(self.tag_rarity.get(tag),tag)) for tag_sub in self.all_tags]

    def sort_result(self,res):
        return {k:v for k,v in sorted(res.items(), key=lambda item:item[1]['rarity'],reverse=True)}

    def recruit(self,tags):
        return self.sort_result({tags_:self.tags_result.get(tags_) for tags_ in subset(tags,self=1) if tags_ in self.tags_result})

    def prep_chars_excel(self):
        Chars.chars_excel={}
        Chars.chars_excel = {characterId:CharacterExcel.from_character(char) for characterId,char in self.chars.items()}

    def save_excel(self):
        df = pd.DataFrame(Chars.chars_excel.values())
        df.to_excel('char.xlsx')
        print(df)

if __name__ == "__main__":
    data=Chars()
    data.save_excel()
    
    # tags = ['减速','控场','费用回复','特种','远程位',]
    tags = ['Vanguard', 'Crowd-Control', 'DP-Recovery', 'Debuff', 'Healing']
    res = data.recruit(tags)
    pprint.pprint(res)

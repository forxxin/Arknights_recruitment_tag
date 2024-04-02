import os
import pickle
import json
from functools import cache
import urllib.request
import tkinter as tk
from itertools import combinations

app_path = os.path.dirname(__file__)
os.chdir(app_path)
def subset(taglist,maxtag=6,self=0):
    for i in range(1,min(maxtag+1,len(taglist)+self)):
        for s in combinations(taglist, i):
            yield frozenset(s)

class Character():
    version=8
    @staticmethod
    @cache
    def _tl_akhr():
        url_tl_akhr = 'https://github.com/Aceship/AN-EN-Tags/raw/master/json/tl-akhr.json'
        file_tl_akhr = 'tl-akhr.json'
        if not os.path.isfile(file_tl_akhr):
            urllib.request.urlretrieve(url_tl_akhr, file_tl_akhr)
        with open(file_tl_akhr, "r", encoding="utf-8") as f:
            return {akhr.get('id'):akhr for akhr in json.load(f)}

    @staticmethod
    @cache
    def _character_table():
        # lang='ja_JP'
        # lang='ko_KR'
        # lang='zh_TW'
        # lang='zh_CN'
        lang='en_US'
        url_character_table = f'https://github.com/Aceship/AN-EN-Tags/raw/master/json/gamedata/{lang}/gamedata/excel/character_table.json'
        file_character_table = f'character_table_{lang}.json'
        if not os.path.isfile(file_character_table):
            urllib.request.urlretrieve(url_character_table, file_character_table)
        with open(file_character_table, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def key_type(typa):
        keys=[]
        for char_id,char_data in Character._character_table().items():
            for key in ['name', 'description', 'canUseGeneralPotentialItem', 'canUseActivityPotentialItem', 'potentialItemId', 'activityPotentialItemId', 'classicPotentialItemId', 'nationId', 'groupId', 'teamId', 'displayNumber', 'appellation', 'position', 'tagList', 'itemUsage', 'itemDesc', 'itemObtainApproach', 'isNotObtainable', 'isSpChar', 'maxPotentialLevel', 'rarity', 'profession', 'subProfessionId', 'trait', 'phases', 'skills', 'displayTokenDict', 'talents', 'potentialRanks', 'favorKeyFrames', 'allSkillLvlup']:
                if isinstance(char_data[key],typa):
                    if key not in keys:
                        keys.append(key)
        return keys

    @staticmethod
    def recruitable(char_id):
        # Character._tl_akhr().get(char_id,{}).get('globalHidden')!=True
        # 'Recruitment' in (char_data.get('itemObtainApproach','') or '')
        # char_data.get('isNotObtainable','')==False
        if Character._tl_akhr().get(char_id) and Character._tl_akhr().get(char_id,{}).get('globalHidden')!=True:
            return True

    @staticmethod
    @cache
    def get_all(key):
        values = []
        for char_id,char_data in Character._character_table().items():
            if Character.recruitable(char_id):
                if key in Character.key_type(list):
                    for value in char_data.get(key,[]) or []:
                        if value not in values:
                            values.append(value)
                else:
                    value = char_data.get(key,'')
                    if key=='profession':
                        value=Character.profession_name.get(value,value)
                    if value not in values:
                        values.append(value)
        return values

    profession_name = {  
        "WARRIOR": "Guard",
        "SNIPER": "Sniper",
        "TANK": "Defender",
        "MEDIC": "Medic",
        "SUPPORT": "Supporter",
        "CASTER": "Caster",
        "SPECIAL": "Specialist",
        "PIONEER": "Vanguard",
    }
    @staticmethod
    @cache
    def _recruit_tag(tier_str='345'):        
        # 1234 2345 345 5 6
        tier=[]
        for i in tier_str:
            tier.append(f'TIER_{i}')

        character_tag={}
        for char_id,char_data in Character._character_table().items():
            if Character.recruitable(char_id) and char_data.get('rarity','None') in tier:
                tags=set(char_data.get('tagList',[])or[])
                profession=char_data.get('profession')
                tags.add(Character.profession_name.get(profession,profession))
                tags.add(char_data.get('position'))
                character_tag[char_id]=tags
        return character_tag
        
    @staticmethod
    def search(tag,tier_str='345'):
        if isinstance(tag,str):
            tag=[tag]
        return Character.search_(frozenset(tag),tier_str)

    @staticmethod
    @cache
    def search_(tag,tier_str='345'):
        def _search():
            for name,_tag in Character._recruit_tag(tier_str).items():
                if set(tag).issubset(_tag):
                    yield name
        return list(_search())
        
    @staticmethod
    def search_rarity(char_ids):
        if char_ids:
            raritys=[]
            for char_id in char_ids:
                rarity = Character._character_table()[char_id].get('rarity')
                raritys.append(rarity)
            raritys.sort()
            return int(raritys[0][-1:])

    @staticmethod
    def _rarity(tag,tier_str='345'):
        return Character.search_rarity(Character.search(tag,tier_str))
        
    @staticmethod
    def rarity(tag) -> int:
        rarity = Character._rarity(tag, '345')
        if rarity:
            return rarity
        rarity = Character._rarity(tag, '2345')
        if rarity:
            return rarity
        rarity = Character._rarity(tag, '1234')
        return rarity

    @staticmethod
    @cache
    def tag_byrarity():
        x = {tag:Character.rarity(tag) for tag in Character.tagList+Character.profession+Character.position}
        return {k: v for k, v in sorted(x.items(), key=lambda item: item[1], reverse=True)}

    @staticmethod
    def comb(taglist=None,maxtag=6):
        if taglist==None:
            taglist=Character.all_tagList[:]
        tagset_list=list(subset(taglist,maxtag=maxtag,self=1))
        tagset_list_norepeat=[]
        for tagset in tagset_list:
            ok=True
            if Character.rarity(tagset):
                for subtagset in subset(tagset,maxtag=maxtag,self=0):
                    if Character.rarity(subtagset) and Character.rarity(tagset)<=Character.rarity(subtagset):
                        ok=False
                        break
            else:
                ok=False
            if ok:
                tagset_list_norepeat.append(tagset)
        return tagset_list_norepeat

    @staticmethod
    def comb_dict(taglist=None,maxtag=6):
        tagset_list = Character.comb(taglist,maxtag)
        tagset_dict={}
        added=[]
        for tag in Character.tag_byrarity():
            for tagset in tagset_list:
                if tag in tagset and tagset not in added:
                    taglist=list(tagset)
                    taglist.remove(tag)
                    tagset_dict.setdefault(tag,[]).append(taglist)
                    added.append(tagset)
        return tagset_dict

    @staticmethod
    @cache
    def min_tier(tier_str):
        return min([int(i) for i in tier_str])

    @staticmethod
    def tagset_format(taglist=None,maxtag=6):
        if taglist==None:
            return Character._tagset_format(taglist,maxtag)
        else:
            return Character._tagset_format(frozenset(taglist),maxtag)

    @staticmethod
    @cache
    def _tagset_format(taglist=None,maxtag=6):
        txt_data=[]
        def txt_insert(value,style=''):
            txt_data.append((value,style))
        def generate_txt_data(tagset_dict):
            for tag,part_tags in tagset_dict.items():
                show=False
                rarity = Character.rarity(tag)
                for part_tag in part_tags:
                    if part_tag:
                        show=True
                        break
                if not (rarity==3 and not show and taglist==None):
                    txt_insert(tag, rarity)
                if show:
                    txt_insert(' '*(max(15-len(tag),1))+'+ ')
                    for part_tag in part_tags:
                        if part_tag:
                            rarity1=Character.rarity([tag]+part_tag)
                            txt_insert('+'.join(part_tag), rarity1)
                            txt_insert(' ')
                if not (rarity==3 and not show and taglist==None):
                    txt_insert('\n')
        
        tagset_dict = Character.comb_dict(taglist,maxtag)
        generate_txt_data(tagset_dict)
        return txt_data

    @staticmethod
    def hr_all():
        result_file="ArknightsRecruitmentTag.tmp"
        def save_result(obj):
            with open(result_file, "wb") as pickle_file:
                pickle.dump([Character.version,obj], pickle_file, pickle.HIGHEST_PROTOCOL)
        def load_result():
            try:
                with open(result_file, "rb") as pickle_file:
                    version,obj = pickle.load(pickle_file)
                    if version==Character.version:
                        return obj
            except: pass
            return []
        txt_data=load_result()
        if not txt_data:
            def txt_insert(value,style=''):
                txt_data.append((value,style))
            for i in range(6,0,-1):
                txt_insert(f"t{i}", i)
            txt_insert("\n")
            txt_insert("Top Operator", 6)
            txt_insert("\n")
            txt_insert("Senior Operator", 5)
            txt_insert("\n")
            txt_data+=Character.tagset_format()
            save_result(txt_data)
        return txt_data

Character.profession=sorted([Character.profession_name.get(profession,profession) for profession in Character.get_all('profession')])
Character.position=sorted(Character.get_all('position'))
Character.tagList=sorted(Character.get_all('tagList'))
Character.all_tagList=sorted(Character.tagList+Character.profession+Character.position)

def ui_hr_tag(tags=[]):
    class Checkbar(tk.Frame):
        def __init__(self, parent=None, picks=[]):
            super().__init__(parent)
            self.checks_value = []
            self.checks={}
            for r,checklist in enumerate(picks):
                for c,tag in enumerate(checklist):
                    value = tk.StringVar(value="")
                    chk = tk.Checkbutton(self, text=tag, variable=value, onvalue=tag, offvalue="", indicatoron=False,foreground=colors.get(Character.rarity(tag),'black'))
                    chk.grid(row=r, column=c)
                    self.checks[tag]=chk
                    self.checks_value.append(value)
            btnk = tk.Button(self,text="Ok",command=self.ok)
            btnc = tk.Button(self,text="Clear",command=lambda:self.select([]))
            btnk.grid(row=len(picks), column=0)
            btnc.grid(row=len(picks), column=1)
            self.real_ok=None
        def ok(self):
            if self.real_ok:
                self.real_ok(self.check())
        def check(self):
            return [value.get() for value in self.checks_value if value.get()]
        def select(self,tags):
            for tag,chk in self.checks.items():
                if tag in tags:
                    chk.select()
                else:
                    chk.deselect()
    def txt_color(txt):
        for i in range(6,0,-1):
            txt.tag_config(str(i), background=colors.get(i,'white'), foreground="black")
            txt.tag_config(i, background=colors.get(i,'white'), foreground="black")
        txt.tag_config('', background="white", foreground="black")
    def real_txt_insert(txt, txt_data):
        for value,style in txt_data:
            txt.insert('end',value,style)

    root = tk.Tk()
    root.title("Arknights Recruitment Tag")
    
    txt_frame = tk.Frame(root, bg='white', width=450, height=60, pady=3)
    txtm_frame = tk.Frame(root, bg='white', width=450, height=60, pady=3)
    
    colors={6:'darkorange', 5:'gold', 4:'plum', 3:'deepskyblue', 2:'lightyellow', 1:'lightgrey', }

    check_frame=Checkbar(root,[Character.profession,Character.position,Character.tagList])
    print(Character.profession) 
    print(Character.position) 
    print(Character.tagList)

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    txt_frame.grid(row=0, sticky="nsew")
    check_frame.grid(row=1, sticky="nsew")
    txtm_frame.grid(row=2, sticky="nsew")

    txt = tk.Text(txt_frame, wrap='none',width=5,height=10)
    txtm = tk.Text(txtm_frame, wrap='none',width=5,height=10)
    txt.pack(fill="both", expand=True)
    txtm.pack(fill="both", expand=True)
    
    txt_color(txt)
    txt_color(txtm)
    
    txt_data = Character.hr_all()
    txt.configure(state='normal')
    real_txt_insert(txt, txt_data)
    text=txt.get('1.0', 'end-1c').splitlines()
    txt_width=len(max(text, key=len))
    txt.configure(height=len(text),width=txt_width)
    txt.configure(state='disabled')
    def ok(tags):
        txt_data=[]
        txt_data+=Character.tagset_format(taglist=tags,maxtag=len(tags))
        txtm.configure(state='normal')
        txtm.delete("1.0",tk.END)
        txtm.insert('end', f"{tags}\n")
        real_txt_insert(txtm, txt_data)
        text=txtm.get('1.0', 'end-1c').splitlines()
        width=len(max(text, key=len))
        txtm.configure(height=len(text),width=max(width,txt_width))
        txtm.configure(state='disabled')
    if tags:
        check_frame.select(tags)
        ok(tags)
    check_frame.real_ok=ok
    root.mainloop()
    
if __name__ == "__main__":
    tags=['Caster', 'Defense']
    ui_hr_tag(tags)

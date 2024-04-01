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
    @staticmethod
    @cache
    def _tl_akhr() -> dict:
        url_tl_akhr = 'https://github.com/Aceship/AN-EN-Tags/raw/master/json/tl-akhr.json'
        file_tl_akhr = 'tl-akhr.json'
        if not os.path.isfile(file_tl_akhr):
            urllib.request.urlretrieve(url_tl_akhr, file_tl_akhr)
        with open(file_tl_akhr, "r", encoding="utf-8") as f:
            return {akhr.get('id'):akhr for akhr in json.load(f)}

    @staticmethod
    @cache
    def _character_table() -> dict:
        url_character_table = 'https://github.com/Aceship/AN-EN-Tags/raw/master/json/gamedata/en_US/gamedata/excel/character_table.json'
        file_character_table = 'character_table.json'
        if not os.path.isfile(file_character_table):
            urllib.request.urlretrieve(url_character_table, "character_table.json")
        with open(file_character_table, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def key_type(typa) -> list:
        keys=[]
        for char_id,char_data in Character._character_table().items():
            for key in ['name', 'description', 'canUseGeneralPotentialItem', 'canUseActivityPotentialItem', 'potentialItemId', 'activityPotentialItemId', 'classicPotentialItemId', 'nationId', 'groupId', 'teamId', 'displayNumber', 'appellation', 'position', 'tagList', 'itemUsage', 'itemDesc', 'itemObtainApproach', 'isNotObtainable', 'isSpChar', 'maxPotentialLevel', 'rarity', 'profession', 'subProfessionId', 'trait', 'phases', 'skills', 'displayTokenDict', 'talents', 'potentialRanks', 'favorKeyFrames', 'allSkillLvlup']:
                if isinstance(char_data[key],typa):
                    if key not in keys:
                        keys.append(key)
        return keys

    @staticmethod
    @cache
    def get_all(key) -> list:
        tags = []
        for char_id,char_data in Character._character_table().items():
            if 'Recruitment' in (char_data.get('itemObtainApproach','') or '') and char_data.get('isNotObtainable','')==False:
                if key in Character.key_type(str):
                    tag = char_data.get(key,'')
                    if key=='profession':
                        tag=Character.profession_name.get(tag,tag)
                    if tag not in tags:
                        tags.append(tag)
                elif key in Character.key_type(list):
                    for tag in char_data.get(key,[]) or []:
                        if tag not in tags:
                            tags.append(tag)
        return tags

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
    def _recruit_tag(tier_str='345') -> dict:        
        # 1234 2345 345 5 6
        tier=[]
        for i in tier_str:
            tier.append(f'TIER_{i}')

        character_tag={}
        for char_id,char_data in Character._character_table().items():
            if Character._tl_akhr().get(char_id,{}).get('globalHidden')!=True and char_data.get('rarity','None') in tier:
                tags=set(char_data.get('tagList',[])or[])
                profession=char_data.get('profession')
                tags.add(Character.profession_name.get(profession,profession))
                tags.add(char_data.get('position'))
                character_tag[char_id]=tags
        return character_tag
        
    @staticmethod
    def search(tag,tier_str='345') -> list:
        if isinstance(tag,str):
            tag=[tag]
        return Character.search_(frozenset(tag),tier_str)

    @staticmethod
    @cache
    def search_(tag,tier_str='345') -> list:
        def _search():
            for name,_tag in Character._recruit_tag(tier_str).items():
                if set(tag).issubset(_tag):
                    yield name
        return list(_search())
        
    @staticmethod
    def search_rarity(char_ids) -> list:
        if char_ids:
            raritys=[]
            for char_id in char_ids:
                rarity = Character._character_table()[char_id].get('rarity')
                raritys.append(rarity)
            raritys.sort()
            return int(raritys[0][-1:])
            
    @staticmethod
    def rarity(tag,tier_str='345') -> list:
        return Character.search_rarity(Character.search(tag,tier_str))

    @staticmethod
    @cache
    def taglist_byrarity():
        _taglist_byrarity=[]
        rarity_single_tag={}
        for tag in Character.tagList+Character.profession+Character.position:
            rarity = Character.rarity(frozenset([tag]), '345')
            if rarity:
                rarity_single_tag.setdefault(rarity,[]).append(tag)
                continue
            rarity = Character.rarity(frozenset([tag]), '2345')
            if rarity:
                rarity_single_tag.setdefault(rarity,[]).append(tag)
                continue
            rarity = Character.rarity(frozenset([tag]), '1234')
            if rarity:
                rarity_single_tag.setdefault(rarity,[]).append(tag)
                continue
        for i in range(5,0,-1):
            _taglist_byrarity+=rarity_single_tag.get(i,[]) 
        return _taglist_byrarity

    @staticmethod
    def hr_tag(tier_str='345',taglist_=None,maxtag=6):
        if taglist_==None:
            taglist_=Character.all_tagList[:]
        txt_data=[]
        def txt_insert(value,style=''):
            txt_data.append((value,style))
        txt_insert("\n")
        for i in tier_str:
            txt_insert(f"t{i}", f'{i}')
        if tier_str=='5':
            txt_insert(" 9h ")
            txt_insert("Senior Operator", '5')
        if tier_str=='6':
            txt_insert(" 9h ")
            txt_insert("Top Operator", '6')
        txt_insert("\n")
        if tier_str in ['5','6']:
            return txt_data
        min_tier=min([int(i) for i in tier_str])
        tagset_list=list(subset(taglist_,maxtag=maxtag,self=1))
        tagset_rarity={}
        rarity_tagset={}
        for tagset in tagset_list:
            rarity=Character.rarity(tagset, tier_str=tier_str)
            tagset_rarity[tagset]=rarity
            rarity_tagset.setdefault(rarity,[]).append(tagset)
        tagset_list_norepeat=[]
        for tagset in tagset_list:
            ok=True
            if tagset_rarity[tagset]:
                for subtagset in subset(tagset,maxtag=maxtag,self=0):
                    if tagset_rarity[subtagset] and tagset_rarity[tagset]<=tagset_rarity[subtagset]:
                        ok=False
                        break
            else:
                ok=False
            if ok:
                tagset_list_norepeat.append(tagset)
        result={}
        added=[]
        for tag in Character.taglist_byrarity():
            for tagset in tagset_list_norepeat:
                if tag in tagset and tagset not in added:
                    taglist=list(tagset)
                    taglist.remove(tag)
                    result.setdefault(tag,[]).append(taglist)
                    added.append(tagset)

        for tag,taglists in result.items():
            show=False
            show1=False
            rarity = tagset_rarity[frozenset([tag])]
            if '345'!=tier_str:
                if rarity and min_tier<=rarity:
                    show=True
            else:
                if rarity and min_tier<rarity:
                    show=True
            for taglist in taglists:
                if taglist:
                    if '345'!=tier_str:
                        rarity1=tagset_rarity[frozenset([tag]+taglist)]
                        rarity1_=Character.rarity(frozenset([tag]+taglist), tier_str='345')
                        if (not rarity1_) or (rarity1_ and rarity1_<rarity1):
                            show1=True
                            break
                    else:
                        show1=True
                        break
            if '345'!=tier_str:
                rarity_=Character.rarity(frozenset([tag]), tier_str='345')
                if rarity_ and rarity_>=rarity:
                    show=False
            if show or show1:
                txt_insert(tag, rarity)
                txt_insert(' '*(max(15-len(tag),1)))
                if show1:
                    txt_insert('+ ')
                for taglist in taglists:
                    if taglist:
                        rarity1=tagset_rarity[frozenset([tag]+taglist)]
                        show2=True
                        if '345'!=tier_str:
                            rarity1_=Character.rarity(frozenset([tag]+taglist), tier_str='345')
                            if rarity1_ and rarity1_>=rarity1:
                                show2=False
                        if show2:
                            txt_insert('+'.join(taglist), rarity1)
                            txt_insert(' ')
                txt_insert('\n')
        return txt_data
    
    @staticmethod
    def hr_all():
        result_file="ArknightsRecruitmentTag.tmp"
        def save_result(obj):
            with open(result_file, "wb") as pickle_file:
                pickle.dump(obj, pickle_file, pickle.HIGHEST_PROTOCOL)
        def load_result():
            try:
                with open(result_file, "rb") as pickle_file:
                    return pickle.load(pickle_file)
            except:
                return []
        txt_data=load_result()
        if not txt_data:
            def txt_insert(value,style=''):
                txt_data.append((value,style))
            txt_insert("t6", '6')
            txt_insert("t5", '5')
            txt_insert("t4", '4')
            txt_insert("t3", '3')
            txt_insert("t2", '2')
            txt_insert("t1", '1')
            txt_insert("\n")
            txt_data+=Character.hr_tag(tier_str='6')
            txt_data+=Character.hr_tag(tier_str='5')
            txt_data+=Character.hr_tag(tier_str='345')
            txt_data+=Character.hr_tag(tier_str='2345')
            txt_data+=Character.hr_tag(tier_str='1234')
            save_result(txt_data)
        return txt_data

Character.profession=sorted([Character.profession_name.get(profession,profession) for profession in Character.get_all('profession')])
Character.position=sorted(Character.get_all('position'))
Character.tagList=sorted(Character.get_all('tagList'))
Character.all_tagList=sorted(Character.tagList+Character.profession+Character.position)

def ui_hr_tag(tags=[]):
    root = tk.Tk()
    root.title("Arknights Recruitment Tag")
    
    txt_frame = tk.Frame(root, bg='white', width=450, height=60, pady=3)
    txtm_frame = tk.Frame(root, bg='white', width=450, height=60, pady=3)
    
    class Checkbar(tk.Frame):
        def __init__(self, parent=None, picks=[]):
            super().__init__(parent)
            self.checks_value = []
            self.checks=[]
            for r,checklist in enumerate(picks):
                for c,pick in enumerate(checklist):
                    value = tk.StringVar(value="")
                    chk = tk.Checkbutton(self, text=pick, variable=value, onvalue=pick, offvalue="", indicatoron=False)
                    chk.grid(row=r, column=c)
                    self.checks.append(chk)
                    self.checks_value.append(value)
            btnk = tk.Button(self,text="Ok",command=self.ok)
            btnc = tk.Button(self,text="Clear",command=lambda: [check.deselect() for check in self.checks])
            btnk.grid(row=len(picks), column=0)
            btnc.grid(row=len(picks), column=1)
            self.func=None
        def ok(self):
            if self.func:
                self.func(self.check())
        def check(self):
            return [value.get() for value in self.checks_value if value.get()]
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
    def txt_color(txt):
        txt.tag_config('6', background="darkorange", foreground="black")
        txt.tag_config('5', background="gold", foreground="black")
        txt.tag_config('4', background="plum", foreground="black")
        txt.tag_config('3', background="deepskyblue", foreground="black")
        txt.tag_config('2', background="lightyellow", foreground="black")
        txt.tag_config('1', background="lightgrey", foreground="black")
        txt.tag_config('', background="white", foreground="black")
    txt_color(txt)
    txt_color(txtm)
    def real_txt_insert(txt, txt_data):
        for value,style in txt_data:
            txt.insert('end',value,style)

    txt_data = Character.hr_all()
    txt.configure(state='normal')
    real_txt_insert(txt, txt_data)
    text=txt.get('1.0', 'end-1c').splitlines()
    txt_width=len(max(text, key=len))
    txt.configure(height=len(text),width=txt_width)
    txt.configure(state='disabled')
    
    def ok(tags):
        txt_data=[]
        txt_data+=Character.hr_tag(tier_str='345',taglist_=tags,maxtag=len(tags))
        txt_data+=Character.hr_tag(tier_str='2345',taglist_=tags,maxtag=len(tags))
        txt_data+=Character.hr_tag(tier_str='1234',taglist_=tags,maxtag=len(tags))
        txtm.configure(state='normal')
        txtm.delete("1.0",tk.END)
        txtm.insert('end', f"{tags}")
        real_txt_insert(txtm, txt_data)
        text=txtm.get('1.0', 'end-1c').splitlines()
        width=len(max(text, key=len))
        txtm.configure(height=len(text),width=max(width,txt_width))
        txtm.configure(state='disabled')
    if tags:
        ok(tags)
    check_frame.func=ok
    root.mainloop()
    
if __name__ == "__main__":
    tags=['Caster', 'Defense']
    ui_hr_tag(tags)

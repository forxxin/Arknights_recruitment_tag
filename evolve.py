import os

import resource

app_path = os.path.dirname(__file__)
os.chdir(app_path)


if __name__ == "__main__":
    res={}
    for char_id,char_data in resource.GameData.json_table('character').items():
        char_data.get('rarity')
        isNotObtainable=char_data.get('isNotObtainable')
        subProfessionId=char_data.get('subProfessionId')
        if 'notchar' in subProfessionId:
            continue
        # if isNotObtainable==True:
            # print(char_id)
            # continue
        char_data.get('profession')
        char_data.get('phases')
        # res.setdefault(char_id,{})[subProfessionId]=subProfessionId
        for idx,phase in enumerate(char_data.get('phases')):
            res.setdefault(char_id,{}).setdefault(idx,[])
            for item in (phase.get('evolveCost') or []):
                i = item.get('id'), item.get('count')
                res.setdefault(char_id,{}).setdefault(idx,[]).append(i)
    print()
    for char_id,data in res.items():
        print(char_id,data)
        
    # https://raw.githubusercontent.com/Aceship/Arknight-Images/main/avatars/char_215_mantic.png

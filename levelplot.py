import dataclasses
import anhrtags
import matplotlib.pyplot as plt
import matplotlib
from functools import cache

gamedata = anhrtags.GData.json_data('gamedata',lang='zh_CN')
def cost(rarity=6,level=90,evolve=2):
    if isinstance(rarity,str):
        rarity=int(rarity[-1:])
    if isinstance(level,str):
        level=int(level)
    if isinstance(evolve,str):
        evolve=int(evolve)
    maxlevels=gamedata['maxLevel'][rarity-1]
    exps=[]
    exp_all=0
    golds=[]
    gold_all=0
    for e,maxlevel in enumerate(maxlevels):
        if e>evolve:
            break
        elif e==evolve:
            level_=level if (level<maxlevel and level>0) else maxlevel
        else:
            level_=maxlevel
        evolve_=e
        exp=gamedata['characterExpMap'][e][:level_-1]
        exps.append(exp)
        exp_all+=sum(exp)
        gold=gamedata['characterUpgradeCostMap'][e][:level_-1]
        # print(gold)
        golds.append(gold)
        gold_all+=sum(gold)
        if evolve>e:
            gold_e=gamedata['evolveGoldCost'][rarity-1][e]
            if gold_e==-1:
                gold_e=0
            # print(gold_e)
            golds.append([gold_e])
            gold_all+=gold_e
    return f'E{evolve_} {str(level_).zfill(2)} R{rarity}',exp_all,gold_all,
    return exps,golds,exp_all,gold_all

@cache
def cost1(rarity=6):
    if isinstance(rarity,str):
        rarity=int(rarity[-1:])
    result=[]
    exp_sum=0
    gold_sum=0
    for e,maxlevel in enumerate(gamedata['maxLevel'][rarity-1]):
        for level in range(1,maxlevel+1):
            exp=gamedata['characterExpMap'][e][level-2] if level>1 else 0
            if level>1:
                gold=gamedata['characterUpgradeCostMap'][e][level-2]
            else:
                gold=0
                if e>0:
                    gold=gamedata['evolveGoldCost'][rarity-1][e-1]
                if gold==-1:
                    gold=0
            exp_sum+=exp
            gold_sum+=gold
            result.append((e,level,exp_sum,gold_sum))
            # print((e,level,exp_sum,gold_sum))
        # if evolve>e:
            # golds.append([gold_e])
            # gold_sum+=gold_e
    return result

def plot(count=None):
    ys=[[]]*7
    datas=[[]]+[cost1(rarity) for rarity in range(1,7)]
    if not count:
        count = max([len(data) for data in datas])
    xs = {rarity:['']*count for rarity in range(1,7)}
    for rarity in range(1,7):
        y1 = []
        y2 = []
        for idx in range(0,count):
            if idx<len(datas[rarity]):
                e,level,exp_sum,gold_sum = datas[rarity][idx]
                text=''
                if level in [1]:
                    if e==0:
                        text=f'R{rarity}\n\n'
                    else:
                        text=f'E{e}\n\n'
                # elif level in range(10,len(datas[rarity]),10):
                elif level == gamedata['maxLevel'][rarity-1][e]:
                    text=f'\n{level}\n'
                else:
                    text='\n\n'
                xs[rarity][idx]=text
                y1.append(exp_sum)
                y2.append(gold_sum)
            else:
                xs[rarity][idx]='\n\n'
                
        ys[rarity]=y1,y2
    fig,ax = plt.subplots()
    fig1,ax1 = plt.subplots()
    ticks=0
    x=['']*count
    for rarity in range(1,7):
        for i,t in enumerate(xs[rarity]):
            # print(count,i,len(x_))
            x[i]+=t
    for rarity,y in enumerate(ys):
        if y:
            y1,y2=y
            ax.scatter(range(len(y1)),y1,s=1,color=anhrtags.colors.get(rarity,'black'))
            ax1.scatter(range(len(y2)),y2,s=1,color=anhrtags.colors.get(rarity,'black'))
    def config(ax,fig,title):
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels([str(item) for item in x])
        formatter = matplotlib.ticker.ScalarFormatter()
        formatter.set_scientific(False)
        ax.yaxis.set_major_formatter(formatter)
        ax.set_ylim(ymin=0)
        fig.set_size_inches(8, 5)
        ax.set_title(title)
        fig.tight_layout()
    config(ax,fig,'EXP')
    config(ax1,fig1,'LMD')
    plt.show()

if __name__ == "__main__":
    for level in [1,30,40,45,50,55,60,70,80,90]:
        for evolve in range(0,3):
            for rarity in range(1,7):
                print(*cost(rarity=rarity,level=level,evolve=evolve))
    plot()
    # plot(count=40+55+1)

'''
            EXP   LMD
E0 30 R1~6 9800 6043 max R12
E0 40 R3~6 16400 13947 R3 max
E0 45 R4~6 20200 19613 R4 max
E0 50 R5~6 24400 26719 R56 max
E1 01 R3 16400 23947
E1 01 R4 20200 34613
E1 01 R5 24400 46719
E1 01 R6 24400 56719
E1 30 R3 40992 38731
E1 30 R4 44792 49397
E1 30 R5 48992 61503
E1 30 R6 48992 71503
E1 40 R3 60782 54010
E1 40 R4 64582 64676
E1 40 R5 68782 76782
E1 40 R6 68782 86782
E1 45 R3 74582 65774
E1 45 R4 78382 76440
E1 45 R5 82582 88546
E1 45 R6 82582 98546
E1 50 R3 92782 82283
E1 50 R4 96582 92949
E1 50 R5 100782 105055
E1 50 R6 100782 115055
E1 55 R3 115400 104040 max R3
E1 55 R4 119200 114706
E1 55 R5 123400 126812
E1 55 R6 123400 136812
E1 60 R4 150200 146241 max
E1 60 R5 154400 158347
E1 60 R6 154400 168347
E1 70 R5 239400 251947 max
E1 70 R6 239400 261947
E1 80 R6 361400 409841 max
E2 01 R4 150200 206241
E2 01 R5 239400 371947
E2 01 R6 361400 589841
E2 30 R4 201211 235117
E2 30 R5 290411 400823
E2 30 R6 412411 618717
E2 40 R4 242936 264506
E2 40 R5 332136 430212
E2 40 R6 454136 648106
E2 45 R4 269911 285264
E2 45 R5 359111 450970
E2 45 R6 481111 668864
E2 50 R4 300961 310554
E2 50 R5 390161 476260
E2 50 R6 512161 694154
E2 55 R4 336486 341088
E2 55 R5 425686 506794
E2 55 R6 547686 724688
E2 60 R4 377086 377809
E2 60 R5 466286 543515
E2 60 R6 588286 761409
E2 70 R4 484000 482003 max R4
E2 70 R5 573200 647709
E2 70 R6 695200 865603
E2 80 R5 734400 819325 max R5
E2 80 R6 856400 1037219
E2 90 R6 1111400 1334796 max R6
'''

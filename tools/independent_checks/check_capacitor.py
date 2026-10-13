"""Capacitor: module cap use / cycle time skills, capacity and recharge
(v2026.10.13.11). Hand-typed pyfa skill rules (RULES) with values read from the
skill items. `python3 -I check_capacitor.py <golden_fit_id>` prints the
non-weapon drain of a golden fit; without an argument it runs the two
constructed fits (Executioner, Tengu)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
G = json.load(open(GOLDEN))
RULES=[
 ('cap','skill:Afterburner',SK('Afterburner','capNeedBonus')),
 ('cap','skill:Afterburner',SK('Fuel Conservation','capNeedBonus')),
 ('dur','skill:Afterburner',SK('Afterburner','durationBonus')),
 ('cap','skill:High Speed Maneuvering',SK('High Speed Maneuvering','capNeedBonus')),
 ('cap','skill:Propulsion Jamming',SK('Propulsion Jamming','capNeedBonus')),
 ('cap','skill:Weapon Disruption',SK('Weapon Disruption','capNeedBonus')),
 ('cap','skill:Sensor Linking',SK('Sensor Linking','capNeedBonus')),
 ('cap','skill:Target Painting',SK('Target Painting','capNeedBonus')),
 ('cap','group:ECM',SK('Electronic Warfare','capNeedBonus')),
 ('cap','skill:Capacitor Emission Systems',SK('Capacitor Emission Systems','capNeedBonus')),
 ('cap','skill:Shield Operation',SK('Shield Compensation','shieldBoostCapacitorBonus')),
 ('cap','skill:Capital Shield Operation',SK('Capital Shield Operation','shieldBoostCapacitorBonus')),
 ('dur','skill:Repair Systems',SK('Repair Systems','durationSkillBonus')),
 ('dur','skill:Capital Repair Systems',SK('Capital Repair Systems','durationSkillBonus')),
 ('cap','group:Armor Resistance Shift Hardener',SK('Resistance Phasing','capNeedBonus')),
 ('dur','group:Armor Resistance Shift Hardener',SK('Resistance Phasing','durationBonus')),
 ('cap','skill:Gunnery',SK('Controlled Bursts','capNeedBonus')),
 ('dur','skill:Energy Pulse Weapons',SK('Energy Pulse Weapons','durationBonus')),
 ('dur','skill:Micro Jump Drive Operation',SK('Micro Jump Drive Operation','durationBonus')),
]
def nm(t): return name(int(t))
def gname(t):
    g=groups[str(types[str(t)]['groupID'])]; n=g.get('groupName'); return n.get('en-us') if isinstance(n,dict) else n
def mult(tid,target):
    a={aname(x['attributeID']):x['value'] for x in td[str(tid)]['dogmaAttributes']}
    reqs={nm(int(a[k])) for k in ('requiredSkill1','requiredSkill2','requiredSkill3','requiredSkill4','requiredSkill5','requiredSkill6') if k in a}
    m=1
    for tg,f,v in RULES:
        if tg!=target: continue
        kind,val=f.split(':',1)
        if (kind=='skill' and val in reqs) or (kind=='group' and gname(tid)==val): m*=v
    return m,a
def drain(items, extra=lambda tid,tgt:1):
    tot=0; rows=[]
    for tid,q in items:
        m,a=mult(tid,'cap'); cap=a.get('capacitorNeed',0)
        if cap<=0: continue
        if a.get('speed'): continue  # weapons handled separately
        dur=a.get('duration',0)
        if not dur: continue
        md,_=mult(tid,'dur')
        d=q*cap*m*extra(tid,'cap')/(dur*md*extra(tid,'dur')/1000)
        rows.append((nm(tid),q,round(d,3))); tot+=d
    return tot,rows
if len(sys.argv) > 1:
    fid=sys.argv[1]
    f=G[fid]
    if 'tally' in f:
        items=[(int(t),d['totalQty']/d['lossCount']) for s in ('High slots','Mid slots','Low slots','Rigs') for t,d in (f['tally'].get(s) or {}).items()]
    else:
        import collections; c=collections.Counter()
        for it in f['killmail']['victim']['items']:
            fl=it['flag']
            if 11<=fl<=34 or 92<=fl<=99: c[it['item_type_id']]+=it.get('quantity_destroyed',0)+it.get('quantity_dropped',0)
        items=[(t,q) for t,q in c.items() if groups[str(types[str(t)]['groupID'])]['categoryID']==7]
    t,r=drain(items)
    for x in r: print('  ',x)
    print(fid,'non-weapon drain',round(t,3))
    sys.exit(0)
# ---- Executioner constructed (capacity 432 / peak 10.0 / drain 13.37 / armor rep 20.4)
ship=A('Executioner'); print('ship cap',ship['capacitorCapacity'],'recharge',ship['rechargeRate'],'shipBonus2AF',ship.get('shipBonus2AF'))
mwd=A('5MN Microwarpdrive II'); smc=A('Small Semiconductor Memory Cell II'); ccc=A('Small Capacitor Control Circuit II'); edl=A('Small Energy Discharge Elutriation II')
hs=A('Heat Sink II'); las=A('Small Focused Pulse Laser II'); std=A('Imperial Navy Standard S'); con=A('Conflagration S'); scr=A('Warp Scrambler II'); sar=A('Small Armor Repairer II')
cap=ship['capacitorCapacity']*1.25*mwd['capacitorCapacityMultiplier']*(1+smc['capacitorCapacityBonus']/100)
tau=ship['rechargeRate']/1000*0.75*(1+ccc['capRechargeBonus']/100)
print('capacity',cap,'tau',tau,'peak',2.5*cap/tau)
# lasers: Controlled Bursts x Executioner shipBonus2AF(x5) x Elutriation rig x charge
cb=SK('Controlled Bursts','capNeedBonus')
hull=1+ship['shipBonus2AF']*5/100
rig=1+edl['capNeedBonus']/100
charge=( (1+std['capNeedBonus']/100)*2 + (1+con.get('capNeedBonus',0)/100) )/3
rof=las['speed']/1000*SK('Gunnery','turretSpeeBonus' if False else 'turretSpeeBonus') if False else None
gun=1+[v for k,v in A('Gunnery').items() if k=='turretSpeeBonus'][0]*5/100
rf=1+[v for k,v in A('Rapid Firing').items() if k=='rofBonus'][0]*5/100
cyc=las['speed']/1000*gun*rf*hs['speedMultiplier']
lasers=3*las['capacitorNeed']*cb*hull*rig*charge/cyc
print('laser capNeed',las['capacitorNeed'],'cb',cb,'hull',hull,'rig',rig,'chargeAvg',charge,'cycle',cyc,'gun',gun,'rf',rf,'hs',hs['speedMultiplier'],'->',lasers)
mwdd=mwd['capacitorNeed']*SK('High Speed Maneuvering','capNeedBonus')/(mwd['duration']/1000)
scrd=scr['capacitorNeed']*SK('Propulsion Jamming','capNeedBonus')*b(ship['eliteBonusInterceptorRole'])/(scr['duration']/1000)  # shipCapPropulsionJamming (effect 3495): T1 tackle-frigate role -80%
sard=sar['capacitorNeed']/(sar['duration']/1000*SK('Repair Systems','durationSkillBonus'))
print('mwd',mwdd,'scram',scrd,'rep',sard,'TOTAL',lasers+mwdd+scrd+sard)
print('armor rep HP/s',sar['armorDamageAmount']/(sar['duration']/1000*SK('Repair Systems','durationSkillBonus')))
# ---- Tengu constructed (capacity 1812.5 / peak 28.3 / drain 39.9)
ship=A('Tengu'); core=A('Tengu Core - Augmented Graviton Reactor'); flux=A('Capacitor Flux Coil II')
lsb=A('Large Shield Booster II'); ab=A('10MN Afterburner II'); web=A('Stasis Webifier II')
cds=A('Medium Core Defense Capacitor Safeguard II'); cos=A('Medium Core Defense Operational Solidifier I')
print('ship cap',ship['capacitorCapacity'],'rech',ship['rechargeRate'],'core keys',{k:v for k,v in core.items() if 'apacitor' in k or 'subsystemBonusCaldariCore' in k})
capAdd=core.get('capacitorCapacity',0)
cap=(ship['capacitorCapacity']+capAdd)*1.25*(1+core['subsystemBonusCaldariCore']*5/100)*flux['capacitorCapacityMultiplier']
tau=ship['rechargeRate']/1000*0.75*flux['capacitorRechargeRateMultiplier']
print('capacity',cap,'tau',tau,'peak',2.5*cap/tau)
lsbCap=lsb['capacitorNeed']*SK('Shield Compensation','shieldBoostCapacitorBonus')*(1+cds['shieldBoostCapacitorBonus']/100)
lsbDur=lsb['duration']/1000*(1+cos['durationSkillBonus']/100)
abd=ab['capacitorNeed']*SK('Afterburner','capNeedBonus')*SK('Fuel Conservation','capNeedBonus')/(ab['duration']/1000*SK('Afterburner','durationBonus'))
webd=web['capacitorNeed']*SK('Propulsion Jamming','capNeedBonus')/(web['duration']/1000)
print('lsb',lsbCap/lsbDur,'ab',abd,'web',webd,'TOTAL',lsbCap/lsbDur+abd+webd)
print('booster HP/s raw (pre amp/skills)',lsb['shieldBonus']/lsbDur)

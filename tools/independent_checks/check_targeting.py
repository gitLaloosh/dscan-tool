"""Targeting range / scan resolution / sensor strength (v2026.10.13.13). Hand-typed
pyfa rules: skills (Long Range Targeting, Signature Analysis, racial Sensor
Compensation) x pen[default group: Sensor Booster (script-scaled), Signal Amp,
rigs, WCS/Nullifier] x pen[postMul: WCS/Nullifier/cloak scan-res multipliers]."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_common import *
LRT = SK('Long Range Targeting', 'maxTargetRangeBonus'); SA = SK('Signature Analysis', 'scanResolutionBonus'); SC = SK('Gravimetric Sensor Compensation', 'sensorStrengthBonus')
def strength(ship):
    ks={'radar':'scanRadarStrength','ladar':'scanLadarStrength','magnetometric':'scanMagnetometricStrength','gravimetric':'scanGravimetricStrength'}
    k=max(ks,key=lambda k:ship.get(ks[k],0)); return k,ship[ks[k]]
# ---- A: Caracal
c=A('Caracal'); sb=A('Sensor Booster II'); sa=A('Signal Amplifier II'); wcs=A('Warp Core Stabilizer II')
trs=A('Targeting Range Script'); srs=A('Scan Resolution Script'); ifp=A('Medium Ionic Field Projector II'); tss=A('Medium Targeting System Subcontroller II')
sbR=lambda s: sb['maxTargetRangeBonus']*(1+(s['maxTargetRangeBonusBonus'] if s else 0)/100)
sbS=lambda s: sb['scanResolutionBonus']*(1+(s['scanResolutionBonusBonus'] if s else 0)/100)
sbG=lambda s: sb['scanGravimetricStrengthPercent']*(1+(s['sensorStrengthBonusBonus'] if s else 0)/100)
rng=[1+sbR(trs)/100,1+sbR(srs)/100,1+sbR(None)/100,1+sa['maxTargetRangeBonus']/100,1+ifp['maxTargetRangeBonus']/100,1+wcs['maxTargetRangeBonus']/100]
scn_def=[1+sbS(trs)/100,1+sbS(srs)/100,1+sbS(None)/100,1+sa['scanResolutionBonus']/100,1+tss['scanResolutionBonus']/100]
scn_post=[wcs['scanResolutionMultiplier']]
k,base=strength(c)
strg=[1+sbG(trs)/100,1+sbG(srs)/100,1+sbG(None)/100,1+sa['scanGravimetricStrengthPercent']/100]
print('Caracal constructed (110530 / 486.6 / 40.3): range', c['maxTargetRange']*LRT*pen(rng), 'scanres', c['scanResolution']*SA*pen(scn_def)*pen(scn_post), k, base*SC*pen(strg))
print('   range mults',[round(x,3) for x in rng],'scan',[round(x,3) for x in scn_def])
# ---- B: Crow + nullifier + SB
cr=A('Crow'); nul=A('Interdiction Nullifier II')
nr=nul['maxTargetRangeBonus']*(1+cr['shipBonusRole1']/100); ns=nul['scanResolutionMultiplier']*(1+cr['shipBonusRole3']/100)
k,base=strength(cr)
print('Crow constructed (47531 / 1257.8 / 21.3): range', cr['maxTargetRange']*LRT*pen([1+sb['maxTargetRangeBonus']/100,1+nr/100]), 'scanres', cr['scanResolution']*SA*pen([1+sb['scanResolutionBonus']/100])*pen([ns]), k, base*SC*pen([1+sb['scanGravimetricStrengthPercent']/100]),'nullifier',nr,ns)
# ---- C: Tengu
t=A('Tengu'); core=A('Tengu Core - Electronic Efficiency Gate'); prop=A('Tengu Propulsion - Interdiction Nullifier'); cl=A('Improved Cloaking Device II')
add=prop.get('maxTargetRange',0)
k,base=strength(t)
print('Tengu constructed (85938 / 157.5 / 42.0): range',(t['maxTargetRange']+add)*LRT*(1+core['subsystemBonusCaldariCore2']*5/100),'scanres',t['scanResolution']*SA*pen([cl['scanResolutionMultiplier']]),k,base*SC*(1+core['subsystemBonusCaldariCore']*5/100),'add',add,'core',core['subsystemBonusCaldariCore2'],core['subsystemBonusCaldariCore'])

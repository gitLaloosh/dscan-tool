import fs from 'fs'; import vm from 'vm';
const html = fs.readFileSync(process.argv[2],'utf8');
const code = html.match(/<script>([\s\S]*)<\/script>/)[1];
function fakeEl(){ return { addEventListener(){}, get style(){return {};}, querySelectorAll(){return [];}, appendChild(){}, get innerHTML(){return '';}, set innerHTML(v){} }; }
const sb={fetch:async()=>({ok:false}),document:{getElementById(){return fakeEl();},createElement(){return fakeEl();}},console,Promise,Map,Set,Infinity,Math,JSON,Object,Array,Number,String};
vm.createContext(sb);
const names=['SKILL_MODULE_ATTR_MODS_AT_V','MODULE_ATTR_MOD_EFFECTS','SHIP_CAP_ATTR_EFFECTS','SHIP_SENSOR_ATTR_EFFECTS','SHIP_HP_ATTR_EFFECTS','SIEGE_FAMILY_LOCAL_REP_EFFECTS','SIEGE_FAMILY_REMOTE_REP_EFFECTS','SHIP_SHIELD_RECHARGE_EFFECTS','WEAPON_RANGE_MOD_EFFECTS','SHIP_SIG_HULL_BONUS_EFFECTS','MWD_SIG_BONUS_SHIP_EFFECTS','MWD_SIG_BONUS_SUBSYSTEM_EFFECTS','SENSOR_STRENGTH_PERCENT_EFFECT_IDS'];
vm.runInContext(code+`\n;globalThis.__T={${names.join(',')}};`, sb);
process.stdout.write(JSON.stringify(sb.__T));


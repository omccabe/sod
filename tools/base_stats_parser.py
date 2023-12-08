#!/usr/bin/python

import csv

# Generates go/ts baes stats files from assets/db_inputs/basestats

BASE_DIR = ""

DIR_PATH = "assets/db_inputs/basestats/"
OUTPUT_PATH = "sim/core/"

BASE_MP = "octbasempbyclass.txt"
MELEE_CRIT = "chancetomeleecrit.txt"
MELEE_CRIT_BASE = "chancetomeleecritbase.txt"
SPELL_CRIT = "chancetospellcrit.txt"
SPELL_CRIT_BASE = "chancetospellcritbase.txt"
COMBAT_RATINGS = "combatratings.txt"
RATING_SCALAR = "octclasscombatratingscalar.txt"

MAX_LEVEL = 60
LEVELS = [25,40,50,60]

Offs = {
    "Warrior": 0,
    "Paladin": 1,
    "Hunter": 2,
    "Rogue": 3,
    "Priest": 4,
    "Shaman": 6,
    "Mage": 7,
    "Warlock": 8,
    "Monk": 9,
    "Druid": 10,
}

#Warrior	Paladin	Hunter	Rogue	Priest	Shaman	Mage	Warlock	Monk	Druid
def GenIndexedDb(file : str):
    db = {}
    with open(file) as tsv:
        first = True
        for line in csv.reader(tsv, delimiter="\t"):
            if first:
                first = False
                continue
            db[line[0]] = line[1:]
    return db

def GenRowIndexedDb(file : str):
    db = {}
    with open(file) as tsv:
        first = True
        for col in zip(*[line for line in csv.reader(tsv, delimiter='\t')]):
            if first:
                first = False
                continue
            db[col[0]] = list(col[1:])
    return db

class ClassStats:
    BaseMp : dict
    MCrit : dict
    SCrit : dict
    MCritBase : dict
    SCritBase : dict
    CombatRatings : dict

def GenExtraStatsGoFile(cs: ClassStats):
    header = '''
package core

// **************************************
// AUTO GENERATED BY BASE_STATS_PARSER.PY
// **************************************

import (
	"github.com/wowsims/sod/sim/core/proto"
	"github.com/wowsims/sod/sim/core/stats"
)

'''
    output = header
    output += f"const ExpertisePerQuarterPercentReduction = {cs.CombatRatings['weapon skill'][MAX_LEVEL-1]}\n"
    output += f"const HasteRatingPerHastePercent = {cs.CombatRatings['haste melee'][MAX_LEVEL-1]}\n"
    output += f"// Crit/Hit ratings are straight percentage values in classic\n"
    output += f"const CritRatingPerCritChance = 1\n"
    output += f"const SpellCritRatingPerCritChance = 1\n"
    output += f"const MeleeHitRatingPerHitChance = 1\n"
    output += f"const SpellHitRatingPerHitChance = 1\n"
    output += f"const DefenseRatingPerDefense = {cs.CombatRatings['defense skill'][MAX_LEVEL-1]}\n"
    output += f"const DodgeRatingPerDodgeChance = {cs.CombatRatings['dodge'][MAX_LEVEL-1]}\n"
    output += f"const ParryRatingPerParryChance = {cs.CombatRatings['parry'][MAX_LEVEL-1]}\n"
    output += f"const BlockRatingPerBlockChance = {cs.CombatRatings['block'][MAX_LEVEL-1]}\n"
    output += f"const ResilienceRatingPerCritReductionChance = {cs.CombatRatings['crit taken melee'][MAX_LEVEL-1]}\n"

    output += '''var CritPerAgiAtLevel = map[proto.Class]map[int]float64{
  proto.Class_ClassUnknown: {25: 0.0, 45: 0.0, 50: 0.0, 60: 0.0},'''
    for c in ["Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Shaman", "Mage", "Warlock", "Druid"]:
        cName = c.split()
        if len(cName) > 1:
            cName[1] = cName[1].lower() 
        cName = ''.join(cName)
        levelOutput = f"\n  proto.Class_Class{cName}: {{"
        for level in LEVELS:
            mc = float(cs.MCrit[str(level)][Offs[c]])*100
            levelOutput += f"{level}:{mc:.4f}, "
        output += levelOutput + "},"
    output += "\n}\n"

    output += '''var ExtraClassBaseStats = map[proto.Class]map[int]stats.Stats{
proto.Class_ClassUnknown: {},'''
    for c in ["Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Shaman", "Mage", "Warlock", "Druid"]:
        cName = c.split()
        if len(cName) > 1:
            cName[1] = cName[1].lower() 
        cName = ''.join(cName)
        output += f"\n  proto.Class_Class{cName}: {{"
        for level in LEVELS:
            output += f"\n    {level}: {{"
            # mp = float(cs.BaseMp[str(level)][Offs[c]])
            scb = float(cs.SCritBase["1"][Offs[c]])*100
            mcb = float(cs.MCritBase["1"][Offs[c]])*100
            # output += f"\n      stats.Mana: {mp:.4f},"
            output += f"\n      stats.SpellCrit: {scb:.4f}*CritRatingPerCritChance,"
            output += f"\n      stats.MeleeCrit: {mcb:.4f}*CritRatingPerCritChance,"
            output += "\n    },"
        output += "\n  },"
    output += "\n}\n"
    return output
    

if __name__ == "__main__":
    args = ClassStats()
    args.BaseMp = GenIndexedDb(BASE_DIR + DIR_PATH + BASE_MP)
    args.MCrit = GenIndexedDb(BASE_DIR + DIR_PATH + MELEE_CRIT)
    args.SCrit = GenIndexedDb(BASE_DIR + DIR_PATH + SPELL_CRIT)
    args.MCritBase = GenIndexedDb(BASE_DIR + DIR_PATH + MELEE_CRIT_BASE)
    args.SCritBase = GenIndexedDb(BASE_DIR + DIR_PATH + SPELL_CRIT_BASE)
    args.CombatRatings = GenRowIndexedDb(BASE_DIR + DIR_PATH + COMBAT_RATINGS)

    output = GenExtraStatsGoFile(args)
    fname = BASE_DIR + OUTPUT_PATH + "base_stats_auto_gen.go"
    print(f"Writing stats to: {fname}")
    f = open(fname, "w")
    f.write(output)
    f.close()

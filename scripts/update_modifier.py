# NEED FIX FOR V2 TO BE CALLED BEFORE TRANSLATION SO IT PROPAGATES TO ALL FILES

#!/usr/bin/python3

import sys
import json
import collections
from collections import OrderedDict
import os.path
import ast
import itertools

'''
This script may be ran anywhere within the gamedatabase.
./updateModifiers.py <fileName or all>
./updateModifiers.py all
./updateModifiers.py luna.json
'''

# Name of file from command prompt, "all" for all files.
#print(str(sys.argv))
fileName = sys.argv[1]

writeOutput = True
printOutput = False
verbose     = False

#################################
# Special Cases, Damage modifiers
#################################
def specialVal(info, item, rnd, constVal, constSb):
  return None
def specialSimp(info, item, rnd, constVal, constSb):
  if info['fileName'] == 'cidd.json' and \
     str(item['multiplier']) == ' * hero_atk' and \
     info['skillName'] == 'Relentless Strike':
    cidd = calcMod(item['value'],constVal,rnd)
    cidd = cidd.split('[')
    cidd1 = cidd[2].split(',')[0]
    cidd2 = cidd[3].split(', ')[1].split(']')[0]
    #ret = '(S2Active['+cidd1+', '+cidd2+'] * hero_atk)'
    ret = '(['+cidd1+', '+cidd2+'] * hero_atk)'
    return ret
  return None
def specialSb(info, item, rnd, constVal, constSb):
  return None
def specialSimpSb(info, item, rnd, constVal, constSb):
  if info['fileName'] == 'cidd.json' and \
     str(item['multiplier']) == ' * hero_atk' and \
     info['skillName'] == 'Relentless Strike':
    cidd = calcMod(item['soulburn'],constVal,rnd)
    cidd = cidd.split('[')
    cidd1 = cidd[2].split(',')[0]
    cidd2 = cidd[3].split(', ')[1].split(']')[0]
    #ret = '(S2Active['+cidd1+', '+cidd2+'] * hero_atk)'
    ret = '(['+cidd1+', '+cidd2+'] * hero_atk)'
    return ret
  return None


#################################
# Helper functions
#################################

def calcMod(val1, val2, rnd):
  name1 = None
  name2 = None
  if str(val1)[0].isdigit():
    values1 = val1
  else:
    findStart = str(val1).split('[')
    name1 = findStart[0]
    values1 = ast.literal_eval('['+findStart[1])
  if str(val2)[0].isdigit():
    values2 = val2
  else:
    findStart = str(val2).split('[')
    name2 = findStart[0]
    values2 = ast.literal_eval('['+findStart[1])

  if name1 is None:
    if name2 is None:
      newVal = round(val1 * val2, rnd)
    else:
      newVal = '['
      #newVal = name2+'['
      count2 = 0
      for item in values2:
        if count2 is not 0:
          newVal += ', '
        newVal += str(round(val1 * item, rnd))
        count2 += 1
      newVal += ']'
  else:
    if name2 is None:
      newVal = '['
      #newVal = name1+'['
      count1 = 0
      for item in values1:
        if count1 is not 0:
          newVal += ', '
        newVal += str(round(item * val2, rnd))
        count1 += 1
      newVal += ']'
    else:
      newVal = name1+'['
      count1 = 0
      for item1 in values1:
        if count1 is not 0:
          newVal += ', '
        newVal += '['
        #newVal += name2+'['
        count2 = 0
        for item2 in values2:
          if count2 is not 0:
            newVal += ', '
          newVal += str(round(item1 * item2, rnd))
          count2 += 1
        newVal += ']'
        count1 += 1
      newVal += ']'

  return newVal



#################################
# Update damage modifers
#################################

def constructModString(info, cur, group, sep, rnd, constVal, constSb):
  descr  = cur[0]
  value  = cur[1]
  simp   = cur[2]
  sb     = cur[3]
  simpSb = cur[4]
  count = 0
  for item in group:
    if count is not 0:
      descr += sep; value += sep; simp += sep; sb += sep; simpSb += sep
    descr+=item['description']
    start = ''
    end = ''
    if item['multiplier'] is not None:
      start ='('
      end = str(item['multiplier'])+')'
    if specialVal(info, item, rnd, constVal, constSb) is not None:
      value += specialVal(info, item, rnd, constVal, constSb)
    else:
      value+=start+str(item['value'])+end
    if specialSimp(info, item, rnd, constVal, constSb) is not None:
      simp += specialSimp(info, item, rnd, constVal, constSb)
    else:
      simp+=start+str(calcMod(item['value'],constVal,rnd))+end
    if specialSb(info, item, rnd, constVal, constSb) is not None:
      sb += specialSb(info, item, rnd, constVal, constSb)
    else:
      sb+=start+str(item['soulburn'])+end
    if specialSimpSb(info, item, rnd, constVal, constSb) is not None:
      simpSb += specialSimpSb(info, item, rnd, constVal, constSb)
    else:
      simpSb+=start+str(calcMod(item['soulburn'],constSb,rnd))+end
    count+=1
  return descr,value,simp,sb,simpSb

def updateDmgMod(fileName, dictVar):
  skillJson = dictVar['jsonData']
  modList = []
  for mod in skillJson["damageModifiers"]:
    tmp = {}
    for item in mod:
      tmp[item] = mod[item]
    modList.append(tmp)

  info = {}
  addGroup = []
  multiGroup = []
  constGroup = []
  flatGroup = []
  otherGroup = []

  info['fileName'] = str(fileName)
  info['skillName'] = str(skillJson['name'])

  for mod in modList:
    groupSwitcher = {
      'pow': [constGroup, 'pow!', None, True],
      'atk_rate': [addGroup, 'atk_rate', 'hero_atk', False],
      'ally_atk_rate': [addGroup, 'ally_atk_rate', 'ally_atk', False],
      'def_rate': [addGroup, 'def_rate', 'hero_def', False],
      'hp_rate': [addGroup, 'hp_rate', 'hero_hp', False],
      'spd_rate': [multiGroup, 'spd_rate', 'hero_spd', False],
      'skill_dmg_rate': [multiGroup, 'skill_dmg_rate', 'hero_special_count', \
                         False],
      'self_hp_current_rate': [multiGroup, 'self_hp_current_rate', \
                               'hero_hp_remaining_percent', False],
      'target_hp_missing_rate': [multiGroup, 'target_hp_missing_rate', \
                                 'target_hp_lost_percent', False],
      'self_hp_missing_rate': [multiGroup, 'self_hp_missing_rate', \
                               'hero_hp_lost_percent', False],
      'skill_dmg_list': [multiGroup, 'skill_dmg_list', None, True],
      'target_hp_rate': [addGroup, 'target_hp_rate', 'target_hp', False],
      'self_hp_missing_value': [flatGroup, 'self_hp_missing_value', \
                                'hero_hp_lost_value', False],
      'crit_dmg_rate':[otherGroup, 'crit_dmg_rate', None, False],
      'target_spd_rate': [multiGroup, 'target_spd_rate', 'target_spd', False],
      'target_buff_rate': [multiGroup, 'target_buff_rate', \
                           'target_buffs', True],
      'target_debuff_rate': [multiGroup, 'target_debuff_rate', \
                             'target_debuffs', True],
      'targets_rate': [multiGroup, 'targets_rate', \
                       'num_targets', True],
      }

    group = groupSwitcher.get(mod['name'])
    if group is None:
      print('Failed on type '+mod['name'])
      print(str(dictVar))
      quit()
    if group[2] is not None:
      modDescr = '('+group[1]+' * '+group[2]+')'
    else:
      modDescr = group[1]
    if mod['value'] == 0 and mod['soulburn'] == 0:
      continue
    group[2] = ' * '+str(group[2])
    if str(mod['value']).startswith('['):
      mod['value'] = str(mod['value'])
      #mod['value'] = str(group[1])+str(mod['value'])
      if group[3] == True:
        group[2] = ''
        modDescr = group[1]
    if str(mod['soulburn']).startswith('['):
      mod['soulburn'] = str(mod['soulburn'])
      #mod['soulburn'] = str(group[1])+str(mod['soulburn'])
    group[0].append({'value':mod['value'], 'soulburn':mod['soulburn'],
                     'multiplier':group[2], 'description':modDescr})
  constGroup.append({'value':1.871, 'soulburn':1.871,
                     'multiplier':'', 'description':'constant'})
  descr  = ""
  value  = ""
  simp   = ""
  sb     = ""
  simpSb = ""

  simpValCalc = 1
  simpSbCalc = 1
  if len(constGroup):
    for item in constGroup:
      simpValCalc = calcMod(simpValCalc, item['value'], 6)
      simpSbCalc = calcMod(simpSbCalc, item['soulburn'], 6)

  if len(addGroup):
    s = '('
    descr +=s; value +=s; simp +=s; sb +=s; simpSb +=s
    descr,value,simp,sb,simpSb = constructModString( \
                              info, [descr,value,simp,sb,simpSb], \
                              addGroup, ' + ', 4, simpValCalc, simpSbCalc)
    descr += ')'; value += ')'; simp += ')'; sb += ')'; simpSb += ')'

  if len(multiGroup):
    s = '(1 + ('
    if descr != "":
      s = ' * '+s
    descr +=s; value +=s; simp +=s; sb +=s; simpSb +=s
    descr,value,simp,sb,simpSb = constructModString( \
                              info, [descr,value,simp,sb,simpSb], \
                              multiGroup, ' + ', 6, 1, 1)
    descr += '))'; value += '))'; simp += '))'; sb += '))'; simpSb += '))'

  if len(constGroup) and descr != "":
    s = ' * '
    sep = ' * '
    descr +=s; value +=s; sb +=s;
    count = 0
    for item in constGroup:
      if count is not 0:
        descr += sep; value += sep; sb += sep;
      #if str(val).startswith('[') is True:
      descr+=item['description']
      value+=str(item['value'])
      #if str(item['value']).startswith('[') is True:
      #  simp+=str(item['description'])+str(item['value'])
      sb+=str(item['soulburn'])
      #if str(item['value']).startswith('[') is True:
      #  simpSb+=str(item['value'])
      count+=1

  #print('descr : '+descr)
  #print('value : '+value)
  #print('simp  : '+simp)
  #print('sb    : '+sb)
  #print('simpSb: '+simpSb)

  if 'simpleDmgMod' in skillJson:
    if skillJson['simpleDmgMod']['description'] != descr or \
       skillJson['simpleDmgMod']['value'] != value or \
       skillJson['simpleDmgMod']['simplified'] != simp or \
       skillJson['simpleDmgMod']['soulburn'] != sb or \
       skillJson['simpleDmgMod']['simplifiedSoulburn'] != simpSb:
      print('Changes in '+fileName)

  skillJson['simpleDmgMod'] = OrderedDict()
  skillJson['simpleDmgMod']['description'] = descr
  skillJson['simpleDmgMod']['value'] = value
  skillJson['simpleDmgMod']['simplified'] = simp
  skillJson['simpleDmgMod']['soulburn'] = sb
  skillJson['simpleDmgMod']['simplifiedSoulburn'] = simpSb

#################################
# Search Dictionary functions
#################################

# Create a list of all variables that match searchVar
def findDictWithVar(jsonData, searchVar, path):
    dictList = []
    index = 0
    for var in jsonData:
        if var == searchVar:
            dictList = dictList+[{'jsonData':jsonData, 'path':path}]
        elif isinstance(var, collections.Mapping):
            ret = findDictWithVar(var, searchVar, path+['item:'+str(index)])
            if ret != []:
                dictList = dictList+ret
        elif isinstance(jsonData[var], collections.Mapping):
            ret = findDictWithVar(jsonData[var], searchVar, path+['dict:'+var])
            if ret != []:
                dictList = dictList+ret
        elif isinstance(jsonData[var], list):
            if len(jsonData[var]) == 0:
                continue;
            if isinstance(jsonData[var][0], collections.Mapping) == False:
                continue;
            ret = findDictWithVar(jsonData[var], searchVar, path+['list:'+var])
            if ret != []:
                dictList = dictList+ret
        index = index + 1
    return dictList

#################################
# Path Helper functions
#################################

# Convert path to type, value
def convertPath(pathStr):
    pathType = ''
    pathValue = ''
    if pathStr.startswith('dict:'):
        pathType = 'dict'
        pathValue = pathStr[5:]
    elif pathStr.startswith('item:'):
        pathType = 'item'
        pathValue = int(pathStr[5:])
    elif pathStr.startswith('list:'):
        pathType = 'list'
        pathValue = pathStr[5:]
    else:
        pathType = ''
        pathValue = pathStr
    return pathType,pathValue

# Check if paths match, * values means all match
def matchPath(pathA, pathB):
    if pathA == pathB:
        return True
    pathTypeA,pathValueA = convertPath(pathA)
    pathTypeB,pathValueB = convertPath(pathB)
    if pathTypeA == pathTypeB and (pathValueA == '*' or pathValueB == '*'):
        return True
    if pathTypeA == '' and pathValueA == '*':
        return True
    if pathTypeB == '' and pathValueB == '*':
        return True
    return False

#################################
# Main helper functions
#################################

# Write json into file
def writeJson(outputFile, jsonData):
    with open(outputFile, 'w') as outfile:
        json.dump(jsonData, outfile, indent=4, separators=(',', ': '), ensure_ascii=False)
        outfile.write("\n")

# Print json to screen
def printJson(jsonData):
    print(json.dumps(jsonData, indent=4, separators=(',', ': '), ensure_ascii=False))

#################################
# Main function
#################################
def main(fileName, command, searchVar, newVar, path):
    with open(fileName, 'r') as infile:
        if verbose:
            print(fileName)
        inJson = json.load(infile, object_pairs_hook=OrderedDict)
        dictList = findDictWithVar(inJson, searchVar, [])
        if len(dictList) <= 0:
            print(searchVar+' was not found in '+fileName+'.')
            return
        for dictVar in dictList:
            #print('looking at path '+str(dictVar['path']))
            # If path variable is set, only process when path matches
            if path is not None and path != dictVar['path'] and path != ['*']:
                if len(path) > len(dictVar['path']):
                    continue
                match = True
                for inHop,searchHop in zip(path,dictVar['path']):
                    if matchPath(inHop, searchHop) == False:
                        match = False
                if len(path) != len(dictVar['path']):
                    if len(path) == 0 or inHop != '*':
                        match = False
                if match == False:
                    continue
            # Update damage modifiers
            if command == 'damage':
                updateDmgMod(fileName, dictVar)
        if writeOutput:
            writeJson(fileName, inJson)
        if printOutput:
            printJson(inJson)


#################################
# Pre-Main code - Calls main
#################################

# Create decoder, so we can decode strings to OrderedDict.
decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)

# Get list of all json files
def getAllJsonFiles(dir):
    allFiles = os.listdir(dir)
    jsonFiles = []
    for fileName in allFiles:
        if fileName.endswith('.json'):
            if 'TEMPLATE'.lower() in fileName.lower():
                continue
            jsonFiles = jsonFiles + [fileName]
    return jsonFiles

def findHeroDirectory(curPath):
    curList = curPath.split('/')
    if len(curList) <= 1:
      quit()
    if curList[-1] == 'hero':
        return ''
    if curList[-1] == 'src':
        return 'hero'
    lsList = os.listdir(curPath)
    if 'hero' in lsList:
        return 'hero'
    if 'src' in lsList:
        return 'src/hero'
    return '../'+findHeroDirectory('/'.join(curList[0:-1]))

dirToHero = ''
dirToHero = findHeroDirectory(os.getcwd())
if dirToHero != '':
    os.chdir(dirToHero)
if fileName == 'all':
    fileList = getAllJsonFiles('.')
else:
    if os.path.isfile(fileName) == False:
        print(fileName+' is not a file.')
        quit()
    fileList = [fileName]

# Walk through all files and act
for fileName in fileList:
    command = 'damage'
    searchVar = 'damageModifiers'
    newVar = ''
    path = ast.literal_eval("['list:skills', '*']")
    main(fileName, command, searchVar, newVar, path)

#!/usr/bin/python3

SCRIPT_VERSION = 1.0

import json
import glob
import re
import os
import subprocess
import shutil
import copy
import subprocess
import sys

# =================================
# Install benedict if not available
try:
    from benedict import benedict
except ImportError:
    try:
        subprocess.call([sys.executable, "-m", "pip", "install", 'python-benedict'])
    except:
        pass
    try:
        subprocess.call([sys.executable, "-m", "pip3", "install", 'python-benedict'])
    except:
        pass
finally:
    from benedict import benedict

# =================================
# parse arguments
import argparse

# initiate the parser
parser = argparse.ArgumentParser(description = 'Script to parse SRC files into translated collections to be imported to database.')
parser.add_argument("-V", "--version", help="show script version", action="store_true")
parser.add_argument("-B", "--buildonly", help="buildonly, without attempting to call mongoimport", action="store_true")

args = parser.parse_args()

if args.version:
    print("{0} (EpicSevenDB/gamedatabase v2.x)".format(SCRIPT_VERSION))
    exit(0)

# =================================

def getLangKey(langFilePath):
    lang_regex = re.compile(r"(.*\/)(text\_)(.*)(\.json)", re.IGNORECASE)
    return lang_regex.sub(r"\3", langFilePath)

def mkdir(folderName):
    if not os.path.exists(BUILD_FOLDER + '/' + folderName):
        os.makedirs(BUILD_FOLDER + '/' + folderName)

def printline():
    print('=================================')

def saveFile( filename, path, contents):
    filepath = path + "/{0}.json".format(filename)
    with open(filepath, 'w') as f:
        json.dump(contents, f)

def get_translation(customLangData):
    def translate(translationKey):
        translation = ''

        if not translationKey:
            return 'MISSING_TRANSLATION_KEY'

        if not translation and customLangData:
            try:
                translation = customLangData[translationKey]
            except:
                pass

        if not translation:
            try:
                translation = text_en[translationKey]
            except:
                pass

        if not translation:
            return 'MISSING_TRANSLATION_VALUE('+translationKey+')'

        return translation
    return translate

def get_folder_files(srcFolder):
    return sorted(glob.glob("{0}/*.json".format(srcFolder)))

def translate_folder(srcFolder):
    srcFolderFilesRegex = re.compile(r"(.*\/src\/)(.*)", re.IGNORECASE)
    foldername = srcFolderFilesRegex.sub(r"\2", srcFolder)
    fileParser = globals()['{0}_parser'.format(foldername)]
    print(fileParser)
    printline()
    print(foldername)
    printline()
    folder_files = get_folder_files(srcFolder)

    for file in folder_files:
        srcFolderFilesRegex = re.compile(r"(.*\/)(.*)(\.json)", re.IGNORECASE)
        filename = srcFolderFilesRegex.sub(r"\2", file)
        print('* Translating '+filename)
        file_data = json.load(open(file));
        file_keys = file_data.keys()
        if "_id" not in file_keys:
            file_data["_id"] = filename

        for lang in lang_files:
        # lang = '/Users/RaphaelDDL/Workspace/epicsevendb-gamedatabase/src/text/text_en.json'
            currentLanguageData = json.load(open(lang))
            get_translation_specific = get_translation(currentLanguageData)
            lang_key = getLangKey(lang)
            lang_folder = foldername+'-'+lang_key
            mkdir(lang_folder)
            print('-- ' + lang_key)
            saveFile(filename, BUILD_FOLDER+'/'+lang_folder, fileParser(filename,benedict(copy.deepcopy(file_data)),get_translation_specific))

# =================================

def mount_collection_array(folderName):
    folder_files = get_folder_files(BUILD_FOLDER+"/"+folderName)
    collection = []

    for file in folder_files:
        data = json.load(open(file))
        collection.append(data)

    saveFile(folderName, buildCollectionsFolder, collection)
    print('Collection {0} saved'.format(folderName))

def update_mongo(collection, filePath):
    printline()
    print("** Updating MONGODB => collection \"{0}\" with file {1} **\n".format(collection, filePath))
    subprocess.call(mongoimport_command.format(collection, filePath), shell=True)
    print("\n** MONGODB => collection \"{0}\" updated **\n\n".format(collection))

# =================================

def artifact_parser(filename,data,get_translation_specific):
    data["name"] = get_translation_specific(data["name"])
    data["description"] = get_translation_specific(data["description"])
    data["skill.description"] = get_translation_specific(data["skill.description"])
    return data

def materials_parser(filename,data,get_translation_specific):
    data["name"] = get_translation_specific(data["name"])
    data["description"] = get_translation_specific(data["description"])
    data["category"] = get_translation_specific(data["category"])
    return data

def hero_parser(filename,data,get_translation_specific):
    data["name"] = get_translation_specific(data["name"])
    data["description"] = get_translation_specific(data["description"])
    data["story"] = get_translation_specific(data["story"])
    data["get_line"] = get_translation_specific(data["get_line"])

    if data["specialty"]:
        data["specialty.name"] = get_translation_specific(data["specialty.name"])
        data["specialty.description"] = get_translation_specific(data["specialty.description"])

        if data["specialty.type"]:
            data["specialty.type.name"] = get_translation_specific(data["specialty.type.name"])
            data["specialty.type.description"] = get_translation_specific(data["specialty.type.description"])

    if data["camping"]:
        try:
            for i1 in range(len(data["camping.personalities"])):
                data["camping.personalities"][i1] = get_translation_specific(data["camping.personalities"][i1])
        except:
            pass

        try:
            for i2 in range(len(data["camping.topics"])):
                data["camping.topics"][i2] = get_translation_specific(data["camping.topics"][i2])
        except:
            pass

        try:
            camp_val_keys = data["camping.values"].keys()
            camp_val_new = {}
            for camp_values in camp_val_keys:
                camp_val_new[get_translation_specific(camp_values)] = data["camping.values."+camp_values]
            data["camping.values"] = camp_val_new
        except:
            pass

    # zodiac_tree
    for zodiac_in in range(len(data["zodiac_tree"])):
        data["zodiac_tree"][zodiac_in]["_id"] = "zodiac_{0}".format(zodiac_in)
        data["zodiac_tree"][zodiac_in]["name"] = get_translation_specific(data["zodiac_tree"][zodiac_in]["name"])
        data["zodiac_tree"][zodiac_in]["description"] = get_translation_specific(data["zodiac_tree"][zodiac_in]["description"])

        for zodiac_cost_index in range(len(data["zodiac_tree"][zodiac_in]["costs"])):
                data["zodiac_tree"][zodiac_in]["costs"][zodiac_cost_index]["_id"] = "zodiac_{0}_cost_{1}".format(zodiac_in,zodiac_cost_index)

    # skills
    data["buffs"] = []
    data["debuffs"] = []
    data["common"] = []

    for sk_in in range(len(data["skills"])):
        data["skills"][sk_in]["_id"] = "skill_{0}".format(sk_in)
        data["skills"][sk_in]["name"] = get_translation_specific(data["skills"][sk_in]["name"])
        data["skills"][sk_in]["description"] = get_translation_specific(data["skills"][sk_in]["description"])

        try:
            for sk_bf_in in range(len(data["skills"][sk_in]["buff"])):
                data["buffs"].append(data["skills"][sk_in]["buff"][sk_bf_in])
        except:
            pass

        try:
            for sk_dbf_in in range(len(data["skills"][sk_in]["debuff"])):
                data["debuffs"].append(data["skills"][sk_in]["debuff"][sk_dbf_in])
        except:
            pass

        try:
            for sk_cm_in in range(len(data["skills"][sk_in]["common"])):
                data["common"].append(data["skills"][sk_in]["common"][sk_cm_in])
        except:
            pass

        try:
            data["skills"][sk_in]["enhanced_description"] = get_translation_specific(data["skills"][sk_in]["enhanced_description"])
        except:
            pass

        try:
            data["skills"][sk_in]["soul_description"] = get_translation_specific(data["skills"][sk_in]["soul_description"])
        except:
            pass

        for sk_enh_index in range(len(data["skills"][sk_in]["enhancements"])):
            data["skills"][sk_in]["enhancements"][sk_enh_index]["_id"] = "skill_{0}_enh_{1}".format(sk_in,sk_enh_index)
            data["skills"][sk_in]["enhancements"][sk_enh_index]["string"] = get_translation_specific(data["skills"][sk_in]["enhancements"][sk_enh_index]["string"])

            for sk_enh_cost_index in range(len(data["skills"][sk_in]["enhancements"][sk_enh_index]["costs"])):
                data["skills"][sk_in]["enhancements"][sk_enh_index]["costs"][sk_enh_cost_index]["_id"] = "skill_{0}_enh_{1}_cost_{2}".format(sk_in,sk_enh_index,sk_enh_cost_index)

    return data


def buffs_parser(filename,data,get_translation_specific):
    data["name"] = get_translation_specific(data["name"])
    data["effect"] = get_translation_specific(data["effect"])
    return data


def ex_equip_parser(filename,data,get_translation_specific):
    data["name"] = get_translation_specific(data["name"])
    data["description"] = get_translation_specific(data["description"])

    for sk_exeq_index in range(len(data["skills"])):
        data["skills"][sk_exeq_index]["_id"] = sk_exeq_index

        try:
            data["skills"][sk_exeq_index]["description"] = get_translation_specific(data["skills"][sk_exeq_index]["description"])
        except:
            pass

        try:
            if data["skills"][sk_exeq_index]["skill_description"]:
                data["skills"][sk_exeq_index]["skill_description"] = get_translation_specific(data["skills"][sk_exeq_index]["skill_description"])
        except:
            pass

    return data

# =================================
# STEP 1 -> translation

BASE_PATH = os.getcwd()
BUILD_FOLDER=BASE_PATH+"/dist_py"
COLLECTIONS_FOLDER_NAME = '_collections'
TRANSLATION_FOLDERS = [ 'hero', 'artifact', 'materials', 'buffs', 'ex_equip' ]

text_en = json.load(open(BASE_PATH+'/src/text/text_en.json'))
lang_files = sorted(glob.glob(BASE_PATH+ "/src/text/*.json"))

if os.path.exists(BUILD_FOLDER):
    shutil.rmtree(BUILD_FOLDER);
    os.makedirs(BUILD_FOLDER)

# =================================
# STEP 2 -> mount to collection & import
buildCollectionsFolder=BUILD_FOLDER+"/"+COLLECTIONS_FOLDER_NAME

mongoimport_command = "mongoimport --host $E7DB_ATLAS_SHARDS --ssl --username $E7DB_ATLAS_USER --password \"$E7DB_ATLAS_PW\" --authenticationDatabase $E7DB_ATLAS_AUTH_DB --db $E7DB_ATLAS_DB --collection {0} --type json --file {1} --jsonArray --drop;"

# =================================

def do_translate():
    languages = []
    for lang_file in lang_files:
        languages.append(getLangKey(lang_file))

    print('languages to translate: ')
    print(languages)
    # languages = ['en','de','es','fr','ja','kr','pt','zht']

    for folder_to_build in TRANSLATION_FOLDERS:
        translate_folder(BASE_PATH+'/src/'+ folder_to_build)
    printline()
    print('Done creating translated files, building into single jsonArray for mongoimport')
    printline()

def do_build():
    mkdir(COLLECTIONS_FOLDER_NAME)

    build_folder_folders = [ f.name for f in os.scandir(BUILD_FOLDER) if f.is_dir() and not f.name == COLLECTIONS_FOLDER_NAME ]

    for built_folder in build_folder_folders:
        mount_collection_array(built_folder)
    printline()
    print('Done creating collections for mongo')
    printline()

def do_import():
    print('calling mongoimport')
    printline()

    collections = glob.glob(buildCollectionsFolder+'/*.json')
    regex = re.compile(r"(.*\/)(.*)(\.json)", re.IGNORECASE)

    for collection_file in collections:
        collection_filename = regex.sub(r"\2", collection_file)
        update_mongo(collection_filename, collection_file)

    printline()
    print('Done importing into mongodb')
    printline()

# =================================

do_translate()
do_build()

if not args.buildonly:
    do_import()

exit(0)

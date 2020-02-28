import json
import glob
import re
import os
import subprocess
import shutil
import copy

# =================================

def getLangKey(langFilePath):
    lang_regex = re.compile(r"(.*\/)(text\_)(.*)(\.json)", re.IGNORECASE)
    return lang_regex.sub(r"\3", langFilePath)

def mkdir(folderName):
    if not os.path.exists(buildFolder + '/' + folderName):
        os.makedirs(buildFolder + '/' + folderName)

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
            translation = customLangData[translationKey]

        if not translation:
            translation = text_en[translationKey]

        if not translation:
            return 'MISSING_TRANSLATION_VALUE'

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
            currentLanguageData = json.load(open(lang))
            get_translation_specific = get_translation(currentLanguageData)
            lang_key = getLangKey(lang)
            lang_folder = foldername+'-'+lang_key
            mkdir(lang_folder)
            print('-- ' + lang_key)
            saveFile(filename, buildFolder+'/'+lang_folder, fileParser(filename,copy.deepcopy(file_data),get_translation_specific))


# =================================

def artifact_parser(filename,data,get_translation_specific):
    data["name"] = get_translation_specific(data["name"])
    data["description"] = get_translation_specific(data["description"])
    data["skill"]['description'] = get_translation_specific(data["skill"]["description"])
    return data

def materials_parser(filename,data,get_translation_specific):
    data["name"] = get_translation_specific(data["name"])
    data["description"] = get_translation_specific(data["description"])
    data["category"] = get_translation_specific(data["category"])
    return data

# =================================

BASE_PATH = os.getcwd()

buildFolder=BASE_PATH+"/dist_trans"

if os.path.exists(buildFolder):
    shutil.rmtree(buildFolder);
    os.makedirs(buildFolder)

languages = []
lang_files = sorted(glob.glob(BASE_PATH+ "/src/text/*.json"))
for lang_file in lang_files:
    languages.append(getLangKey(lang_file))

print('languages to translate: ')
print(languages)
# languages = ['en','de','es','fr','ja','kr','pt','zht']
text_en = json.load(open(BASE_PATH+'/src/text/text_en.json'))

# =================================

translate_folder(BASE_PATH+'/src/artifact')
translate_folder(BASE_PATH+'/src/materials')
# translate_folder('../src/hero', hero_parser)

import json
import glob
import re
import os
import subprocess
import shutil

#### import to mongodb server
mongoimport = "mongoimport --host $E7DB_ATLAS_SHARDS --ssl --username $E7DB_ATLAS_USER --password \"$E7DB_ATLAS_PW\" --authenticationDatabase $E7DB_ATLAS_AUTH_DB --db $E7DB_ATLAS_DB --collection {0} --type json --file {1} --jsonArray --drop;";

buildFolder="../dist"

if os.path.exists(buildFolder):
    shutil.rmtree(buildFolder);
    os.makedirs(buildFolder)

def update_mongo(collection, filePath):
    print("** Updating MONGODB => collection \"{0}\" with file {1} **\n".format(collection, filePath))
    subprocess.call(mongoimport.format(collection, filePath), shell=True)
    print("\n** MONGODB => collection \"{0}\" updated **\n\n".format(collection, filePath))


def mount_collection_array(files, parentFolder):
    collection = []
    filesFolder=buildFolder + "/" + parentFolder;
    regex = re.compile(r"(.*\/)(.*)(\.json)", re.IGNORECASE)

    for file in files:
        if not os.path.exists(filesFolder):
            os.makedirs(filesFolder)

        filename = regex.sub(r"\2", file)

        data = json.load(open(file))
        keys = data.keys()
        if "_id" not in keys:
            print("file {0} does not containt _ID, adding it".format(filename))
            data["_id"] = filename
        collection.append(data)

    compiledCollection = filesFolder + "/{0}.json".format(parentFolder)
    with open(compiledCollection, 'w') as f:
        json.dump(collection, f)
        print("\n** Compiled:" + compiledCollection + " **\n\n")
    update_mongo(parentFolder, compiledCollection)


## compile collections
mount_collection_array(glob.glob("../src/artifact/*.json"), "artifact")
mount_collection_array(glob.glob("../src/hero/*.json"), "hero")

## compile translation collections
translations = glob.glob("../src/text/*.json")

for file in translations:
    translationFolder=buildFolder + "/text";
    if not os.path.exists(translationFolder):
        os.makedirs(translationFolder)

    regex = re.compile(r"(.*\/)(.*)(\.json)", re.IGNORECASE)
    filename = regex.sub(r"\2", file)

    collection = []
    data = json.load(open(file))
    for k in data.keys():
        new_obj = {}
        new_obj['text'] = data[k]
        new_obj['_id'] = k
        collection.append(new_obj)

    compiledTranslationCollection = translationFolder + "/{0}.json".format(filename)
    with open(compiledTranslationCollection, 'w') as f:
        json.dump(collection, f)
        print("compiled:" + compiledTranslationCollection)
    update_mongo(filename, compiledTranslationCollection)

print("All done!");




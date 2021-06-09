from tkinter import filedialog
from tkinter import *
import copy
import shutil
import sys
import json
import os
from pathlib import Path
import locg
import comicvine
import comicutil
import archiveutil
import imageutil
import config
import comixology
import comicdb
from comicapi import comicinfoxml, filenameparser

SETTINGS = config.get_config() 
REMOVE_SCENE_PROMO = SETTINGS["remove_scene_promo"]
REMOVE_SUBFOLDERS = SETTINGS["remove_subfolders"]
REMOVE_COMIXOLOGY_META = SETTINGS["remove_comixology_meta"]
REMOVE_HASHED_FILES = SETTINGS["remove_hashed_files"]
LIBRARY_LOCATION = SETTINGS["library_location"]
KEEP_ORIGINAL = SETTINGS["keep_original"]
COMPARE_COVERS = SETTINGS["compare_covers"]
PDF_ZOOM = SETTINGS['from_pdf_zoom']
ARCHIVE_TYPE = SETTINGS['archive_type']
METADATA_TYPE = SETTINGS['metadata_type']
IMAGE_TYPE = SETTINGS['image_type']
RENAME_TEMPLATE = SETTINGS['rename_template']
COMIC_DATABASE = SETTINGS["comic_database"]
WRITE_METADATA = SETTINGS["write_metadata"] 

VERSION = ""
if os.path.exists(Path(__file__).parent.joinpath("version.json")):
    with open(Path(__file__).parent.joinpath("version.json")) as version_text:
        version_json = json.load(version_text)
        VERSION = version_json['version']


def screen_clear():
   # for mac and linux(here, os.name is 'posix')
   if os.name == 'posix':
      _ = os.system('clear')
   else:
      # for windows platfrom
      _ = os.system('cls')
   # print out some text

def move_to_library(file,details):
    extension = os.path.splitext(file)[1]
    new_name = copy.copy(RENAME_TEMPLATE)
    seperator = os.path.sep
    publisher = details["publisher"]
    series = details["volumeName"]
    issue_name = details["issueName"]
    issue_year = details["storeDate"].split('-')[0]
    series_year = details["volumeYear"]
    if series_year == "UNKNOWN" or series_year == "PRESENT" or series_year == None or series_year == "":
        series_year = issue_year
    issue = details['issueNumber']
    new_name = new_name.format(seperator=seperator,publisher=publisher,series=series,series_year=series_year,issue_year=issue_year,issue_pad2=comicutil.pad_to_length(issue,2),issue_pad3=comicutil.pad_to_length(issue,3),issue_name=issue_name)
    new_name = os.path.join(LIBRARY_LOCATION,f"{new_name}{extension}")
    new_name = comicutil.stripBadChars(new_name)
    os.makedirs(os.path.dirname(new_name),exist_ok=True)
    shutil.move(file,new_name)
    print(f"Comic copied to {new_name}")

def convert_to(oldfile,newfile,metadata=None,image_type=IMAGE_TYPE):
    try:
        tmp = ""
        try:
            tmp = archiveutil.extract_to_temp(oldfile,PDF_ZOOM)
        except Exception as e:
            print("Extract error: ",e)
            shutil.rmtree(tmp)
            return False

        if REMOVE_SCENE_PROMO:
            try:
                comicutil.remove_promos_from_dir(tmp)
            except Exception as e:
                print(f"Error removing promos: {e}")
                shutil.rmtree(tmp)
                return False

        if REMOVE_COMIXOLOGY_META:
            try:
                comicutil.remove_comixology_meta_from_dir(tmp)
            except Exception as e:
                print(f"Error removing promos: {e}")
                shutil.rmtree(tmp)
                return False

        if REMOVE_HASHED_FILES:
            try:
                comicutil.remove_hashed_files_from_dir(tmp)
            except Exception as e:
                print(f"Error removing hashed files: {e}")
                shutil.rmtree(tmp)
                return False

        if IMAGE_TYPE != "" and IMAGE_TYPE != None:
            imageutil.convert_dir_to_type(tmp,image_type)

        if REMOVE_SUBFOLDERS:
            archiveutil.remove_subfolders(tmp)

        if metadata is not None:
            try: 
                meta = comicutil.comicdb_to_meta(metadata)
                metas = comicutil.get_meta_from_dir(tmp)
                for m in comicutil.metadata_files:
                    if metas[METADATA_TYPE] == "" and WRITE_METADATA:
                        comicutil.write_meta_to_dir(meta,tmp,METADATA_TYPE)
                    elif metas[METADATA_TYPE] != "" and WRITE_METADATA == "overwrite":
                        comicutil.write_meta_to_dir(meta,tmp,METADATA_TYPE)
                    elif metas[METADATA_TYPE] != "" and WRITE_METADATA:
                        if METADATA_TYPE == "ComicInfo.xml":
                            xml1 = comicinfoxml.ComicInfoXml().stringFromMetadata(metas[METADATA_TYPE])
                            xml2 = comicinfoxml.ComicInfoXml().stringFromMetadata(meta)
                            xml3 = ""
                            if WRITE_METADATA == "merge_new":
                                xml3 = comicutil.merge_meta_xml(xml1,xml2,"xml1")
                            if WRITE_METADATA == "merge_existing":
                                xml3 = comicutil.merge_meta_xml(xml1,xml2,"xml2")
                            new_meta = comicinfoxml.ComicInfoXml().metadataFromString(xml3)
                            comicutil.write_meta_to_dir(new_meta,tmp,METADATA_TYPE)
            except Exception as e:
                print(f"Failed to write metadata to directory: {repr(e)}")
                
        try:
            return archiveutil.dir_to_archive(tmp,newfile,metadata)
        except Exception as e:
            print("Archive error: ",e)
            shutil.rmtree(tmp)
            return False
    except Exception as e:
        print(f"Convert error: {repr(e)}")
        return False

def file_or_folder():
    print("--------------------------")
    print("File or Folder? Default: 1")
    print("--------------------------")
    print("1: File")
    print("2: Folder")
    print("--------------------------")
    val = input("") or "1"
    if val == "":
        return
    if val == "1":
        Tk().withdraw()
        return filedialog.askopenfilename(initialdir = "/",title = "Select file")
    if val == "2":
        Tk().withdraw()
        return filedialog.askdirectory(initialdir="/",title='Select directory')

def convert_to_archive_type():
    print("--------------------------")
    print("Convert to New Format")
    print("Default 1")
    print("--------------------------")
    print(f"1: Convert to Prefered Type: {ARCHIVE_TYPE.upper()}")
    print("2: Convert to CBZ")
    print("3: Convert to CBR")
    print("4: Convert to PDF")
    print("5: Convert to CB7")
    print("6: Convert to CBA")
    print("7: Convert to CBT")
    print("8: Convert to EPUB")
    print("--------------------------")
    val = input("") or "1"
    selected = file_or_folder()
    if selected == "" or selected == None:
        return
    file_types = {"1":ARCHIVE_TYPE.lower(),"2":"cbz","3":"cbr","4":"pdf","5":"cb7","6":"cba","7":"cbt","8":"epub"}

    if os.path.isdir(selected):
        for subdir, dirs, files in os.walk(selected):
            for file in files:
                if archiveutil.is_archive(file):
                    old_file = subdir + os.sep + file
                    base_file = os.path.splitext(old_file)[0]
                    new_file = f"{base_file}.{file_types[val]}"
                    converted = convert_to(old_file,new_file)
                    print(f"file coverted: {converted}")
                    if not KEEP_ORIGINAL and converted and old_file != new_file:
                        os.remove(old_file)
    else:
        if archiveutil.is_archive(selected):
            old_file = selected
            base_file = os.path.splitext(old_file)[0]
            new_file = f"{base_file}.{file_types[val]}"
            converted = convert_to(old_file,new_file)
            if not KEEP_ORIGINAL and converted and old_file != new_file:
                os.remove(old_file)

def convert_to_image_type():
    print("--------------------------")
    print("Convert to New Format")
    print("Default 1")
    print("--------------------------")
    print(f"1: Convert to Prefered Type: {IMAGE_TYPE.upper()}")
    print("2: Convert to JPG")
    print("3: Convert to PNG")
    print("4: Convert to WEBP")
    print("5: Convert to BMP")
    print("6: Convert to GIF")
    print("7: Convert to TIFF")
    print("--------------------------")
    val = input("") or "1"
    selected = file_or_folder()
    if selected == "" or selected == None:
        return
    image_types = {"1":IMAGE_TYPE.lower(),"2":"jpg","3":"png","4":"webp","5":"bmp","6":"gif","7":"tiff"}

    if os.path.isdir(selected):
        for subdir, dirs, files in os.walk(selected):
            for file in files:
                if archiveutil.is_archive(file):
                    file = subdir + os.sep + file
                    converted = convert_to(file,file,comicdb_info=None,image_type=image_types[val])
                    print(f"Image files in {converted} converted to {image_types[val]}")

    else:
        if archiveutil.is_archive(selected):
            file = selected
            converted = convert_to(file,file,comicdb_info=None,image_type=image_types[val])
            print(f"Image files in {converted} converted to {image_types[val]}")

def remove_scene_promos():
    print("--------------------------")
    print("Remove Scene Promos")
    print("")
    selected = file_or_folder()
    if selected == "" or selected == None:
        return
    if os.path.isdir(selected):
        for subdir, dirs, files in os.walk(selected):
            for file in files:
                filepath = subdir + os.sep + file
                if archiveutil.is_archive(filepath):
                    comicutil.remove_promos_from_file(filepath,PDF_ZOOM)
    else:
        if archiveutil.is_archive(selected):
            comicutil.remove_promos_from_file(selected,PDF_ZOOM)

def set_database():
    print("--------------------------")
    print("Set Comic Database")
    print("Default 1")
    print("--------------------------")
    print("1: Comicvine")
    print("2: League of Comic Geeks")
    print("3: Comixology")
    print("4: Back to Menu")
    print("--------------------------")
    val = input("") or "1"
    if val == "1":
        comicdb.set_database("comicvine")
        print("Comic Database set to Comicvine")
    if val == "2":
        comicdb.set_database("locg")
        print("Comic Database set to League of Comic Geeks")
    if val == "3":
        comicdb.set_database("comixology")      
        print("Comic Database set to Comixology")  
    if val == "4" or val.lower() == "q" or val == "quit" or val == "back":
        comicdb.set_database("comicvine")        

def tag_interactive(filename,results=None,issues=None):
    last_series = None
    results = results
    issues = issues
    originalfilename = filename
    details = comicutil.get_comic_details(filename)
    query = f"{details.series}"
    if details.year == None or details.year == "":
        details.year = "0000"
    if results != None:
        last_series = results["last_series"]
        results = results["results"]
    if results == None:
        results = comicdb.search_series(query,50,70)
    print("-----------------------------------------------------------------")
    print(f"File Name:    {originalfilename}")
    #print(f"Search Query: {query}")
    stop = False
    year_range = False
    for result in results:
        if not stop:
            if result["end_year"] == "PRESENT" or result["end_year"] == "UNKNOWN":
                year_range = True
            elif int(details.year) <= int(result["end_year"]):
                year_range = True
            if year_range:
                val = None
                if last_series != details.series:
                    print(f'---------------------- Seach Result -----------------------------')
                    print(f'Series Name:        {result["name"]}')
                    print(f'Year:               {result["year"]}')
                    print(f'Publisher:          {result["publisher"]}')
                    print(f'Issues:             {result["issue_count"]}')
                    print(f'Series Link:        {result["link"]}')
                    print("-----------------------------------------------------------------")
                    print(f'Name Match Confidence:   {result["confidence"]}')
                    print("-----------------------------------------------------------------")
                    val = input("Is this the right series? (y/n/q) default (y): ") or "y"
                else:
                    val = "y"
                if val.lower() == "y" or val.lower() == "yes":
                    val = "y"
                elif val.lower() == "n" or val.lower() == "no":
                    val = "n"
                elif val.lower() == "q" or val.lower() == "quit" or val.lower() == "exit":
                    val = "q"
                if val == "y":
                    if issues == None:
                        issues = comicdb.get_series_by_id(result["id"])
                    for issue in issues:
                        if issue['issueNumber'] == details.issue or details.issue == "":
                            if "storeDate" not in issue:
                                issue.update(comicdb.get_issue_by_id(issue["id"]))
                            extracted = ""
                            if COMPARE_COVERS:
                                extracted = archiveutil.extract_to_temp(filename)
                            #if details.year in issue["storeDate"]:
                            if True:
                                print("-----------------------------------------------------------------")
                                print(f"File Name:    {originalfilename}")
                                print(f'---------------------- Seach Result -----------------------------')
                                print(f'Issue Name:         {issue["issueName"]}')
                                print(f'Store Date:         {issue["storeDate"]}')
                                print(f'Issue Link:         {issue["issueLink"]}')
                                print(f'Series Name:        {result["name"]}')
                                print(f'Series Year:        {result["year"]}')
                                print(f'Publisher:          {result["publisher"]}')
                                if COMPARE_COVERS:
                                    webcover = imageutil.getImageFromUrl(issue['coverImage'])
                                    cbcover = comicutil.get_cover_from_dir(extracted)
                                    cover_confidence = imageutil.compare_images2(webcover,cbcover)
                                    print(f'Cover Match Confidence:   {cover_confidence}')
                                print("-----------------------------------------------------------------")
                                val = input("Rename with these details? (y/n/q) default (y): ") or "y"
                                if val.lower() == "y" or val.lower() == "yes":
                                    val = "y"
                                elif val.lower() == "n" or val.lower() == "no":
                                    val = "n"
                                elif val.lower() == "q" or val.lower() == "quit" or val.lower() == "exit":
                                    val = "q"
                                if val == "y":
                                    if "description" not in issue:
                                        issue.update(comicdb.get_issue_by_id(issue["id"]))
                                    file_folder = os.path.dirname(filename)
                                    issue_name = comicutil.stripBadChars(comicutil.remove_issue_number(issue["issueName"]))
                                    issue_year = issue["storeDate"].split("-")[0]
                                    #new_filename = f'{issue_name} #{comicutil.pad_to_length(issue["issueNumber"])} ({issue_year}).{ARCHIVE_TYPE.lower()}'
                                    new_filename = f"temp.{ARCHIVE_TYPE.lower()}"
                                    new_file = os.path.join(file_folder,new_filename)
                                    meta_details = copy.deepcopy(result)
                                    meta_details.update(issue)
                                    converted = convert_to(filename,new_file,meta_details)
                                    if not KEEP_ORIGINAL and converted and filename != new_file:
                                        os.remove(filename)
                                    move_to_library(new_file,meta_details)
                                    result["last_series"] = details.series
                                    results = {"results":results,"last_series":details.series}
                                    return results, issues, ""
                                    break
                                if val == "n":
                                    pass
                
                                if val == "q":
                                    if os.path.isdir(extracted):
                                        shutil.rmtree(extracted)
                                    stop = True
                                    break
                if val == "q":
                    return results, issues, "quit"

                if val == "n":
                    pass
    try:
        if os.path.isdir(extracted):
            shutil.rmtree(extracted)
    except:
        pass
    results = {"results":results,"last_series":details.series}
    return results, issues, ""

def search_and_tag_interactive():
    print("--------------------------")
    print("Get Details and Organize")
    print("")
    selected = file_or_folder()
    if selected == "" or selected == None:
        return
    if os.path.isdir(selected):
        results = None
        issues = None
        for subdir, dirs, files in os.walk(selected):
            for file in files:
                filepath = subdir + os.sep + file
                if archiveutil.is_archive(filepath):
                    details = comicutil.get_comic_details(filepath)
                    if results is not None:
                        if results["last_series"] != details.series:
                            results = None
                            issues = None
                    r, i, q = tag_interactive(filepath,results,issues)
                    results = r
                    issues = i
                    if q == "quit":
                        break
    else:
        if archiveutil.is_archive(selected):
            tag_interactive(selected)

def main_menu():
    print("============================================================================")
    print(f"                           ComicTools {VERSION}")
    print("============================================================================")
    print("What would like to do? default: 1")
    print("")
    print("1: Tag and Organize.")
    print("2: Convert Archive Yype.")
    print("3: Convert Image Type.")
    print("4: Remove Scene Promos.")
    print("5: Change Comic Database.")
    print("6: List Supported Archive Types.")
    print("7: Quit.")
    print("============================================================================")
    val = input("") or "1"
    if val == "1":
        search_and_tag_interactive()
    if val == "2":
        convert_to_archive_type()
    if val == "3":
        convert_to_image_type()
    if val == "4":
        remove_scene_promos()
    if val == "5":
        set_database()
    if val == "6":
        archiveutil.list_supported_formats()
    if val == "7" or val.lower() == "q" or val.lower() == "quit" or val.lower() == "exit":
        sys.exit()

if __name__ == "__main__":
    while True:
        main_menu()
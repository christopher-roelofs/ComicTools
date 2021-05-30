
import os
import json
import comixology
import comicvine
import locg
import config

mappings_file = 'comicdb.json'
mappings = {}

SETTINGS = config.get_config() 

comicdb = comixology

if "comic_database" in SETTINGS:
    if SETTINGS["comic_database"] == "comicvine":
        comicdb = comicvine
    if SETTINGS["comic_database"] == "comixology":
        comicdb = comixology
    if SETTINGS["comic_database"] == "locg":
        comicdb = locg

def set_database(database):
    global comicdb
    if database == "comicvine":
        comicdb = comicvine
    if database == "comixology":
        comicdb = comixology
    if database == "locg":
        comicdb = locg

def load_mappings():
    global mappings
    if os.path.exists(mappings_file):
        with open(mappings_file) as mappings_text:
            mappings = json.load(mappings_text)
    else:
        pass

def search_comics(query,volumeConfidence=0,issueConfidence=0):
    return comicdb.search_comics(query,volumeConfidence=0,issueConfidence=0)

def search_series(query,volumeConfidence=0,issueConfidence=0):
    return comicdb.search_series(query,volumeConfidence=0,issueConfidence=0)

def get_series_by_id(id):
    return comicdb.get_series_by_id(id)

def get_issue_by_id(id):
    return comicdb.get_issue_by_id(id)

def map_publisher(publisher):
    if publisher in mappings["publishers"]:
        return mappings["publishers"][publisher]
    else:
        return publisher


load_mappings()

    

import datetime
import sys
import os
import csv
import pandas as pd
import time

sys.path.insert(0, os.path.join(os.path.split(os.getcwd())[0],'src/'))
from arxivbulletin import arxivbulletin

def openfile(fn):
    # open and read from user provided files
    try:
        results = []
        with open(os.path.join(os.path.split(os.getcwd())[0], fn)) as f:
            for line in f:
                results.append(line.strip())
        return results
    # if files do not exist, create empty array
    except IOError:
        results = []
        return results

path ='/home/bart/Documents/arXiv/cmtucla_arXiv'
# Go through folders with users
user_list = []
for subdir, dirs, files in os.walk(os.path.join(path,'users')):
    for folders in dirs:
        user_list.append(folders)


for user in user_list:
    keywords = openfile(os.path.join(path,'users/',user,'keywords.txt'))
    keyauthors = openfile(os.path.join(path,'users/',user,'keyauthors.txt'))
    myconfig = pd.read_csv(os.path.join(path,'users/',user,'config.csv'), header=None, index_col=0, squeeze=True).to_dict()
    myconfig['categories'] = openfile(os.path.join(path,'users/',user,'categories.txt'))

    arxivsummary = arxivbulletin(myconfig, keywords, keyauthors)
    arxivsummary.send_report()
    time.sleep(4)

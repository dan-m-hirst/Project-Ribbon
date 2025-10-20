# -*- coding: utf-8 -*-
"""


@author: Daniel
"""

import pandas as pd
import glob
import os
import numpy as np
# Read HTML file exported by FM - in this case,
# an example of an output from the player scouting page
# This reads as a list, not a dataframe

def get_statcols(data):
    to_keep = []
    raw_start = data.columns.get_loc('Mins') + 1
    raw_end = data.columns.get_loc('AP')
    for i in range(raw_start,raw_end):
        to_keep.append(data.columns[i])
    # could use to_drop = ["Rec","Inf","Name","Division","Club","Age","Mins","AP","index"]
    # debug func to track cols print(f"Keeping {to_keep}...")
    return data.drop(data.columns.difference(to_keep),axis=1).columns

def data_import(datapath):
    print("Reading HTML input file...")
    data = pd.read_html(datapath)[0]
    print("File read! Cleaning...")
    data = data.replace('-',0,regex=False)
    # clean %age stats, coerce all stats to float to avoid errors in median() funcs later
    for col in data.columns:
        if "%" in col:
            data[col] = data[col].str.strip("%").astype(float)
    statcols = get_statcols(data)
    for col in data[statcols].columns:
        if data[col].dtypes != float:
            data[col] = data[col].astype(float)
    data = data.replace('-',0)
    data = data.drop(['Rec','Inf'],axis=1)
    print("Data cleaned!")
    return data

def join_league_rankings(data, leagues_path):
    # join leagues to rankings, create index to track rank no.s and create weight cols
    print("Parsing league rankings...")
    if leagues_path:
        leagues_list = pd.read_html(
            os.path.join(leagues_path)
            )
    else:
        leagues_list = pd.read_html(
            os.path.join(
                r'\Users\Daniel\Documents',
                'Sports Interactive',
                'Football Manager 2024', 
                'lgs.html'
            )
        )
    league_strength_fieldnm = 'League Strength'
    leagues = leagues_list[0]
    leagues[league_strength_fieldnm] = 1 + leagues.index[::-1]
    leagues[league_strength_fieldnm] = leagues[league_strength_fieldnm].fillna(0)
    leagues = leagues.rename(columns={'Name':'Division'})
    # alt weight method: leagues['weight2'] = leagues['index']**2 / max(leagues['index']**2)
    # alt weight method: leagues['dumbweight1.025'] = (1.025**leagues['index'] / max(1.025**leagues['index']))
    print("Merging rankings onto main data...")
    merged = pd.merge(
        left = data,
        right = leagues,
        how = 'left',
        on = 'Division',
        validate = 'many_to_one'
        )
    print("Files merged! Handling non-joins...")
    weightcols = leagues.drop(['Division', 'Nation', 'Reputation'], axis=1)
    for col in merged.columns:
        if merged[col].isna().any() == True and col in weightcols:
            # Get minimum weight from leagues file
            minweight = min(merged[col])
            # Assign NaN rows to use this minimum weight
            merged[col] = merged[col].fillna(minweight)
    # Give weight column generic name for usability
    print("Merge complete!")
    return merged

def convertaskprice(price):
    lgth = len(price)
    if price in ['','Â£0']:
        return 0
    returndict = {
        'M':float(price[2:lgth-1])*1000000,
        'K':float(price[2:lgth-1])*1000}
    try:
        return returndict[price[-1:]]
    except KeyError:
        return float(price[-(lgth - 1):])

def percentilerank(df):
        return df.rank(0,'min',pct=True)


def addpercentiles(data):
    statcols = get_statcols(data)
    perc_cols = []
    print("Deriving percentile rankings...")
    for col in data[statcols]:
        origcol = data[col]
        perc_colname = 'Perc_' + col
        perc_cols.append(perc_colname)
        perc_col = round(100*percentilerank(origcol), 2)
        data[perc_colname] = perc_col
    data['Avg_perc'] = data[perc_cols].mean(axis=1)
    print("Calculating percentile-of-percentile rankings...")
    data['Perc_Score'] = 100*percentilerank(data['Avg_perc'])
    print("Calculating costs...")
    data['Perc_Cost'] = 100*percentilerank(data['AP'])
    data = data.reindex(range(len(data['League Strength'])))
    percs = data['AP'].quantile(q=data['Perc_Cost']/100)
    percs = percs.reset_index(drop=True)
    data['Projected Cost'] = round(percs,0)
    print("All percentiles derived!")
    return data


def do_all(datapath, leagues_path):
    data = data_import(datapath)
    data = join_league_rankings(data, leagues_path)
    data['AP'] = data['AP'].map(convertaskprice)
    data = addpercentiles(data)
    return data
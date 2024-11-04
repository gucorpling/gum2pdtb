import os
import pandas as pd
import numpy as np
import re
from collections import defaultdict
import json
import xml.etree.ElementTree as ET

"""DM-RSTrel combo frequency"""

def update_DM_rst_dct(dct, fp_rs4):
    """
    take an .rs4 file, update the existing dictionary with
    all the DMs and orphans, along with the RST relations
    they are associated with.
    """

    # read the file into xml tree
    tree = ET.parse(fp_rs4)
    root = tree.getroot()
        
    # concatenate all the segments into a single list of tokens
    text = []
    for segment in root.iter('segment'):
        text.extend(segment.text.split())
    
    # retrieve all the DMs and Orphans
    for signal in root.iter('signal'):
        if signal.attrib['type'] not in ['dm', 'orphan']:
            continue
        # get the DM token
        # int(i)-1 because .rs4 token IDs are 1-based
        tok_ids = sorted([int(i)-1 for i in signal.attrib['tokens'].split(',')])
        toks = ' '.join(text[i] for i in tok_ids)
        toks = toks.lower()
        
        # get the relation associated with it
        source_edu = signal.attrib['source']
        rel = root.find(f".//*[@id='{source_edu}']").attrib['relname']
        
        if toks not in dct:
            dct[toks] = dict()
        if rel not in dct[toks]:
            dct[toks][rel] = 0
        dct[toks][rel] += 1

    return dct

"""DM -> PDTB sense & RST -> PDTB sense"""

# simplifying function
def simplify_pdtb_sense(pdtb_sense):
    simplified = re.sub(r"\.(A|a)rg.+", "", pdtb_sense)  # e.g. arg1-as-denier
    simplified = re.sub(r"\+[a-zA-Z]+", "", simplified)  # e.g. +SpeechAct
    return simplified

# DM -> PDTB sense
def create_dm2pdtb(url, cutoff=0.01, collapse_long_distance=True):
    """
    take a Google sheet url, return DM -> PDTB sense dictionary.
    """
    # pdtb manual
    pdtb_manual = pd.read_csv(url, keep_default_na=False)
    
    # converting df into dictionaries
    # pdtb manual (with simplification)
    pdtb_manual_dct = defaultdict(lambda: defaultdict(lambda: 0))
    for i in range(len(pdtb_manual)):
        if pdtb_manual.loc[i, "Lemma"] != "":
            lemma = pdtb_manual.loc[i, "Lemma"].lower().strip()
            if collapse_long_distance:
                lemma = re.sub(r"\+", " ", lemma)
        freq = pdtb_manual.loc[i, "Freq"]
        sense = pdtb_manual.loc[i, "Sense"].lower().strip() # taking sense 1
        if "|" in sense:
            sense = sense.split("|")[0]
        sense_simple = simplify_pdtb_sense(sense)
        pdtb_manual_dct[lemma][sense_simple] += int(freq)
    
    # applying frequency cut-off at p = 0.01 post-hoc
    if not cutoff:
        return pdtb_manual_dct
    for dm in pdtb_manual_dct:
        senses = pdtb_manual_dct[dm]
        total = sum([senses[sense] for sense in senses])
        pdtb_manual_dct[dm] = {
            sense:freq for sense, freq in pdtb_manual_dct[dm].items()\
                if freq > total*cutoff
                }
    return pdtb_manual_dct

# rst-dt -> gum8 (tatsuya's mapping)
def create_rstdt2gum8(url, reverse=True):
    """
    take a Google sheet url, return DM -> PDTB sense dictionary.
    """
    
    rstdt2gum = pd.read_csv(url, keep_default_na=False)

    rstdt2gum_dct = {}
    for i in range(len(rstdt2gum)):
        rstdt = rstdt2gum.loc[i, "RST-DT"].lower().strip()
        gum8_relation = [item.lower().strip(' ') for item in rstdt2gum.loc[i, "GUM8"].split(',')]
        rstdt2gum_dct[rstdt] = gum8_relation
    
    if not reverse:
        return rstdt2gum_dct
    
    gum2rstdt_dct = {}
    for key in rstdt2gum_dct:
        for val in rstdt2gum_dct[key]:
            if val not in gum2rstdt_dct:
                gum2rstdt_dct[val] = []
            gum2rstdt_dct[val].append(key)
    
    return gum2rstdt_dct

# pdtb -> rstdt mapping
def create_pdtb2rstdt(url, reverse=True):
    pdtb2rstdt = pd.read_csv(url,keep_default_na=False)
    pdtb2rstdt_dct = {}
    for i in range(len(pdtb2rstdt)):
        sense = pdtb2rstdt.loc[i, "Sense-1_simp"].lower().strip()
        iso = [item.lower().strip(' ') for item in pdtb2rstdt.loc[i, "RST-DT (ISO)"].split(',')]
        olia = [item.lower().strip(' ') for item in pdtb2rstdt.loc[i, "RST-DT (OLiA)"].split(',')]
        unidim = [item.lower().strip(' ') for item in pdtb2rstdt.loc[i, "RST-DT (UniDim)"].split(',')]
        pdtb2rstdt_dct[sense] = {}
        pdtb2rstdt_dct[sense]['iso'] = iso
        pdtb2rstdt_dct[sense]['olia'] = olia
        pdtb2rstdt_dct[sense]['unidim'] = unidim
        pdtb2rstdt_dct[sense]['all'] = list(set(iso).union(set(olia)).union(set(unidim)))
    
    # manually adding List and Sequence to Expansion.Conjunction
    pdtb2rstdt_dct['expansion.conjunction']['all'].extend(['list', 'sequence'])
    
    if not reverse:
        return pdtb2rstdt_dct
    
    rstdt2pdtb_dct = {}
    for key in pdtb2rstdt_dct:
        for rel in pdtb2rstdt_dct[key]['all']:
            if rel not in rstdt2pdtb_dct:
                rstdt2pdtb_dct[rel] = []
            rstdt2pdtb_dct[rel].append(key)

    return rstdt2pdtb_dct

def create_gum2pdtb(gum2rstdt_dct, rstdt2pdtb_dct):
    """
    take GUM -> RST-DT mapping and
    RST-DT -> PDTB mapping,
    and turn them into a single
    GUM -> PDTB mapping,
    while post-processing each dictionary.
    """
    gum2pdtb_dct = {}
    for gum_rel in gum2rstdt_dct:
        if gum_rel not in gum2pdtb_dct:
            gum2pdtb_dct[gum_rel] = []
        for rstdt_rel in gum2rstdt_dct[gum_rel]:
            if rstdt_rel not in rstdt2pdtb_dct:
                continue
            gum2pdtb_dct[gum_rel].extend(
                [simplify_pdtb_sense(sense) for sense in rstdt2pdtb_dct[rstdt_rel]]
                )
    
    # set-ify and then list-ify
    for gum_rel in gum2pdtb_dct:
        gum2pdtb_dct[gum_rel] = list(set(gum2pdtb_dct[gum_rel]))
    return gum2pdtb_dct


def create_dm_rst2pdtb(dm_rst_dct, dm2pdtb_dct, gum2pdtb_dct):    
    dms = sorted(list(dm_rst_dct.keys()))
    gum_rels = sorted(list(gum2pdtb_dct.keys()))
    dm_rst2pdtb_dct = dict()
    for dm in dms:  # fill in the table row by row
        for rel in gum_rels:  # fill in the row column by column
            dm_allowed = set(dm2pdtb_dct[dm])
            gum_allowed = set(gum2pdtb_dct[rel])
            allowed = dm_allowed.intersection(gum_allowed)
            dm_rst2pdtb_dct[(dm, rel)] = list(allowed)
    
    return dm_rst2pdtb_dct


def update_dm_rst2pdtb(url, dm_rst2pdtb_dct):
    disambiguation = pd.read_csv(url, keep_default_na=False)
    
    for i in range(len(disambiguation)):
        if disambiguation.loc[i, "DM"] == "":
            continue
        
        dm = disambiguation.loc[i, "DM"].lower().strip()
        rst = disambiguation.loc[i, "RST"].lower().strip()
        pdtb = []
        if disambiguation.loc[i, "proposed PDTB"]:
            pdtb = disambiguation.loc[i, "proposed PDTB"].lower().strip().split(', ')
        dm_rst2pdtb_dct[(dm, rst)] = pdtb
    
    return dm_rst2pdtb_dct


def update_gum2pdtb(gum2pdtb_dct, addition_list):
    for rst, pdtb in addition_list:
        gum2pdtb_dct[rst.strip()].append(pdtb.strip())
    return gum2pdtb_dct


def create_dm_pdtb2rst(dm_rst2pdtb_dct):
    dm_pdtb2rst_dct = dict()
    dm_rst = list(dm_rst2pdtb_dct.keys())
    for dm, rst in dm_rst:
        pdtbs = dm_rst2pdtb_dct[(dm, rst)]
        for pdtb in pdtbs:
            if (dm, pdtb) not in dm_pdtb2rst_dct:                
                dm_pdtb2rst_dct[(dm, pdtb)] = []
            dm_pdtb2rst_dct[(dm, pdtb)].append(rst)
    return dm_pdtb2rst_dct


def create_crosstable(dm_rst_dct, dm2pdtb_dct, gum2pdtb_dct):
    """
    take DM / RST frequency dictionary,
    DM -> PDTB mapping dictionary,
    and GUM -> PDTB mapping dictionary dictionary,
    and return a Pandas DataFrame
    """
    dms = sorted(list(dm_rst_dct.keys()))
    gum_rels = sorted(list(gum2pdtb_dct.keys()))
    ct = pd.DataFrame(index=dms, columns=gum_rels)
    dm_total = dict()  # to keep track of DM subtotal
    gum_rel_total = dict()  # to keep track of DM subtotal
    for dm in dms:  # fill in the table row by row
        for rel in gum_rels:  # fill in the row column by column
            dm_allowed = set(dm2pdtb_dct[dm])
            gum_allowed = set(gum2pdtb_dct[rel])
            allowed = dm_allowed.intersection(gum_allowed)
            freq = dm_rst_dct[dm][rel] if rel in dm_rst_dct[dm] else 0
            ct.loc[dm, rel] = str(freq) + " | " + re.sub(r"['\{\}]", "", str(allowed)) if\
                len(allowed) > 0 else freq
            # update the total
            if dm not in dm_total:
                dm_total[dm] = 0
            if rel not in gum_rel_total:
                gum_rel_total[rel] = 0
            dm_total[dm] += freq
            gum_rel_total[rel] += freq
    gum_rel_total_df = pd.DataFrame(np.array([gum_rel_total[rel] for rel in gum_rels]).reshape(1, 31),
                                columns=gum_rels, index=["Total"])
    dm_total = [sum(dm_total.values())]+[dm_total[dm] for dm in dms]
    dm_index = ['Total'] + dms
    dm_total_df = pd.DataFrame(dm_total, columns = ["Total"], index=dm_index)
    ct = pd.concat([gum_rel_total_df, ct])
    ct = pd.concat([dm_total_df, ct], axis=1)    
    return ct

def main():
    RS4_DIR = os.path.join('rst', 'rstweb')
    RST2PDTB_ADDITION_FP = os.path.join('mappings', 'rst2pdtb.tab')
    with open(RST2PDTB_ADDITION_FP) as f:
        rst2pdtb_addition = [row.split('\t') for row in f.readlines()]

    DM_RST_freq = dict()
    
    # create a cross table with DMs (row) and RST relations (column),
    # to be filled later
    for fn in os.listdir(RS4_DIR):
        fp_rs4 = os.path.join(RS4_DIR, fn)
        dm_rst_dct = update_DM_rst_dct(DM_RST_freq, fp_rs4)
    
    # URLs
    pdtb2rstdt_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS6ZdxcybILo765sqQ2DWKoAhVJUAlLrAq6G9-Lg5z_AYfg3QoPmr0WmWgecsGz5Y7FKZECtG5x9I5Y/pub?gid=273216568&single=true&output=csv"
    pdtb_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS6ZdxcybILo765sqQ2DWKoAhVJUAlLrAq6G9-Lg5z_AYfg3QoPmr0WmWgecsGz5Y7FKZECtG5x9I5Y/pub?gid=1103084500&single=true&output=csv"
    rstdt2gum_ta_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS6ZdxcybILo765sqQ2DWKoAhVJUAlLrAq6G9-Lg5z_AYfg3QoPmr0WmWgecsGz5Y7FKZECtG5x9I5Y/pub?gid=2051019438&single=true&output=csv"
    disambiguation = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTE74iPZb06R2dUTaM6XxYUhOcY30pjRxzQ2duClGWq6r1PqxCtLzLpmQLWz2lGdTeFZRcMhZhTkU6H/pub?gid=1259285212&single=true&output=csv"

    # create dictionaries
    dm2pdtb_dct = create_dm2pdtb(pdtb_url, cutoff=None)
    gum2rstdt_dct = create_rstdt2gum8(rstdt2gum_ta_url, reverse=True)
    rstdt2pdtb_dct = create_pdtb2rstdt(pdtb2rstdt_url, reverse=True)

    gum2pdtb_dct = create_gum2pdtb(gum2rstdt_dct, rstdt2pdtb_dct)
    # update rst -> pdtb mapping based on manual addition
    gum2pdtb_dct = update_gum2pdtb(gum2pdtb_dct, rst2pdtb_addition)

    dm_rst2pdtb_dct = create_dm_rst2pdtb(dm_rst_dct, dm2pdtb_dct, gum2pdtb_dct)    
    # update (dm, rst) -> pdtb mapping based on manual disambiguation
    dm_rst2pdtb_dct = update_dm_rst2pdtb(disambiguation, dm_rst2pdtb_dct)

    # create (dm, pdtb) -> rst based on (dm, rst) -> pdtb dictionary
    dm_pdtb2rst_dct = create_dm_pdtb2rst(dm_rst2pdtb_dct)
    
    # make two dictionaries json-serializable
    keys = list(dm_rst2pdtb_dct.keys())
    for key in keys:
        dm_rst2pdtb_dct['@'.join(key)] = dm_rst2pdtb_dct[key]
        del dm_rst2pdtb_dct[key]
    
    keys = list(dm_pdtb2rst_dct.keys())
    for key in keys:
        dm_pdtb2rst_dct['@'.join(key)] = dm_pdtb2rst_dct[key]
        del dm_pdtb2rst_dct[key]
    
    # make dm2pdtb simpler (no frequency)
    for dm in dm2pdtb_dct:
        dm2pdtb_dct[dm] = list(dm2pdtb_dct[dm].keys())
    # save dictionaries
    mappings = {'dm2pdtb': dm2pdtb_dct,
                'rst2pdtb': gum2pdtb_dct,
                'dm@rst2pdtb': dm_rst2pdtb_dct,
                'dm@pdtb2rst': dm_pdtb2rst_dct}
    with open(os.path.join("mappings.json"), 'w') as f:
        json.dump(mappings, f, indent=4)

#    with open(os.path.join("..", "data", "dm2pdtb.json"), 'w') as f:
#        json.dump(dm2pdtb_dct, f)
#    with open(os.path.join("..", "data", "gum2pdtb.json"), 'w') as f:
#        json.dump(gum2pdtb_dct, f)
    
    # create the crosstable
#    ct = create_crosstable(dm_rst_dct, dm2pdtb_dct, gum2pdtb_dct)
#    ct.to_csv(os.path.join("..", "data", "DM-RST-crosstable-nocutoff-1111.csv"))
#    return ct
# Some analyses

if __name__ == "__main__":
    main()

"""some analyses
ct = main()
total = 0
type_freq = 0
ambiguous_cells = []
for i in range(np.shape(ct)[0]):
    for j in range(np.shape(ct)[1]):
        cell = ct.iloc[i, j]
        if "," in str(cell):
            freq = int(str(cell).split("|")[0].strip())
            total += freq
            if freq > 0:
                PDTB_senses = str(cell).split("|")[1].strip()
                ambiguous_cells.append([ct.index[i], ct.columns[j], PDTB_senses, freq, ''])
                type_freq += 1

ct.columns[3]

pd.DataFrame(ambiguous_cells,
             columns = ['DM', 'RST', 'PDTB', 'freq', 'notes']
             ).to_csv(os.path.join('..', 'data', 'ambiguous_cells_nocutoff.csv'))
"""
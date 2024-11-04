"""
Scorer for tabular relation files with identical document names in two folders in format:

DOCNAME	TYPE	CONN	SENSE	RST	ARG1	ARG2	ARG1_IDS	ARG2_IDS	KEY NOTES
GUM_whow_cactus	explicit	and	expansion.conjunction	joint-list_m	has pads that look like beavertails ;	and yields red or purple flowers from spring to early summer .	[8]	[9]	9-8-joint-list_m    _
GUM_whow_cactus	implicit	and	expansion.conjunction	joint-other_m	The Beavertail Cactus ( Opunitia basilares ) , found primarily in the Mojave Desert and northwest Mexico ; can grow to be about 24 inches ( 60 cm ) high ; has pads that look like beavertails ; and yields red or purple flowers from spring to early summer .	Growing Beavertail can be done at any time of year by scattering seeds in a shady bed or , for faster results , planting cuttings in a mix of soil and sand and ensuring that they have a bit of water and plenty of sun .	[9]	[10, 11, 12, 13]	10-9-joint-other_m	_

...
"""
import os
from glob import glob
from collections import defaultdict
from argparse import ArgumentParser

ud_dev=["GUM_interview_cyclone","GUM_interview_gaming","GUM_news_iodine","GUM_news_homeopathic","GUM_voyage_athens","GUM_voyage_coron","GUM_whow_joke","GUM_whow_overalls","GUM_bio_byron","GUM_bio_emperor","GUM_fiction_lunre","GUM_fiction_beast","GUM_academic_exposure","GUM_academic_librarians","GUM_reddit_macroeconomics","GUM_reddit_pandas","GUM_speech_impeachment","GUM_textbook_labor","GUM_vlog_radiology","GUM_conversation_grounded","GUM_textbook_governments","GUM_vlog_portland","GUM_conversation_risk","GUM_speech_inauguration","GUM_court_loan","GUM_essay_evolved","GUM_letter_arendt","GUM_podcast_wrestling"]
ud_test=["GUM_interview_libertarian","GUM_interview_hill","GUM_news_nasa","GUM_news_sensitive","GUM_voyage_oakland","GUM_voyage_vavau","GUM_whow_mice","GUM_whow_cactus","GUM_fiction_falling","GUM_fiction_teeth","GUM_bio_jespersen","GUM_bio_dvorak","GUM_academic_eegimaa","GUM_academic_discrimination","GUM_reddit_escape","GUM_reddit_monsters","GUM_speech_austria","GUM_textbook_chemistry","GUM_vlog_studying","GUM_conversation_retirement","GUM_textbook_union","GUM_vlog_london","GUM_conversation_lambada","GUM_speech_newzealand","GUM_court_mitigation","GUM_essay_fear","GUM_letter_mandela","GUM_podcast_bezos"]
pdtb_path = "C:\\Uni\\Corpora\\PDTB\\pdtbMerge-v9-3\\gold"

no_rst = 0
murky_labels = ["background","other"]
level = 2


def shorten(label):
    label=label.lower()
    label = label.replace("expansion.","exp.").replace("comparison.","comp.").replace("contingency.","cont.").replace("temporal.","temp.").replace("expansion.","exp.").replace("attribution.","attr.").replace("contrast.","contr.").replace("cause.","caus.").replace("condition.","cond.").replace("concession.","conc.")
    label = label.replace("synchronous","synch").replace("negative","ng").replace("concession","conces").replace("condition","cond").replace("level-of-detail","lev-det")
    label = label.replace("instantiation","inst").replace("substitution","subs").replace("equivalence","equiv").replace("antithesis","antith").replace("result","res").replace("purpose","purp")
    label = label.replace("similarity","sim").replace("contrast","contr").replace("conjunction","conj").replace("disjunction","disj").replace("preparation","prep").replace("cause","caus").replace("exception","excpt")
    return label


def correct_murkey(gold_data, pred_data):
    gold_lines = gold_data.strip().split("\n")
    pred_lines = pred_data.strip().split("\n")
    murky_gold = []
    for line in gold_lines:
        if "\t" in line:
            fields = line.split("\t")
            if any([x in fields[4] for x in murky_labels]):
                murky_gold.append(line)

    out_pred = []
    for line in pred_lines:
        if "\t" in line:
            fields = line.split("\t")
            if any([x in fields[4] for x in murky_labels]):
                continue
        out_pred.append(line)
    out_pred += murky_gold
    return "\n".join(out_pred)

def read_rels(tsv, rels, spans, senses, genre_count, genre_senses, genre="all"):
    global no_rst
    lines = tsv.strip().split("\n")
    for l in lines[1:]:
        fields = l.split("\t")
        docname, rtype, conn, sense, rst, arg1, arg2, arg1_ids, arg2_ids, key = fields[:10]
        if "." in sense:
            sense = ".".join(sense.split(".")[:level])
        if rst.lower() == "none":
            no_rst+=1
        rels[rtype].add((docname,arg1,arg2,sense))
        spans[rtype].add((docname,arg1,arg2,rtype))
        senses[rtype].add((docname,rtype,sense,key))
        rels["all"].add((docname,arg1,arg2,sense))
        spans["all"].add((docname,arg1,arg2,rtype))
        senses["all"].add((docname,rtype,sense,key))
        if genre != "all":
            genre_count[genre] += 1
            genre_senses[genre][sense] += 1

    return rels, spans, senses, genre_count, genre_senses


def get_pdtb_stats(pdtb_dir):
    rels = defaultdict(int)
    senses = defaultdict(int)
    if not pdtb_dir.endswith(os.sep):
        pdtb_dir += os.sep
    pdtb_files = glob(pdtb_dir + "**" + os.sep + "wsj*",recursive=True)
    for file_ in pdtb_files:
        data = open(file_).read()
        for line in data.strip().split("\n"):
            if len(line)>0:
                cols = line.split("|")
                reltype = cols[0].lower()
                relname = cols[8]
                rels[reltype] += 1
                rels["all"] += 1
                senses[relname] += 1
    return rels, senses


parser = ArgumentParser()
parser.add_argument("-g", "--gold_dir", help="Directory with gold .tab files", default="output")
parser.add_argument("-p", "--pred_dir", help="Directory with predicted .tab files", default="output_wo_cache")
parser.add_argument("-t", "--test_only", help="Only score on UD test set", action="store_true")
parser.add_argument("-l", "--latex", help="Format the resulting table for Latex", action="store_true")
parser.add_argument("--pdtb", help="Also get PDTB stats, requires path to PDTB", action="store_true")
parser.add_argument("--correct_murky", help="Assume relations spawned by murky RST labels have been corrected", action="store_true")
opts = parser.parse_args()

gold_files = sorted(glob(opts.gold_dir + os.sep + "*.tab"))
pred_files = sorted(glob(opts.pred_dir + os.sep + "*.tab"))

gold_rels = defaultdict(set)
pred_rels = defaultdict(set)
gold_spans = defaultdict(set)
pred_spans = defaultdict(set)
gold_senses = defaultdict(set)
pred_senses = defaultdict(set)
relcount = defaultdict(int)
genre_senses = defaultdict(lambda :defaultdict(int))

for i, gold_file in enumerate(gold_files):
    docname = os.path.basename(gold_file).replace(".tab","")
    genre = docname.split("_")[1]
    if docname not in ud_test and opts.test_only:
        continue
    pred_file = pred_files[i]

    gold_data = open(gold_file).read()
    pred_data = open(pred_file).read()

    if opts.correct_murky:
        pred_data = correct_murkey(gold_data, pred_data)

    gold_rels, gold_spans, gold_senses, relcount, _ = read_rels(gold_data, gold_rels, gold_spans, gold_senses, relcount, {}, genre="all")
    pred_rels, pred_spans, pred_senses, relcount, genre_senses = read_rels(pred_data, pred_rels, pred_spans, pred_senses, relcount, genre_senses, genre=genre)


if opts.latex:
    tabsep = " & "
    double_tabsep = " & "
    line_end = " \\\\\n"
else:
    tabsep = "\t"
    double_tabsep = "\t\t"
    line_end = "\n"

subset = " - test set" if opts.test_only else " - whole corpus"

print("Level " + str(level) + " scores" + subset)
# Get P/R/F1 for each relation type
print("Relation scores (exact match)" + subset)
print(tabsep.join(["type\t","P","R","F1"]))
for rtype in sorted(gold_rels.keys(),key=lambda x:(x=="all",x)):
    tp = len(gold_rels[rtype].intersection(pred_rels[rtype]))
    fp = len(pred_rels[rtype] - gold_rels[rtype])
    fn = len(gold_rels[rtype] - pred_rels[rtype])

    p = tp / (tp + fp) if tp + fp > 0 else 0
    r = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * p * r / (p + r) if p + r > 0 else 0

    print(f"{rtype}{double_tabsep if len(rtype)<=7 else tabsep}{p:.4f}{tabsep}{r:.4f}{tabsep}{f1:.4f}")

print("\nSpan scores (incl. rel maj type but not sense)"+subset)
for rtype in sorted(gold_spans.keys(),key=lambda x:(x=="all",x)):
    tp = len(gold_spans[rtype].intersection(pred_spans[rtype]))
    fp = len(pred_spans[rtype] - gold_spans[rtype])
    fn = len(gold_spans[rtype] - pred_spans[rtype])

    p = tp / (tp + fp) if tp + fp > 0 else 0
    r = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * p * r / (p + r) if p + r > 0 else 0

    print(f"{rtype}{double_tabsep if len(rtype)<=7 else tabsep}{p:.4f}{tabsep}{r:.4f}{tabsep}{f1:.4f}",end=line_end)

print("\nSense scores (incl. rel maj type and sense but not exact span)"+subset)
for rtype in sorted(gold_senses.keys(),key=lambda x:(x=="all",x)):
    tp = len(gold_senses[rtype].intersection(pred_senses[rtype]))
    fp = len(pred_senses[rtype] - gold_senses[rtype])
    fn = len(gold_senses[rtype] - pred_senses[rtype])

    p = tp / (tp + fp) if tp + fp > 0 else 0
    r = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * p * r / (p + r) if p + r > 0 else 0

    print(f"{rtype}{double_tabsep if len(rtype)<=7 else tabsep}{p:.4f}{tabsep}{r:.4f}{tabsep}{f1:.4f}",end=line_end)
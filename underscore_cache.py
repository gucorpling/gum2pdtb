import re, sys, json, pathlib, os
from glob import glob

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = os.path.join(ROOT_DIR, 'data')

def underscore_file(filename):
    if filename.endswith(".tab"):
        text_fields = [5,6]  # tab format
    elif filename.endswith(".rels"):
        text_fields = [3,4,7,8]  # rels format
    elif filename.endswith(".jsonl"):
        text_fields = ["input","unit1_txt","unit2_txt"]  # jsonl format
    else:
        raise ValueError("Unknown file format")


    lines = open(filename).read().strip().split("\n")[1:]
    output = []

    if filename.endswith("jsonl"):
        for line in lines:
            data = json.loads(line)
            if "_reddit_" in line:
                for key in text_fields:
                    data[key] = re.sub(r'[^\s]', '_', data[key])
            output.append(json.dumps(data))
    else:
        for line in lines:
            if "\t" in line:
                fields = line.split("\t")
                if "_reddit_" in line:
                    for i in text_fields:
                        fields[i] = re.sub(r'[^\s]', '_', fields[i])
                    line = "\t".join(fields)
            output.append(line)

    with open(filename,"w",encoding="utf8",newline="\n") as outf:
        outf.write("\n".join(output))


if __name__ == '__main__':

    files = ["cached_rels.tab","connector_preds"]
    for f in files:
        if ".tab" in f:
            underscore_file(os.path.join(DATA_DIR, f))
        else:
            for file_ in glob(os.path.join(DATA_DIR, f, "*.jsonl")):
                underscore_file(os.path.join(DATA_DIR, f, file_))
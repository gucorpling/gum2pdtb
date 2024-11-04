from typing import List, Dict
import os, io
import json


ellipsis_marker = "<*>"

def format_range(tok_ids):
    # Takes a list of IDs and returns formatted string:
    # contiguous subranges of numbers are separated by '-', e.g. 5-24
    # discontinuous subranges are separated by ',', e.g. 2,5-24
    def format_subrange(subrange):
        if len(subrange) == 1:
            return str(subrange[0]+1)
        else:
            return str(min(subrange)+1) + "-" + str(max(subrange)+1)

    subranges = [[]]
    last = None
    for tid in sorted(tok_ids):
        if last is None:
            subranges[-1].append(tid)
        elif tid == last +1:
            subranges[-1].append(tid)
        else:
            subranges.append([tid])
        last = tid

    formatted = []
    for subrange in subranges:
        formatted.append(format_subrange(subrange))

    return ",".join(formatted)


def format_text(arg1_toks, toks):
    last = arg1_toks[0] - 1
    output = []
    for tid in sorted(arg1_toks):
        if tid != last + 1:
            output.append(ellipsis_marker)
        output.append(toks[tid].text)
        last = tid
    return " ".join(output)


def flat_tokens(tokens: List) -> List:
    return [token.text for token in tokens]


def output_file(output_path: str, rels: List, doc_state, format: str = "tab") -> None:
    if format == "rels":
        rows = ["\t".join(["doc","unit1_toks","unit2_toks","unit1_txt","unit2_txt","s1_toks","s2_toks","unit1_sent","unit2_sent","dir","rel_type","orig_label","label"])]
    else:
        rows = ["\t".join(['DOCNAME', 'TYPE', 'CONN', 'SENSE', 'RST', 'ARG1', 'ARG2', 'ARG1_IDS', 'ARG2_IDS', 'KEY', 'NOTES'])]
    for rel in rels:
        if format == "tab":
            rows.append("\t".join([str(x) for x in rel]))
        else:
            docname, reltype, conn, sense, rst_rel, arg1, arg2, arg1_ids, arg2_ids, key, notes = rel
            if sense.lower() in ["norel","entrel"]:  # Don't export these in accordance with DISRPT shared task setup
                continue
            direction = "1>2" if "arg1" in sense else "1<2"
            unit1_ids = arg1_ids if arg1_ids[0] < arg2_ids[0] else arg2_ids
            unit2_ids = arg2_ids if arg1_ids[0] < arg2_ids[0] else arg1_ids
            unit1_edus = [doc_state.edus[e] for e in unit1_ids]
            unit2_edus = [doc_state.edus[e] for e in unit2_ids]
            unit1_token_ids = [tid for edu in unit1_edus for tid in edu.tok_ids]
            unit2_token_ids = [tid for edu in unit2_edus for tid in edu.tok_ids]
            unit1_text = format_text(unit1_token_ids, doc_state.tokens)
            unit2_text = format_text(unit2_token_ids, doc_state.tokens)
            unit1_token_range = format_range(unit1_token_ids)
            unit2_token_range = format_range(unit2_token_ids)
            unit1_sents = [edu.sent_id for edu in unit1_edus]
            unit2_sents = [edu.sent_id for edu in unit2_edus]
            unit1_sents_tok_ids = [int(tok.doc_token_id) - 1 for tok in doc_state.tokens if tok.sent_id in unit1_sents]
            unit2_sents_tok_ids = [int(tok.doc_token_id) - 1 for tok in doc_state.tokens if tok.sent_id in unit2_sents]
            unit1_sents_text = format_text(unit1_sents_tok_ids, doc_state.tokens)
            unit2_sents_text = format_text(unit2_sents_tok_ids, doc_state.tokens)
            unit1_sents_tok_ids = format_range(unit1_sents_tok_ids)
            unit2_sents_tok_ids = format_range(unit2_sents_tok_ids)
            parts = sense.split(".")
            if len(parts) == 1:  # Match DISRPT format
                modified_sense = sense.lower()
            elif len(parts) > 1:
                modified_sense = parts[0].lower() + "." + parts[1].lower()
            row = [docname, unit1_token_range, unit2_token_range, unit1_text, unit2_text, unit1_sents_tok_ids, unit2_sents_tok_ids, unit1_sents_text, unit2_sents_text, direction, reltype, sense, modified_sense]
            rows.append("\t".join(row))

    with io.open(output_path, "w", encoding="utf8", newline="\n") as f:
        f.write("\n".join(rows).strip() + "\n")

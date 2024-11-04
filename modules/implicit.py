"""
@Shabnam @Wes
"""
import sys
import os
import re
from argparse import ArgumentParser
from modules.base import ConvertBase


class Implicit(ConvertBase):

    def __init__(self, data_dir, direct_mappings_dir, probs_mappings_dir, conn_preds_dir):
        super().__init__(data_dir, direct_mappings_dir, probs_mappings_dir, conn_preds_dir)
        self.banned_rst = ['elaboration-attribute_r', 'purpose-attribute_r', 'attribution-positive_r', 'attribution-negative_r', 'topic-question_r']

    def get_connectors(self, doc, rel):
        docname = doc.docname

        # disco preds are in linear order so smaller ID = arg1
        if rel.source.tok_ids[0] < rel.target.tok_ids[0]:
            arg1 = rel.source
            arg2 = rel.target
        else:
            arg1 = rel.target
            arg2 = rel.source

        # if intersentential, clip to sentence
        if arg1.sent_ids != arg2.sent_ids:
            span1 = arg1.head_edu_sent.plain_text
            span2 = arg2.head_edu_sent.plain_text
        else:  # if intrasentential, whole thing
            span1 = ' '.join([edu.text for edu in arg1.edus])
            span2 = ' '.join([edu.text for edu in arg2.edus])

        mapkey = (span1, span2)
        mapkey = (re.sub(r'[^\s]', '_', span1), re.sub(r'[^\s]', '_', span2))
        if mapkey in self.conn_preds[docname]:
            return self.conn_preds[docname][mapkey]
        else:
            # print("bad key", file=sys.stderr)
            return None
    def _get_connectors(self, doc, rel):
        """
        adapted from get_rel_probs in base.py
        returns a list of top5 connectors for a given relation
        """
        docname = doc.docname

        #actually we are using head_edu text as the key
        #raw_source, raw_target = rel.source.raw_text, rel.target.raw_text

        #not using anymore, wasn't capturing full sentence text in a few cases
        raw_source_old = " ".join([edu.text for edu in rel.source.edus])
        raw_target_old = " ".join([edu.text for edu in rel.target.edus])
        #
        #
        source_sent_id = rel.source.sent_ids[0]
        target_sent_id = rel.target.sent_ids[0]

        source_sent = doc.sents[source_sent_id]
        target_sent = doc.sents[target_sent_id]

        #fixed, should be entire setnence text now
        raw_source = source_sent.plain_text
        raw_target = target_sent.plain_text

        # print("Raw source old :", raw_source_old, file=sys.stderr)
        # print("Raw source sent:", raw_source, file=sys.stderr)
        # print("Raw target old :", raw_target_old, file=sys.stderr)
        # print("Raw target sent:", raw_target, file=sys.stderr)

        # print("Raw Source text for relation ---", raw_source, "\n", file=sys.stderr)
        # print("Raw Target text for relation ---", raw_target, "\n", file=sys.stderr)
        dir = rel.is_forward
        mapkey = (raw_source, raw_target, dir)
        reversed_mapkey = (raw_target, raw_source, not dir)
        # print("Hypothetical Map Key for connector predictions:", mapkey, "\n", file=sys.stderr)
        # print("Hypothetical Map Key for connector predictions:", reversed_mapkey, "\n", file=sys.stderr)

        if mapkey in self.conn_preds[docname]:
            return self.conn_preds[docname][mapkey]

        elif reversed_mapkey in self.conn_preds[docname]:
            return self.conn_preds[docname][reversed_mapkey]
        else:
            # print("bad key", file=sys.stderr)
            return None


    def convert(self, doc, rel):
        bad_key = False
        # copied in part from implicit.py module
        source_sent_ids, target_sent_ids = list(rel.source.sent_ids), list(rel.target.sent_ids)

        source_par_ids, target_par_ids = list(rel.source.par_ids), list(rel.target.par_ids)
        subtypes = [sig.subtype for sig in rel.signals]

        #source_sent_id = rel.source.sent_ids[0]
        source_sent_id = rel.source.head_edu_sent.sent_id
        #target_sent_id = rel.target.sent_ids[0]
        target_sent_id = rel.target.head_edu_sent.sent_id
        source_sent_type = doc.sents[source_sent_id].s_type
        target_sent_type = doc.sents[target_sent_id].s_type

        if rel.relname in self.banned_rst:
            return None
        elif "cache" in rel.pdtb_rels:
            return
        elif len(source_sent_ids) == 0 or len(target_sent_ids) == 0:
            #print("Source or target has no sentence ids. This must be an error?", file=sys.stderr)
            return None
        elif source_sent_ids[0] == target_sent_ids[0]:
            #print("Source and target sentence IDs are the same sentence. Must not be implicit.", file=sys.stderr)
            return None
        elif abs(int(source_sent_ids[0]) - int(target_sent_ids[0])) > 1:
            #print("Sentences are not adjacent. Must not be implicit", file=sys.stderr)
            return None
        elif "dm" in subtypes:
            # print("Explicit DM Signal found. Must not be implicit", file=sys.stderr)
            return None
        elif "orphan" in subtypes:
            # print("Orphan signal found. Must not be implicit", file=sys.stderr)
            return None
        elif source_par_ids != target_par_ids:
            # print("Source and target paragraph IDs are not adjacent. Must not be impicit", file=sys.stderr)
            return None
        elif source_sent_type in ["frag","intj"]:
            # print("Source sent is not a verbal sentence. Disregarded.", file=sys.stderr)
            return None
        elif target_sent_type in ["frag","intj"]:
            # print("Target sent is not a verbal sentence. Disregarded", file=sys.stderr)
            return None

        elif len(source_sent_ids) > 1:
            # print("More than 1 source sentence ID for this relation. Since implicit relations are only between two adjacent sentences, this relation is not implicit", file=sys.stderr)
            pass
            #return None
        elif len(target_sent_ids) > 1:
            #print(
            #    "More than 1 target sentence ID for this relation. Since implicit relations are only between two adjacent sentences, this relation is not implicit",
            #    file=sys.stderr)
            pass
            #return None

            
        #print("Sent_IDs", source_sent_ids[0], target_sent_ids[0], file=sys.stderr)


        #ids for dm set to -1 because there is no signalling dm
        # print("Source text:", rel.source.raw_text, file=sys.stderr)
        # print("Source tok ids", rel.source.tok_ids, file=sys.stderr)
        # print("Target text:", rel.target.raw_text, file=sys.stderr)
        # print("Target tok ids:", rel.target.tok_ids, file=sys.stderr)

        ids = [-1]
        #print("Relation object:", rel, file=sys.stderr)
        # for sig in rel.signals:
        #     if sig.subtype not in ['dm', 'orphan']:
        #         continue  # explicit = dm or orphan
        #     dm = ' '.join([tok.text for tok in sig.toks]).lower()
        #     ids = sig.tok_ids
        #     rst = rel.relname[:-2]


        # print("SENT IDS", rel.source.sent_ids, rel.target.sent_ids, file=sys.stderr)
        # print("SENT", doc.sents[rel.source.sent_ids[0]])
        # print("SENT toks", doc.sents[rel.source.sent_ids[0]].plain_text)
        connectors = self.get_connectors(doc, rel)

        #print("CONNECTORS:",connectors, file=sys.stderr)

        #TODO - fix situations where there are no predicted connectors
        if not connectors: #if there is no connectors, aka if the tokens don't align for the connector prediction
            # print(doc.docname, connectors, file=sys.stderr)
            #
            # print("no connectors", file=sys.stderr)
            #print("bad key", file=sys.stderr)
            bad_key = True
            connectors = ["BAD CONN"] #if there are no predicted connectors, forced to choose norel

        all_probs = self.get_rel_probs(doc.docname, rel, doc.sents)
        rst = rel.relname[:-2]

        #loop through the connectors. If dm + rst is a valid 2pdtb key, stop and choose that connector
        #else continue looping through the top5. If none of the top5 connectors work, return norel
        found_conn = False
        best_conn = ""
        for conn in connectors:
            #print("LOOPING THE CONNECTORS", conn, file=sys.stderr)
            if not found_conn:
                try:
                    pdtbs = self.direct_mappings['dm@rst2pdtb']['@'.join([conn, rst])]
                    assert pdtbs
                    #print("THE CONNECTOR", conn, pdtbs, file=sys.stderr)
                    found_conn = True
                    best_conn = conn
                    #print("BEST CONNECTOR:",best_conn, file=sys.stderr)

                except:
                   # print("bad mapping", conn, file=sys.stderr)
                    pass

        if not found_conn:
            # if none of the top5 dm + rst spawn a pdtb relation, return norel
            pdtbs = ["NoRel"]

        else:
            #make sure we actually chose a connector
            # print(found_conn, file=sys.stderr)
            # print(best_conn, file=sys.stderr)
            assert best_conn
            dm = best_conn #best_conn is top predicted dm
            pdtbs = self.direct_mappings['dm@rst2pdtb']['@'.join([best_conn, rst])]
            # print(dm, pdtbs, file=sys.stderr)

        hyp_conn = connectors[0]
        # try:
        #     pdtb = self.direct_mappings['dm@rst2pdtb']['@'.join([dm, rst])]
        # except:
        #     return

        if len(pdtbs) == 1:  #ideal case, 1 possible pdtb tag
            pdtb = pdtbs[0]
            if pdtb == "NoRel":
                rel.pdtb_rels['implicit'].append(('norel', "NoRel", [-1], "_"))
            else:
                rel.pdtb_rels['implicit'].append(('implicit', pdtb, ids, dm))

        else:
            assert len(pdtbs) > 1
            #below copied from implicit.py
            if len(pdtbs) == 0:  # if no intersection, shouldn't actually apply for implicit bc we will declare NoRel
                # TODO: get union of RST & DM, rank?
                pdtbs = self.direct_mappings['dm2pdtb'].get(dm, []) + \
                        self.direct_mappings['rst2pdtb'].get(rst, [])

            elif len(pdtbs) > 1:
                pass

            if all_probs:  # if the disco preds are available (won't need this once fixed)
                probs = [[pdtb_rel, all_probs.get(pdtb_rel, 0)] for pdtb_rel in
                         pdtbs]  # TODO get method in case of PDTB rel name discrepancies

                pdtb = sorted(probs, key=lambda x: x[1], reverse=True)[0][0]

            else:  # if disco preds are NOT available - for yilun and janet to fix
                pdtb = pdtbs[0]  # just pick the first one in the list

            if pdtb == "NoRel":
                dm = "_"
            reltype = 'implicit' if pdtb != "NoRel" else 'norel'

            rel.pdtb_rels['implicit'].append((reltype, pdtb, ids, dm))

        #print("OUTPUT:", rel.pdtb_rels["implicit"], file=sys.stderr)
        # if len(pdtb) > 1:
        #     # TODO: rank
        #     pdtb = pdtb[0]  # placeholder
        # if pdtb[0] not in rel.pdtb_rels['implicit']:
        #     rel.pdtb_rels['implicit'].append(pdtb[0])
        if bad_key:
            return 1


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-i", help="data dir", default='../data')
    parser.add_argument("-d", help="example docname", default='GUM_academic_art')
    args = parser.parse_args()

    data_dir = args.i
    docname = args.d
    conllu_dir = os.path.join(data_dir, "dep", docname+".conllu")
    rs4_dir = os.path.join(data_dir, "rst", "rstweb", docname+".rs4")
    direct_mappings_dir = os.path.join(data_dir, 'mappings.json')
    probs_mappings_dir = os.path.join(data_dir, 'discodisco_preds')
    conn_pred_dir = os.path.join(data_dir, "connector_preds")

    implicit_module = Implicit(data_dir, direct_mappings_dir, probs_mappings_dir, conn_pred_dir)
    doc = implicit_module.process_files(conllu_dir, rs4_dir, docname)

    for node_id, rel in doc.rels.items():
        implicit_module.convert(doc, rel)
        implicit_module.output(docname, node_id, rel, 'implicit')

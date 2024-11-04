"""
@Jessica
"""
import os
from argparse import ArgumentParser
#from base import ConvertBase
from modules.base import ConvertBase


class AltlexC(ConvertBase):
    def __init__(self, data_dir, direct_mappings_dir):
        super().__init__(data_dir, direct_mappings_dir)
        self.direct_mappings = self.direct_mappings['rst2pdtb']
        self.doc_state = None

    def set_doc_state(self, doc_state):
        self.doc_state = doc_state

    def convert(self, doc, rel):
        self.extract_auxiliary_inversion_from_conllu(rel)
        self.extract_so_that_from_conllu(rel)
        self.extract_such_from_conllu(rel)
        # TODO: too X that/for (but seems to be unattested in GUM10)
        #self.extract_too_from_conllu(doc.parsed_conllu, rel)
        self.extract_ssim_from_conllu(rel)
        # TODO: pred_inv_as (but seems to be unattested in GUM10)
        #self.extract_pred_inv_from_conllu(doc.parsed_conllu, rel)
        self.extract_as_inv_from_conllu(rel)
        self.extract_inf_from_conllu(rel)
        self.extract_coord_from_conllu(doc.parsed_conllu, rel)
        self.extract_participle_advcl(rel)

    def extract_too_advs(self, sentence_tokens, start_token_id):
        toos = []

        for i in range(len(sentence_tokens)):
            token = sentence_tokens[i]
            if token["form"] == "too":
                if i > 0 and i < len(sentence_tokens) - 1:
                    next_token = sentence_tokens[i + 1]
                    if next_token["xpos"] == "JJ" or next_token["xpos"] == "RB":
                        start_span = start_token_id + i
                        end_span = start_token_id + i + 1
                        too = (
                            (start_span, end_span),
                            f"{token['form']} {next_token['form']}",
                            " ".join([token["form"] for token in sentence_tokens]),
                            start_token_id
                        )
                        toos.append(too)

        return toos

    def extract_so_sims(self, sentence_tokens, start_token_id):
        ssims = []

        for i in range(len(sentence_tokens)):
            token = sentence_tokens[i]
            if token["form"] == "so":
                if i > 0 and i < len(sentence_tokens) - 1:
                    next_token = sentence_tokens[i + 1]
                    if next_token["form"] == "is":
                        start_span = start_token_id + i
                        end_span = start_token_id + i + 1
                        ssim = (
                            (start_span, end_span),
                            f"{token['form']} {next_token['form']}",
                            " ".join([token["form"] for token in sentence_tokens]),
                            start_token_id
                        )
                        ssims.append(ssim)

        return ssims

    def extract_pred_inversion(self, sentence_tokens, start_token_id):
        pinvs = []

        for i in range(len(sentence_tokens)):
            current_token = sentence_tokens[i]
        
        # Check if the current token is an auxiliary verb indicating inversion
        if current_token["deprel"] == "aux":
            if i < len(sentence_tokens) - 2:
                next_token = sentence_tokens[i + 1]
                context_token = sentence_tokens[i + 2]

                # Check if the context token is a subject noun
                if context_token["deprel"] == "nsubj":
                    start_span = start_token_id + i
                    end_span = start_token_id + i + 3
                    
                    # Construct the predicate inversion text
                    pinv_text = " ".join(token["form"] for token in sentence_tokens[i:i+3])
                    sentence_text = " ".join(token["form"] for token in sentence_tokens)
                    
                    predicate_inversions.append((
                        (start_span, end_span),
                        pinv_text,
                        sentence_text,
                        start_token_id
                    ))
            elif i < len(sentence_tokens) - 1 and current_token["form"] == "do" and sentence_tokens[i+1]["form"] == "not":
                if i < len(sentence_tokens) - 3:
                    third_token = sentence_tokens[i + 2]

                    # Check if the third token is a subject noun
                    if third_token["deprel"] == "nsubj":
                        start_span = start_token_id + i
                        end_span = start_token_id + i + 4
                        
                        # Construct the predicate inversion text
                        pinv_text = " ".join(token["form"] for token in sentence_tokens[i:i+4])
                        sentence_text = " ".join(token["form"] for token in sentence_tokens)
                        
                        predicate_inversions.append((
                            (start_span, end_span),
                            pinv_text,
                            sentence_text,
                            start_token_id
                        ))
        return pinvs

    def extract_infinitives(self, sentence_tokens, start_token_id):
        infs = []
        for i in range(len(sentence_tokens)):
            prev_token = sentence_tokens[i - 1] if i > 0 else None
            token = sentence_tokens[i]
            if token["lemma"] == "to" and token["deprel"] == "mark":
                if prev_token is not None:
                    if prev_token["lemma"] != "order":  # Make sure we don't include "in order to" (since that is an explicit DM, not AltLexC)
                        start_span = start_token_id + i
                        end_span = start_token_id + i + 1
                        inf = (
                            (start_span, end_span),  
                            {token['form']},
                            " ".join([token["form"] for token in sentence_tokens]),  
                            start_token_id  
                        )
                        infs.append(inf)
        return infs

    def extract_conj(self, sentence_tokens, start_token_id):
        coord = []
        # Find the root token
        root_token = next((token for token in sentence_tokens if token["deprel"] == "root"), None)
        
        if root_token is not None:
            nsubj_token = next((prev_token if i > 0 and prev_token["deprel"] in ["amod", "det", "nmod:poss", "cc", "discourse", "mark"] else token for i, (prev_token, token) in enumerate(zip([None] + sentence_tokens[:-1], sentence_tokens)) if token["head"] == root_token["id"] and (token["deprel"] in ["nsubj", "nsubj:pass", "csubj"] or any(child["deprel"] in ["nsubj", "nsubj:pass", "csubj"] for child in sentence_tokens if child["head"] == token["id"]))), None)
            last_conj_token = None
            and_token = None 
            preceding_token = None
            for token in sentence_tokens:
                if (
                    token["deprel"] == "conj" 
                    and int(token["head"]) == int(root_token["id"]) 
                ):
                    if preceding_token is not None and preceding_token["form"].lower() not in ["and", "or", "but"]:
                        last_conj_token = token
                        break  # Exit the loop once we find the last conjunct
                preceding_token = token
            
            # If a "conj" token is found, find the first punctuation token after it
            if last_conj_token is not None:
                and_token = None
                found_last_conj = False
                for token in sentence_tokens:
                    if found_last_conj and token["form"].lower() == "and":
                        and_token = token
                        break
                    if token == last_conj_token:
                        found_last_conj = True
           
            # If both last_conj_token and punct_token are found, construct the spans
            if and_token is not None:
                start_span = int(nsubj_token["id"]) if nsubj_token else int(root_token["id"])
                end_span = int(and_token["id"])

                # Check all tokens between root_token and last_conj_token for "and", "or", or "but"
                valid_conjuncts = all(
                    token["form"].lower() not in ["and", "or", "but"]
                    for token in sentence_tokens[start_span:end_span]
                    if token not in (nsubj_token, and_token)
                )

                if valid_conjuncts:
                    # Extract the forms of tokens between the root and last conj token (excluding root and last_conj_token)
                    between_toks = [
                        token["form"]
                        for token in sentence_tokens[start_span:end_span]
                        if token not in (nsubj_token, and_token)
                    ]

                    sentence_text = " ".join(token["form"] for token in sentence_tokens)
                    
                    subj_form = nsubj_token['form'] if nsubj_token else ''
                    conj_form = last_conj_token['form'] if last_conj_token else ''
                    co = (
                        (start_span + start_token_id -1, end_span + start_token_id-1),
                        f"{subj_form} {' '.join(between_toks)}",
                        sentence_text,
                        start_token_id
                    )
                    coord.append(co)

        return coord

    def extract_auxiliary_inversion_from_conllu(self, rel):
        if rel.relname == "contingency-condition_r":
            head_edu = self.doc_state.edus[int(rel.head_edu)]
            sent = self.doc_state.sents[head_edu.sent_id]
            edu_head_tok = sent.toks[head_edu.head_toknum - 1]
            if edu_head_tok.head == "0":
                return
            parent = sent.toks[int(edu_head_tok.head) - 1]
            if any(["Conditional" in x and "SubjVerbInversion" in x for x in parent.cxns]):
                # Matched conditional inversion, find the inverted aux
                children = [t for t in sent.toks if t.head == edu_head_tok.token_id]
                for c in children:
                    if c.lemma in ["have","should"]:
                        rel.pdtb_rels["altlexc"].append(("AltLexC","contingency.condition",[int(c.doc_token_id)],c.text.lower()))
                        return
                raise IOError("Sentence contains SubjVerbInversion but no have/should child!")

    def extract_so_that_from_conllu(self, rel):
        """
        So ADJ, that ... (Contingency.Cause.Result)
        """

        if rel.relname.startswith("causal-"):
            head_edu = self.doc_state.edus[int(rel.head_edu)]
            sent = self.doc_state.sents[head_edu.sent_id]
            for i, tok in enumerate(sent.toks):
                if "CausalExcess" in tok.cxns:
                    so = sent.toks[i-1]
                    rel.pdtb_rels["altlexc"].append(("AltLexC", "Contingency.Cause.Result", [int(so.doc_token_id)], so.text.lower()))
                    break
        return


    def extract_such_from_conllu(self, rel):
        """
        Such NP, that ... (Contingency.Cause.Result)
        """
        if rel.relname.startswith("causal-"):
            head_edu = self.doc_state.edus[int(rel.head_edu)]
            sent = self.doc_state.sents[head_edu.sent_id]
            for i, tok in enumerate(sent.toks):
                if "SuchNThat" in tok.cxns:
                    children = [t for t in sent.toks if t.head == tok.token_id]
                    such = [t for t in children if t.lemma == "such"][0]
                    rel.pdtb_rels["altlexc"].append(("AltLexC", "contingency.cause.result", [int(such.doc_token_id)], such.text.lower()))
                    break
        return

    def extract_too_from_conllu(self, data, rel):
        """
        Too ADV, that/for X to Y ... (Contingency.Cause.Result)
        """

        rst_rel_text_l = []

        if rel.relname in ["purpose-goal_r","causal-cause_r","causal-result_r"]:
            rst_rel_text = rel.node.text
            rst_rel_text_l.append(rst_rel_text)
        rst_rel_text_l = [item for item in rst_rel_text_l if item != ""]

        toos = []
        sent_list = []
        start_token_id = 1

        for sentence in data:
            sentence_tokens = [token for token in sentence]
            to = self.extract_too_advs(sentence_tokens, start_token_id)
            toos.extend(to)
            start_token_id += len(sentence_tokens)

        for token_span, to, sentence, sentence_start_id in toos:
            sent_list.append(token_span + (to, sentence))
        sent_list = [x + (self.direct_mappings["purpose-goal"][0],) for x in sent_list] #contingency.cause.result
        modified_list = [(last,) + tuple(rest) for *rest, last in sent_list]

        output = [j for j in modified_list if any(i in j[4] for i in rst_rel_text_l)]
        res1 = [['altlexc', item[0], [item[1], item[2]], item[3]] for item in output]
        if res1:
            res = res1[0]
            return res

    def extract_ssim_from_conllu(self, rel):
        """
        ... so (too) ... (Comparison.Similarity)
        """

        if rel.relname.startswith("joint-list"):
            head_edu = self.doc_state.edus[int(rel.head_edu)]
            sent = self.doc_state.sents[head_edu.sent_id]
            for i, tok in enumerate(head_edu.tokens):
                if "Expansion-SubjVerbInversion-So" in tok.cxns:
                    children = [t for t in sent.toks if t.head == tok.token_id]
                    so = [t for t in children if t.lemma == "so"][0]
                    rel.pdtb_rels["altlexc"].append(("AltLexC", "expansion.conjunction", [int(so.doc_token_id)], so.text.lower()))
                    break
        return

    def extract_pred_inv_from_conllu(self, data, rel):
        """
        ADJ as NP VP, ... (Comparison.Concession), e.g. "Crude as they were..."
        """

        rst_rel_text_l = []
        if rel.relname == "adversative-concession_r":
            rst_rel_text = rel.node.text
            rst_rel_text_l.append(rst_rel_text)
        rst_rel_text_l = [item for item in rst_rel_text_l if item != ""]

        pinvs = []
        sent_list = []
        start_token_id = 1

        for sentence in data:
            sentence_tokens = [token for token in sentence]
            pinv = self.extract_pred_inversion(sentence_tokens, start_token_id)
            pinvs.extend(pinv)
            start_token_id += len(sentence_tokens)

        for token_span, pinv, sentence, sentence_start_id in pinvs:
            sent_list.append(token_span + (pinv, sentence))
        sent_list = [x + (self.direct_mappings["adversative-concession"][0],) for x in sent_list] #comparison.concession
        modified_list = [(last,) + tuple(rest) for *rest, last in sent_list]

        output = [j for j in modified_list if any(i in j[4] for i in rst_rel_text_l)]
        res1 = [['altlexc', item[0], [item[1], item[2] - 1], item[3]] for item in output]
        if res1:
            res = res1[0]
            return res        

    def extract_as_inv_from_conllu(self, rel):
        """
        ... as is/does/was ... (Comparison.Similarity)
        """

        if rel.relname.startswith("joint-list") or rel.relname.startswith("elaboration-additional"):
            head_edu = self.doc_state.edus[int(rel.head_edu)]
            sent = self.doc_state.sents[head_edu.sent_id]
            for i, tok in enumerate(head_edu.tokens):
                if "Expansion-SubjVerbInversion-As" in tok.cxns:
                    children = [t for t in sent.toks if t.head == tok.token_id]
                    as_tok = [t for t in children if t.lemma == "as"][0]
                    rel.pdtb_rels["altlexc"].append(("AltLexC", "comparison.similarity", [int(as_tok.doc_token_id)], as_tok.text.lower()))
                    break
        return
    
    def extract_inf_from_conllu(self, rel):
        """
        Purpose to-infinitives without a connective like "in order";
        forbid if explicit relations already in list
        """
        if rel.relname.startswith("purpose-goal") and len(rel.pdtb_rels["explicit"]) == 0:
            head_edu = self.doc_state.edus[int(rel.head_edu)]
            sent = self.doc_state.sents[head_edu.sent_id]
            edu_head_tok = sent.toks[head_edu.head_toknum - 1]
            children = [t for t in sent.toks if t.head == edu_head_tok.token_id]
            for tok in children:
                if tok.pos == "TO":
                    rel.pdtb_rels["implicit"].append(("implicit", "contingency.purpose.arg2-as-goal", [], "in order"))
                    break
        return

    def extract_coord_from_conllu(self, data, rel):
        if rel.relname.startswith("joint") and len(rel.pdtb_rels["explicit"]) == 0 and not any([s.subtype in ["dm","orphan"] for s in rel.signals]):
            head_edu = self.doc_state.edus[int(rel.head_edu)]
            target_edu = self.doc_state.edus[int(rel.dep_parent)]
            if head_edu.head_func == "conj" and head_edu.sent_id == target_edu.sent_id:
                sent = self.doc_state.sents[head_edu.sent_id]
                edu_head_tok = sent.toks[head_edu.head_toknum - 1]
                children_funcs = [t.deprel for t in sent.toks if t.head == edu_head_tok.token_id]
                if head_edu.head_pos.startswith("V") or "cop" in children_funcs:
                    # This is a verbal (or copula pred) EDU which is coordinate but not explicitly signaled via and/or/then
                    conn = "or" if "disjunction" in rel.relname else "and"
                    label = "expansion.disjunction" if "disjunction" in rel.relname else "expansion.conjunction"
                    if "sequence" in rel.relname:
                        conn = "then"
                        label = "temporal.asynchronous.precedence"
                    rel.pdtb_rels["implicit"].append(("implicit", label, [], conn))

    def extract_participle_advcl(self, rel):
        """
        Pariticipial adjuncts as intrasentential implicits (v3 guidelines, p.33)
        """

        if len(rel.pdtb_rels["explicit"]) > 0 or len(rel.pdtb_rels["implicit"]) > 0:
            return

        mapping = {
            "purpose-goal_r": ("with the purpose of","contingency.purpose"),
            "mode-manner_r": ("by","expansion.manner"),
            "mode-means_r": ("by","expansion.manner"),
            "context-circumstance_r": ("when", "temporal.asynchronous.succession"),
            "causal-result_r": ("thus", "contingency.cause.result"),  # Restrict to result as second arg in text order
            "contingency-condition_r": ("if","contingency.condition"),
            "causal-cause_r": ("as a result of", "contingency.cause.reason"),  # add "being" if VBN
            "adversative-antithesis_r": ("instead", "expansion.substitution"),  # add "of" if first arg in text order
            "elaboration-additional_r": ("specifically","expansion.level-of-detail")
        }
        if rel.relname not in mapping:
            return

        if rel.source.edus[0].xpos[:3] not in ["VBG","VBN"]:  # Must start with bare participle
            return
        if not rel.source.edus[0].deprels.startswith("advcl"):  # Must start with bare participle
            return
        if rel.source.edus[0] != rel.source.head_edu[0]:  # The initial EDU must also be a head EDU, no premodifiers
            return

        conn, sense = mapping[rel.relname]

        # Determine direction and add any necessary words
        if rel.source.tok_ids[0] < rel.target.tok_ids[0]:  # src before target
            if rel.relname == "adversative-antithesis_r":
                conn = conn + "of"
            elif rel.relname == "causal-result_r":
                return  # Only allow result implicit 'thus' as second arg in text order
        if rel.relname == "causal-cause_r" and rel.source.edus[0].xpos[:3] == "VBN":
            conn = conn + " being"

        rel.pdtb_rels["implicit"].append(("implicit", sense, [], conn))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-i", help="data dir", default='../data')
    parser.add_argument("-d", help="example docname", default='GUM_fiction_moon')
    args = parser.parse_args()

    data_dir = args.i
    docname = args.d
    conllu_dir = os.path.join(data_dir, "dep", docname+".conllu")
    rs4_dir = os.path.join(data_dir, "rst", "rstweb", docname+".rs4")
    direct_mappings_dir = os.path.join(data_dir, 'mappings.json')

    altlexc_module = AltlexC(data_dir, direct_mappings_dir)
    doc = altlexc_module.process_files(conllu_dir, rs4_dir, docname)
    altlexc_module.set_doc_state(doc)

    for node_id, rel in doc.rels.items():
        altlexc_module.convert(doc, rel)
        altlexc_module.output(docname, node_id, rel, 'altlexc')
        altlexc_module.output(docname, node_id, rel, 'implicit')

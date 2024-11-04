import argparse
import os
from process import read_file
from convert import Converter
from utils import output_file
from modules.cache import Cache
from modules.hypophora import Hypophora
from modules.explicit import Explicit
from modules.implicit import Implicit
from modules.altlex import Altlex
from modules.altlexC import AltlexC
from modules.entrel import EntRel
from modules.norel import NoRel
from argspan_ordering import order_rel_args, remove_duplicates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", help="data dir", default='./data')
    parser.add_argument("-o", help="output dir", default="./output")
    parser.add_argument("-d", help="document name or all if None", default=None)
    parser.add_argument("--cache", help="[full, filtered, none]: 'full' uses all human correction files, 'filtered' filters out the corrections that were only applied to test set, 'none' does not use any human correction files.", choices=["full", "filtered", "none"], default="full")
    parser.add_argument("--format", choices=["tab","rels"], help="output format", default="tab")
    args = parser.parse_args()

    data_dir = args.i
    output_dir = args.o

    # read json mapping
    disco_pred_dir = os.path.join(data_dir, 'discodisco_preds')
    explicit_mapping_dir = os.path.join(data_dir, 'mappings.json')
    # TODO: replace this with discodisco inference

    conn_pred_dir = os.path.join(data_dir, "connector_preds")


    # initialize conversion modules
    MODULES = {
        'cache': Cache(data_dir, explicit_mapping_dir, disco_pred_dir, filter=args.cache),
        'hypophora': Hypophora(data_dir, explicit_mapping_dir, disco_pred_dir),
        'explicit': Explicit(data_dir, explicit_mapping_dir, disco_pred_dir),
        'implicit': Implicit(data_dir, explicit_mapping_dir, disco_pred_dir, conn_pred_dir),
        'entrel' : EntRel(data_dir, explicit_mapping_dir, disco_pred_dir),
        'altlex': Altlex(data_dir, explicit_mapping_dir, disco_pred_dir),
        'altlexc': AltlexC(data_dir, explicit_mapping_dir)
    }
    norel = NoRel()

    # process each doc
    conllu_dir = os.path.join(data_dir, "dep")
    rs4_dir = os.path.join(data_dir, "rst", "rstweb")
    for doc_id, conllu_name in enumerate(os.listdir(conllu_dir)):
        if args.d is not None:
            if args.d not in conllu_name:
                continue
        docname = conllu_name.replace(".conllu", "")
        print(docname)

        # process two files (conllu, rs4) and create a document state to store sentences, relations, edus, and spans
        doc_state = read_file(os.path.join(conllu_dir, conllu_name), os.path.join(rs4_dir, docname+".rs4"), docname)

        output = []
        doc_converter = Converter(doc_state, MODULES)

        # Give cache and altlexc modules the current doc state
        doc_converter.modules["cache"].set_doc_state(doc_state)
        doc_converter.modules["altlexc"].set_doc_state(doc_state)

        # Run conversion cascade for each input relation
        for node_id, rel in doc_state.rels.items():
            doc_converter.convert(rel, cache=args.cache)
            ordered = order_rel_args(rel,doc_state)
            if ordered is not None:
                if len(ordered) > 0:
                    output.extend(ordered)

        # Catch remaining NoRel cases
        output += norel.convert(doc_state)

        # Apply relations from cache module (potentially overwrites other assignments)
        for rel in MODULES["cache"].additional_rels[docname]:
            ordered = order_rel_args(rel, doc_state)
            if ordered is not None:
                if len(ordered) > 0:
                    output.extend(ordered)

        output = remove_duplicates(output)

        output.sort(key=lambda x: min(set(x[7]).union(x[8])))  # Order by lowest EDU ID

        # output
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        extension = "rels" if args.format == "rels" else "tab"
        output_file(os.path.join(output_dir, docname + "." + extension), output, doc_state, format=args.format)


if __name__ == "__main__":
    main()

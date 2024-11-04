# gum2pdtb
This repository is to reproduce the data presented in the [corpling lab](https://gucorpling.org/corpling/index.html)'s EMNLP paper "GDTB: Genre Diverse Data for English Shallow Discourse Parsing across Modalities, Text Types, and Domains". [You can find the preprint here](https://arxiv.org/abs/2411.00491)!

## Setting up the Environment
```
$ conda create -n gum2pdtb python=3.10
$ conda activate gum2pdtb
$ pip install -r requirements.txt
```

## Restoring Reddit Data
For copyright reasons, we have replaced all Reddit texts with underscores. To restore them, please run the following command:
```
$ python restore.py
```
Please kindly note that, you are solely responsible for downloading Reddit data and that you may only use it for non-commercial purposes.

## Conversion
Please run the following command to convert GUM to PDTB. The `full` argument will make sure that the pipeline reads the manual correction files (described in more detail in the paper). 
```
$ python main.py -o output --cache full --format tab
```

## Reproducing the Results from the Paper
To reproduce the corpus quality statistics (Table 3), create another version of the data by passing the `filtered` argument, and then run `score.py` with the `-t` flag to only evaluate the test split.
```
$ python main.py -o output_wo_cache --cache filtered --format tab
$ python score.py -t
```
If everything worked, you should get the same score as shown in Table 3 (shown below):
```
Level 2 scores - test set
Relation scores (exact match) - test set
type            P       R       F1
altlex          0.9500  0.7600  0.8444
altlexc         1.0000  1.0000  1.0000
entrel          0.7593  0.8913  0.8200
explicit        0.9812  0.9874  0.9843
hypophora       0.8750  0.8537  0.8642
implicit        0.8784  0.8205  0.8485
norel           0.7887  0.9180  0.8485
all             0.9277  0.9161  0.9218

Span scores (incl. rel maj type but not sense) - test set
altlex          0.9500  0.7600  0.8444
altlexc         1.0000  1.0000  1.0000
entrel          0.7778  0.9130  0.8400
explicit        0.9935  1.0000  0.9967
hypophora       0.8750  0.8537  0.8642
implicit        0.9824  0.9176  0.9489
norel           0.7887  0.9180  0.8485
all             0.9678  0.9554  0.9616

Sense scores (incl. rel maj type and sense but not exact span) - test set
altlex          0.9500  0.7600  0.8444
altlexc         1.0000  1.0000  1.0000
entrel          0.7255  0.8810  0.7957
explicit        0.9812  0.9874  0.9843
hypophora       1.0000  0.9756  0.9877
implicit        0.8784  0.8205  0.8485
norel           0.7045  0.8611  0.7750
all             0.9284  0.9159  0.9221
```
## Notes
* If you would like a DISRPT style `.rels` format, use `rels` option for the `--format` argument:
```
$ python main.py -o output --cache full --format rels
```
* This repository is meant to be used to reproduce results presented in the paper. For the latest (and larger) version of the ever-growing GUM (and GDTB) corpus, as well as the fully PDTB-compatible pipe format, please refer to [the GUM repository](https://github.com/amir-zeldes/gum).
* To obtain `data/discodisco_preds/`, we trained DisCoDisCo on [DISRPT PDTB v3 data](https://github.com/disrpt/sharedtask2023/tree/main/data/eng.pdtb.pdtb). For training setup, please refer to the instructions in our [DisCoDisCo repo](https://github.com/gucorpling/DisCoDisCo).
* To obtain `data/connector_preds/`, we finetuned flan-t5 on PDTB data. Please refer to [the DISRPT shared task repository](https://github.com/disrpt/sharedtask2023/tree/main/data/eng.pdtb.pdtb).

## Citation
When using our work, please use the following citation:
```
@inproceedings{corpling-2024-GDTB,
    title = "GDTB: Genre Diverse Data for English Shallow Discourse Parsing across Modalities, Text Types, and Domains",
    author = "Yang Janet Liu* and Tatsuya Aoyama* and Wesley Scivetti* and Yilun Zhu* and Shabnam Behzad and Lauren Elizabeth Levine and Jessica Lin and Devika Tiwari and Amir Zeldes",
    booktitle = "Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing",
    month = nov,
    year = "2024",
    address = "Miami, USA",
    note = "(*equal contribution)", 
    publisher = "Association for Computational Linguistics",
    abstract = "Work on shallow discourse parsing in English has focused on the Wall Street Journal corpus, the only large-scale dataset for the language in the PDTB framework. However, the data is not openly available, is restricted to the news domain, and is by now 35 years old. In this paper, we present and evaluate a new open-access, multi-genre benchmark for PDTB-style shallow discourse parsing, based on the existing UD English GUM corpus, for which discourse relation annotations in other frameworks already exist. In a series of experiments on cross-domain relation classification, we show that while our dataset is compatible with PDTB, substantial out-of-domain degradation is observed, which can be alleviated by joint training on both datasets.", 
}
```

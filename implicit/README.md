## Step 1: Data

We train our connective prediction module on the PDTB-v3 train split. We gather compile candidate implicit sentences from all adjacent sentences in PDTB-v3 train. Sentences with an implicit relation between them are presented in linear order, and alongside the gold implicit connective. Adjacent sentences without an implicit relation between them are presented alongside a gold connective of "NONE". 

Besides the gold relation spans and gold implicit connective, we also feed the model information about the gold relation label which holds between the spans. We first predict the most likely RST relation for the two spans using the DiscoDisco system. We then map this prediction onto the set of eligible PDTB relations that are compatible with the predicted RST relation. We feed our connective prediction module this set of eligible PDTB relations, alongside the gold spans, in order to predict the gold implicit connective. A single example from the final training data looks like the following:
```

{"input": "Sentence 1: space-delimited tokens, Sentence 2: space-delimited tokens, Relations: comma-delimited list of possible PDTB relations", "output": "single PDTB connective"}
```
## Step 2: Training

We finetuned flan-t5 on PDTB data (previous step). Run train.sh to start training.<br>
Please modify train.sh to point to the data and also the path for the final output (you may need to update the following args: train_file, validation_file, test_file, output_dir, cache_dir).

## Step 3: Prediction on GUM

We use our trained system to predict an implicit connective for all candidate relations in GDTB. We map the gold RST relation label onto a set of compatible PDTB relation labels, and feed that as additional input beside the gold spans. For GDTB relations which do not hold between complete sentences, we expand or contract the relation span to include the complete head sentence. We overpredict connectives for all candidate RST relation pairs, but only use predictions for relations which are deemed eligible by the implicit module (adjacent sentences in the same paragraph with no overt connective between them). 

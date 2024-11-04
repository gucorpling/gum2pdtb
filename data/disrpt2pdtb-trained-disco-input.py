import os
DATA_DIR = "disrpt"
splits = ['train', 'dev', 'test']
prefix = 'eng.rst.gum_'
suffix = '.rels'
infix = '.pdtb-trained-disco-input'
dummy_pdtb = 'expansion.conjunction'
dummy_dir = '1<2'
duplicates = set()
num_dup = 0
total = 0
for split in splits:
    with open(os.path.join(DATA_DIR, prefix+split+suffix)) as f:
        lines = [line.strip() for line in f.readlines()]
    for i in range(1,len(lines)):
        line = lines[i].split('\t')
        """
        [doc, unit1_toks, unit2_toks, unit1_txt, unit2_txt,
         s1_toks, s2_toks, unit1_sent, unit2_sent, dir, orig_label, label]
        """
        if line[3]+line[4]+line[10] in duplicates:
            num_dup += 1
        total += 1
        duplicates.add(line[3]+line[4]+line[10])
        line[9] = dummy_dir  # dummy direction
        rst = line[10]
        line[11] = dummy_pdtb  # dummy PDTB relation
        if line[7] != line[8]:  # if INTER-sentential, use the sentence to make it more PDTB-like
            line[1], line[2], line[3], line[4] = line[5], line[6], line[7], line[8]
        assert len(line) == 12
        for item in line:
            assert len(item) > 0
        lines[i] = '\t'.join(line)

    with open(os.path.join(DATA_DIR, prefix+split+infix+suffix), 'w') as f:
        f.write('\n'.join(lines)+'\n')
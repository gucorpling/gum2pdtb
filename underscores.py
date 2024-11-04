import os, glob, re, io, sys, argparse, pathlib

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = os.path.join(ROOT_DIR, 'data')
PY3 = sys.version_info[0] == 3

parser = argparse.ArgumentParser()
parser.add_argument('--rs4_dir', default=os.path.join(DATA_DIR, 'rst', 'rstweb'))
parser.add_argument('--dep_dir', default=os.path.join(DATA_DIR, 'dep'))
parser.add_argument('--dsrpt_dir', default=os.path.join(DATA_DIR, 'discodisco_preds'))
args = parser.parse_args()
rs4_dir, dep_dir, dsrpt_dir = args.rs4_dir, args.dep_dir, args.dsrpt_dir

def main(rs4_dir, dep_dir, dsrpt_dir):
	make_underscores(dep_dir + os.sep, 1, lemma_col=2)
	make_underscores_rst(rs4_dir + os.sep)
	make_underscores_dsrpt(dsrpt_dir + os.sep)

def make_underscores_rst(folder, extension="rs[34]", edu_regex=r'(.*<segment[^>]*>)(.*)(</segment>)'):
	files_to_process = glob.glob(folder + "GUM_reddit*." + extension)
	print("o Processing " + str(len(files_to_process)) + " files in "+folder+"...")

	# Delete tokens in .xml files
	for f_path in files_to_process:

		with io.open(f_path, 'r', encoding='utf-8') as fin:
			in_lines = fin.read().replace("\r","").strip().split("\n")

		with io.open(f_path, 'w', encoding='utf-8', newline="\n") as fout:
			for i, line in enumerate(in_lines):
				if re.search(edu_regex,line) is None:
					fout.write(line + "\n")
				else:
					m = re.search(edu_regex,line)
					pre = m.group(1)
					seg = m.group(2)
					post = m.group(3)
					seg = re.sub(r'[^ ]','_',seg)
					fout.write(pre + seg + post)
					if i < len(in_lines) - 1:  # Trailing newline
						if PY3:
							fout.write("\n")
						else:
							fout.write(unicode("\n"))


def make_underscores(folder, tok_col, lemma_col=None):

	files_to_process = glob.glob(folder + "GUM_reddit*")
	print("o Processing " + str(len(files_to_process)) + " files in "+folder+"...")

	# Delete tokens in .xml files
	for f_path in files_to_process:

		with io.open(f_path, 'r', encoding='utf-8') as fin:
			in_lines = fin.read().replace("\r","").split("\n")

		with io.open(f_path, 'w', encoding='utf-8', newline="\n") as fout:
			for i, line in enumerate(in_lines):
				if line.startswith('<'):
					fout.write(line + "\n")
				elif line.startswith("#Text=") or line.startswith("# text ="):
					underscored_text = line.split("=",1)[0] + "=" + re.sub(r'[^\s]','_',line.split("=",1)[1])
					if PY3:
						fout.write(underscored_text + "\n")
					else:
						fout.write(unicode(underscored_text + "\n"))
				elif "\t" in line:
					#line = line.replace("&amp;","&")
					elements = line.split('\t')
					if lemma_col is not None:
						if elements[lemma_col] == elements[tok_col]:  # Delete lemma if identical to token
							elements[lemma_col] = '_'
						elif elements[tok_col].lower() == elements[lemma_col]:
							elements[lemma_col] = "*LOWER*"
					elements[tok_col] = len(elements[tok_col])*'_'
					if PY3:
						fout.write('\t'.join(elements) + "\n")
					else:
						fout.write(unicode('\t'.join(elements) + "\n"))
				else:
					fout.write(line)
					if i < len(in_lines) - 1:
						if PY3:
							fout.write("\n")
						else:
							fout.write(unicode("\n"))


def underscore_files(filenames):
	def underscore_rel_field(text):
		blanked = []
		text = text.replace("<*>","❤")
		for c in text:
			if c!="❤" and c!=" ":
				blanked.append("_")
			else:
				blanked.append(c)
		return "".join(blanked).replace("❤","<*>")

	for f_path in filenames:
		skiplen = 0
		with io.open(f_path, 'r', encoding='utf8') as fin:
			lines = fin.readlines()

		with io.open(f_path, 'w', encoding='utf8', newline="\n") as fout:
			output = []
			if f_path.endswith(".rels"):
				for l, line in enumerate(lines):
					line = line.strip()
					if "\t" in line and l > 0:
						doc, unit1_toks, unit2_toks, unit1_txt, unit2_txt, s1_toks, s2_toks, unit1_sent, unit2_sent, direction, orig_label, label = line.split("\t")
						if "GUM" in doc and "reddit" not in doc:
							output.append(line)
							continue
						unit1_txt = underscore_rel_field(unit1_txt)
						unit2_txt = underscore_rel_field(unit2_txt)
						unit1_sent = underscore_rel_field(unit1_sent)
						unit2_sent = underscore_rel_field(unit2_sent)
						fields = doc, unit1_toks, unit2_toks, unit1_txt, unit2_txt, s1_toks, s2_toks, unit1_sent, unit2_sent, direction, orig_label, label
						line = "\t".join(fields)
					output.append(line)
			else:
				doc = ""
				for line in lines:
					line = line.strip()
					if line.startswith("# newdoc_id"):
						doc = line.split("=",maxsplit=1)[1].strip()
					if "GUM" in doc and "reddit" not in doc:
						output.append(line)
						continue
					if line.startswith("# text"):
						m = re.match(r'(# text ?= ?)(.+)',line)
						if m is not None:
							line = m.group(1) + re.sub(r'[^\s]','_',m.group(2))
							output.append(line)
					elif "\t" in line:
						fields = line.split("\t")
						tok_col, lemma_col = fields[1:3]
						if lemma_col == tok_col:  # Delete lemma if identical to token
							fields[2] = '_'
						elif tok_col.lower() == lemma_col:
							fields[2] = "*LOWER*"
						if skiplen < 1:
							fields[1] = len(tok_col)*'_'
						else:
							skiplen -=1
						output.append("\t".join(fields))
						if "-" in fields[0]:  # Multitoken
							start, end = fields[0].split("-")
							start = int(start)
							end = int(end)
							skiplen = end - start + 1
					else:
						output.append(line)
			fout.write('\n'.join(output) + "\n")

def make_underscores_dsrpt(folder):
	files = []
	corpus_files = glob.glob(os.sep.join([folder,"*.rels"]))
	corpus_files += glob.glob(os.sep.join([folder,"*.tok"]))
	corpus_files += glob.glob(os.sep.join([folder,"*.conllu"]))
	sys.stderr.write("o Found " + str(len(corpus_files)) + " files in " + os.sep.join([folder]) + "\n")
	files += corpus_files
	underscore_files(files)
	sys.stderr.write("o Replaced text with underscores in " + str(len(files)) + " files\n")
	sys.exit(1)

if __name__ == "__main__":
	main(rs4_dir, dep_dir, dsrpt_dir)
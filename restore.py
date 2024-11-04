import os, glob, re, io, sys, argparse, pathlib, json
from collections import defaultdict
from copy import deepcopy
from fetch_text import run_fetch

ROOT_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = os.path.join(ROOT_DIR, 'data')

PY3 = sys.version_info[0] == 3

parser = argparse.ArgumentParser()
parser.add_argument('--rs4_dir', default=os.path.join(DATA_DIR, 'rst', 'rstweb'))
parser.add_argument('--dep_dir', default=os.path.join(DATA_DIR, 'dep'))
parser.add_argument('--dsrpt_dir', default=os.path.join(DATA_DIR, 'discodisco_preds'))
parser.add_argument('--gumdoc_fp', default=os.path.join(DATA_DIR, 'gum_docs.json'))
args = parser.parse_args()
rs4_dir, dep_dir, dsrpt_dir, gumdoc_fp = args.rs4_dir, args.dep_dir, args.dsrpt_dir, args.gumdoc_fp

def main(dep_dir, rs4_dir, dsrpt_dir):
	response = input("Do you want to try downloading reddit data from an available server?\n"+
					 "Confirm: you are solely responsible for downloading reddit data and "+
					 "may only use it for non-commercial purposes:\n[Y]es/[N]o> ")
	if response == "Y":
		print("Retrieving reddit data by proxy...")
		textdic = run_fetch()
		make_text(dep_dir + os.sep, textdic, 1, unescape_xml=True, lemma_col=2)
		make_text_rst(rs4_dir + os.sep, textdic, unescape_xml=False)
		# with open(gumdoc_fp) as f:
		# 	gum_docs = json.load(f)
		# data = get_proxy_data()
		# docs2text = get_no_space_strings(data, gum_docs)
		make_text_dsrpt(dsrpt_dir + os.sep, textdic)

	else:
		sys.stderr.write("Aborting\n")
		sys.exit(0)



def make_text(folder, textdic, tok_col, lemma_col=None, unescape_xml=False, docs2lemmas=None, docs2tokens=None):
	files_to_process = glob.glob(folder + "GUM_reddit*")
	print("o Processing " + str(len(files_to_process)) + " files in " + folder + "...")

	lemma_dict = defaultdict(list)
	token_dict = defaultdict(list)
	docs2tokens_copy = deepcopy(docs2tokens)
	docs2lemmas_copy = deepcopy(docs2lemmas)
	for f_path in files_to_process:

		with io.open(f_path, 'r', encoding='utf-8') as fin:
			in_lines = fin.read().replace("\r","").split("\n")

		docname = os.path.basename(f_path)[:os.path.basename(f_path).find(".")]
		tokens = textdic[docname]
		if unescape_xml:
			tokens = tokens.replace("&gt;",">").replace("&lt;","<").replace("&amp;","&")
		else:
			if "&" in tokens and not "&amp;" in tokens and not "_ring" in f_path:
				tokens = tokens.replace("&","&amp;")
			tokens = tokens.replace(">","&gt;").replace("<","&lt;")
		if not PY3:
				tokens = tokens.decode("utf8")

		text_tokens = list(tokens)
		with io.open(f_path, 'w', encoding='utf-8', newline="\n") as fout:
			last_pos = ""
			for i, line in enumerate(in_lines):
				if line.startswith('<'):
					fout.write(line+"\n")
				elif line.startswith("#") and "Text=" in line or "text =" in line:
					restored = [line.split("=",1)[0] + "="]
					for c in line.split("=",1)[1]:
						if c != " ":
							restored.append(text_tokens.pop(0))
						else:
							restored.append(c)
					restored = "".join(restored)
					if unescape_xml:
						restored = restored.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
					fout.write(restored+"\n")
				elif "\t" in line:
					elements = line.split('\t')
					if not (len(elements) == 10 and len(elements[-1]) >0 and ("." in elements[0] or "-" in elements[0])):
						elements[tok_col] = tokens[:len(elements[tok_col])]
						token_dict[docname].append(elements[tok_col])
						tokens = tokens[len(elements[tok_col]):]
						#if not unescape_xml:
						#	elements[tok_col] = elements[tok_col].replace("&amp;","&").replace("&","&amp;")
						if lemma_col is not None:
							if elements[lemma_col] == '_':
								if not (elements[tok_col] in ["hearing","hind"] and "_card" in f_path):  # Check known goeswith cases
									elements[lemma_col] = elements[tok_col]
									if len(elements) < 10:
										if last_pos == "GW":
											elements[lemma_col] = "_"
								else:
									elements[lemma_col] = "_"
							elif elements[lemma_col] == "*LOWER*":
								elements[lemma_col] = elements[tok_col].lower()
							lemma_dict[docname].append(elements[lemma_col])
					if len(elements) < 10:
						last_pos = elements[1]
					if docs2lemmas is not None:  # Reconstruct lemmas for conllu
						if "." not in elements[0] and "-" not in elements[0]:
							elements[2] = docs2lemmas_copy[docname].pop(0)
							docs2tokens_copy[docname].pop(0)
						elif "-" in elements[0]:  # Conllu MWT
							elements[1] = docs2tokens_copy[docname][0]
							elements[1] += docs2tokens_copy[docname][1]
					try:
						line = '\t'.join(elements)
						if unescape_xml:
							line = line.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
						fout.write(line+"\n")
					except Exception as e:
						a=4
				else:
					fout.write(line)
					if i < len(in_lines) - 1:
						if PY3:
							fout.write("\n")
						else:
							fout.write(unicode("\n"))
	return lemma_dict, token_dict


def make_text_rst(folder, textdic, unescape_xml=False, extension="rs[34]", edu_regex=r'(.*<segment[^>]*>)(.*)(</segment>)'):
	files_to_process = glob.glob(folder + "GUM_reddit*." + extension)
	print("o Processing " + str(len(files_to_process)) + " files in "+folder+"...")

	# Delete tokens in .xml files
	for f_path in files_to_process:

		tokens = textdic[os.path.basename(f_path)[:os.path.basename(f_path).find(".")]]
		if not PY3:
			tokens = tokens.decode("utf8")
		if unescape_xml:
			tokens = tokens.replace("&gt;",">").replace("&lt;","<").replace("&amp;","&")
		else:
			if "&" in tokens and not "&amp;" in tokens and not "_ring" in f_path:  # Some bigquery entries have no &amp;
				tokens = tokens.replace("&", "&amp;")
			tokens = tokens.replace(">", "&gt;").replace("<","&lt;")  # Reddit API does not escape lt/gt, but does escape &amp;

		with io.open(f_path, 'r', encoding='utf-8') as fin:
			in_lines = fin.read().replace("\r","").split("\n")

		with io.open(f_path, 'w', encoding='utf-8', newline="\n") as fout:
			cursor = 0
			for i, line in enumerate(in_lines):
				if re.search(edu_regex,line) is None:
					fout.write(line + "\n")
				else:
					m = re.search(edu_regex,line)
					pre = m.group(1)
					seg = m.group(2)
					post = m.group(3)
					out_seg = ""
					for c in seg:
						if c == "_":
							try:
								out_seg += tokens[cursor]
							except Exception as e:
								print("WARNING: tried to access tokens at position " + str(cursor) + ", but "
									  + "an exception occurred. Are you sure '" + f_path + "' was downloaded "
									  + "properly? (len(tokens) = " + str(len(tokens)) + ".)")
							cursor += 1
						else:
							out_seg += c

					#out_seg = out_seg.replace("&","&amp;")
					fout.write(pre + out_seg + post + "\n")

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

def get_proxy_data():
	import requests
	out_posts = {}
	tab_delim = requests.get("https://corpling.uis.georgetown.edu/gum/fetch_text_proxy.py").text
	for line in tab_delim.split("\n"):
		if "\t" in line:
			post, text = line.split("\t")
			out_posts[post] = text
	return out_posts

def get_no_space_strings(cache_dict, gum_docs):
	import ast

	no_space_docs = defaultdict(str)

	for doc in gum_docs:
		for post in gum_docs[doc]:
			if post["id"] in cache_dict:
				json_result = cache_dict[post["id"]]
			parsed = ast.literal_eval(json_result)[0]
			if post["type"]=="post":
				plain = parsed["selftext"]
				title = parsed["title"]
				if "title_only" in post:
					if post["title_only"]:
						plain = ""
				if "title_double" in post:
					title = title + " " + title
			else:
				plain = parsed["body"]
				title = ""
			if "_space" in doc:
				plain = plain.replace("&gt;","")  # GUM_reddit_space has formatting &gt; to indicate indented block quotes
			elif "_gender" in doc:
				plain = plain.replace("- The vast","The vast")
				plain = plain.replace("- Society already accommodates","Society already accommodates")
				plain = plain.replace("- Society recognizes disabilities","Society recognizes disabilities")
				plain = plain.replace("- It’s a waste of time","It’s a waste of time")
				plain = plain.replace("PB&amp;J","PB&J")
			elif "_monsters" in doc:
				plain = plain.replace("1. He refers to","a. He refers to")
				plain = plain.replace("2. Using these","b. Using these")
				plain = plain.replace("3. And he has","c. And he has")
				plain = plain.replace("&#x200B; &#x200B;","")
				plain = re.sub(r' [0-9]+\. ',' ',plain)
			elif "_ring" in doc:
				plain = plain.replace("&gt;",">")
			elif "_escape" in doc:
				plain = plain.replace("*1 year later*","1 year later")
			elif "_racial" in doc:
				plain = plain.replace("> ","")
			elif "_callout" in doc:
				plain = plain.replace("_it","it").replace("well?_","well?").replace(">certain","certain")
			elif "_conspiracy" in doc:
				plain = plain.replace(">", "")
			elif "_stroke" in doc:
				plain = plain.replace("&amp;", "&")
			elif "_bobby" in doc:
				plain = plain.replace("&amp;", "&")
			elif "_introvert" in doc:
				plain = plain.replace("enjoy working out.","enjoy working out").replace("~~","")
			elif "_social" in doc:
				plain = plain.replace("the purpose","those purpose").replace("&#x200B;","")
			no_space = re.sub(r"\s","",plain).replace("*","")
			no_space = re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',no_space)  # Remove Wiki style links: [text](URL)
			if no_space_docs[doc] == "":
				no_space_docs[doc] += re.sub(r"\s","",title).replace("*","")
			no_space_docs[doc] += no_space

	return no_space_docs

def make_text_dsrpt(path_to_underscores, text_dict):
	def restore_range(range_string, underscored, tid_dict):
		output = []
		tok_ids = []
		range_strings = range_string.split(",")
		for r in range_strings:
			if "-" in r:
				s, e = r.split("-")
				tok_ids += list(range(int(s),int(e)+1))
			else:
				tok_ids.append(int(r))

		for tok in underscored.split():
			if tok == "<*>":
				output.append(tok)
			else:
				tid = tok_ids.pop(0)
				output.append(tid_dict[tid])
		return " ".join(output)

	dep_files = glob.glob(path_to_underscores+"*.conllu")
	tok_files = glob.glob(path_to_underscores+"*.tok")
	rel_files = glob.glob(path_to_underscores+"*.rels")
	skiplen = 0
	token_dict = {}
	tid2string = defaultdict(dict)
	for file_ in dep_files + tok_files + rel_files:
		lines = io.open(file_,encoding="utf8").readlines()
		underscore_len = 0  # Must match doc_len at end of file processing
		doc_len = 0
		if file_.endswith(".rels"):
			output = []
			violation_rows = []
			for l, line in enumerate(lines):
				line = line.strip()
				if l > 0 and "\t" in line:
					fields = line.split("\t")
					docname = fields[0]
					text = text_dict[docname]
					if "GUM_" in docname and "reddit" not in docname:  # Only Reddit documents need reconstruction in GUM
						output.append(line)
						continue
					doc, unit1_toks, unit2_toks, unit1_txt, unit2_txt, s1_toks, s2_toks, unit1_sent, unit2_sent, direction, orig_label, label = line.split("\t")
					underscore_len += unit1_txt.count("_") + unit2_txt.count("_") + unit1_sent.count("_") + unit2_sent.count("_")
					if underscore_len == 0:
						sys.stderr.write("! Non-underscored file detected - " + os.path.basename(file_) + "\n")
						sys.exit(0)
					unit1_txt = restore_range(unit1_toks, unit1_txt, tid2string[docname])
					unit2_txt = restore_range(unit2_toks, unit2_txt, tid2string[docname])
					unit1_sent = restore_range(s1_toks, unit1_sent, tid2string[docname])
					unit2_sent = restore_range(s2_toks, unit2_sent, tid2string[docname])
					plain = unit1_txt + unit2_txt + unit1_sent + unit2_sent
					plain = plain.replace("<*>","").replace(" ","")
					doc_len += len(plain)
					fields = doc, unit1_toks, unit2_toks, unit1_txt, unit2_txt, s1_toks, s2_toks, unit1_sent, unit2_sent, direction, orig_label, label
					line = "\t".join(fields)
					if doc_len != underscore_len and len(violation_rows) == 0:
						violation_rows.append(str(l) + ": " + line)
				output.append(line)

		else:
			tokfile = True if ".tok" in file_ else False
			output = []
			parse_text = ""
			docname = ""
			for line in lines:
				line = line.strip()
				if "# newdoc_id " in line:
					tid = 0
					if parse_text !="":
						if not tokfile:
							token_dict[docname] = parse_text
					parse_text = ""
					docname = re.search(r'# newdoc_id ?= ?([^\s]+)',line).group(1)
					if "GUM" in docname and "reddit" not in docname:
						output.append(line)
						continue
					if docname not in text_dict:
						raise IOError("! Text for document name " + docname + " not found.\n Please check that your LDC data contains the file for this document.\n")
					if ".tok" in file_:
						text = token_dict[docname]
					else:
						text = text_dict[docname]
					doc_len = len(text)
					underscore_len = 0

				if "GUM" in docname and "reddit" not in docname:
					output.append(line)
					continue

				if line.startswith("# text"):
					m = re.match(r'(# ?text ?= ?)(.+)',line)
					if m is not None:
						i = 0
						sent_text = ""
						for char in m.group(2).strip():
							if char != " ":
								sent_text += text[i]
								i+=1
							else:
								sent_text += " "
						line = m.group(1) + sent_text
						output.append(line)
				elif "\t" in line:
					fields = line.split("\t")
					if skiplen < 1:
						underscore_len += len(fields[1])
						fields[1] = text[:len(fields[1])]
					if not "-" in fields[0] and not "." in fields[0]:
						parse_text += fields[1]
						tid += 1
						tid2string[docname][tid] = fields[1]
					if not tokfile:
						if fields[2] == '_' and not "-" in fields[0] and not "." in fields[0]:
							fields[2] = fields[1]
						elif fields[2] == "*LOWER*":
							fields[2] = fields[1].lower()
					if skiplen < 1:
						text = text[len(fields[1]):]
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

		if not doc_len == underscore_len:
			if ".rels" in file_:
				sys.stderr.write(
					"\n! Tried to restore file " + os.path.basename(file_) + " but source text has different length than tokens in shared task file:\n" + \
					"  Source text in data/: " + str(doc_len) + " non-whitespace characters\n" + \
					"  Token underscores in " + file_ + ": " + str(underscore_len) + " non-whitespace characters\n" + \
					"  Violation row: " + violation_rows[0])
			else:
				sys.stderr.write("\n! Tried to restore document " + docname + " but source text has different length than tokens in shared task file:\n" + \
						  "  Source text in data/: " + str(doc_len) + " non-whitespace characters\n" + \
						  "  Token underscores in " + file_+": " + str(underscore_len) + " non-whitespace characters\n")
			with io.open("debug.txt",'w',encoding="utf8") as f:
				f.write(text_dict[docname])
				f.write("\n\n\n")
				f.write(parse_text)
			sys.exit(0)

		if not tokfile and parse_text != "":
			token_dict[docname] = parse_text

		with io.open(file_, 'w', encoding='utf8', newline="\n") as fout:
			fout.write("\n".join(output) + "\n")

	sys.stderr.write("o Restored text in " + str(len(dep_files)) + " .conllu files, " + str(len(tok_files)) +
					 " .tok files and "+ str(len(rel_files)) + " .rels files\n")


if __name__ == "__main__":
	main(dep_dir, rs4_dir, dsrpt_dir)
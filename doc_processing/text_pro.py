from __future__ import annotations
import json, re, sys, math, statistics as stats
from pathlib import Path

Hdr = ["ref","date","client","name","address","nationality","subject"]

def load_items(p: Path):
	with p.open("r", encoding="utf-8") as f: return json.load(f)

def to_lines(items, ytol=None):
	items=[i for i in items if (i.get("text") or "").strip()]
	if not items: return []
	items.sort(key=lambda x:(x["top"],x["left"]))
	hs=[i["height"] for i in items if i.get("height")]
	ytol = ytol or max(6, round((stats.median(hs) if hs else 12)*0.5))
	lines=[]; cur=[]; y0=items[0]["top"]
	for t in items:
		if abs(t["top"]-y0)<=ytol: cur.append(t)
		else:
			lines.append(sorted(cur,key=lambda x:x["left"]))
			cur=[t]; y0=t["top"]
	if cur: lines.append(sorted(cur,key=lambda x:x["left"]))
	return lines

def join_text(lines):
	lt=[" ".join(w["text"].strip() for w in ln) for ln in lines]
	return lt, "\n".join(lt), " ".join(lt).lower()

def gaps_for_line(ln):
	if len(ln)<2: return []
	g=[]
	for a,b in zip(ln,ln[1:]):
		g.append(b["left"]-(a["left"]+a["width"]))
	return [x for x in g if x>=0]

def check_double_spacing(lines):
	issues=[]; total_large=0
	for idx,ln in enumerate(lines):
		g=gaps_for_line(ln)
		if not g: continue
		med=max(1, int(stats.median(g)))
		large=[(j,gg) for j,gg in enumerate(g) if gg>1.8*med and gg>6]
		if large:
			total_large+=len(large)
			issues.append({"type":"double-spacing","line":idx,"gaps":large,"median_gap":med})
	return issues, total_large

def check_irregular_fonts(lines):
	issues=[]; flagged=0
	for i,ln in enumerate(lines):
		hs=[w["height"] for w in ln if w.get("height")]
		if len(hs)<3: continue
		m=sum(hs)/len(hs); sd=math.sqrt(sum((h-m)**2 for h in hs)/len(hs)) if m else 0
		cv=(sd/m) if m else 0
		if cv>0.30:
			flagged+=1; issues.append({"type":"irregular-font","line":i,"cv":round(cv,3),"mean":round(m,2)})
	return issues, flagged

def check_indentation(lines):
	L=[ln[0]["left"] for ln in lines if ln]
	if len(L)<3: return [],0
	bins={}
	for x in L:
		b=round(x/16)*16
		bins[b]=bins.get(b,0)+1
	levels=sorted(bins.items(), key=lambda x:-x[1])
	dominant=levels[0][0]
	inconsistent=[(i,l) for i,l in enumerate(L) if abs(l-dominant)>24]
	return ([{"type":"indent-inconsistent","line":i,"left":l,"dominant":dominant} for i,l in inconsistent], len(inconsistent))

def edit_distance(a,b):
	la,lb=len(a),len(b)
	if abs(la-lb)>3: return 4
	dp=list(range(lb+1))
	for i,ca in enumerate(a,1):
		prv=dp[0]; dp[0]=i
		for j,cb in enumerate(b,1):
			cur=min(dp[j]+1, dp[j-1]+1, prv+(ca!=cb)); prv,dp[j]=dp[j],cur
	return dp[lb]

def find_headers(doc_lc):
	found={h:(doc_lc.find(h)>=0) for h in Hdr}
	return found

def near_miss_headers(tokens):
	nm=[]
	for t in tokens:
		w=t["text"]
		if not w.endswith(":"): continue
		b=w[:-1].lower()
		for h in Hdr:
			if b==h: continue
			if abs(len(b)-len(h))<=2 and edit_distance(b,h)<=2:
				nm.append({"type":"incorrect-header","at":t,"got":w,"want":h})
	return nm

def content_validation(lines, tokens, doc_lc):
	issues=[]; bad_spell=0
	for t in tokens:
		w=t["text"]
		if len(w)>3 and re.fullmatch(r"[A-Za-z][A-Za-z\-\.]*", w) and t.get("conf",100.0)<70.0:
			bad_spell+=1; issues.append({"type":"spelling","at":t,"conf":t.get("conf")})
	H=find_headers(doc_lc)
	missing=[h for h,v in H.items() if not v]
	if missing:
		for h in missing: issues.append({"type":"missing-section","header":h})
	nm=near_miss_headers(tokens)
	issues+=nm
	return issues, bad_spell, missing

def structure_analysis(lines, doc_lc):
	line_texts=[" ".join(w["text"] for w in ln).lower() for ln in lines]
	pos={h:next((i for i,s in enumerate(line_texts) if h in s), None) for h in Hdr}
	order_pairs=[("ref","date"),("date","client"),("client","name"),("name","address"),("address","nationality"),("nationality","subject")]
	wrong=[]; ok=0; total=0
	for a,b in order_pairs:
		if pos[a] is None or pos[b] is None: continue
		total+=1
		if pos[a] <= pos[b]: ok+=1
		else: wrong.append({"type":"order","a":a,"b":b,"posA":pos[a],"posB":pos[b]})
	completeness=sum(1 for v in pos.values() if v is not None)/len(Hdr)
	order_score=(ok/total) if total else 0.0
	issues=[{"type":"structure-order","detail":wrong}] if wrong else []
	return issues, completeness, order_score, pos

def template_match(doc_lc):
	present=sum(1 for h in Hdr if h in doc_lc)
	return present/len(Hdr)

def risk_score(counts):
    # here is the weight, if we wanna change in the future 
	w={"double":1,"fonts":5,"indent":1,"spelling":10,"missing":15,"order":8}
	raw=(w["double"]*counts.get("double",0)+
		 w["fonts"]*counts.get("fonts",0)+
		 w["indent"]*counts.get("indent",0)+
		 w["spelling"]*counts.get("spelling",0)+
		 w["missing"]*counts.get("missing",0)+
		 w["order"]*counts.get("order",0))
	damp=(1.0 - 0.3*counts.get("template",0) - 0.3*counts.get("completeness",0))
	damp=max(0.5, min(1.0, damp))
	score=min(100, int(raw*damp))
	return max(0, score)

def analyze(path: str, out: str|None=None, out_txt: str|None=None):
	audit=[]
	p=Path(path)
	items=load_items(p); audit.append(f"items:{len(items)}")
	lines=to_lines(items); audit.append(f"lines:{len(lines)}")
	_, _, doc_lc = join_text(lines)

	ds, n_ds = check_double_spacing(lines); audit.append(f"double_spacing_flags:{n_ds}")
	rf, n_rf = check_irregular_fonts(lines); audit.append(f"irregular_font_lines:{n_rf}")
	ind, n_ind = check_indentation(lines); audit.append(f"indent_flags:{n_ind}")
	flat=[w for ln in lines for w in ln]
	cont, n_spell, missing = content_validation(lines, flat, doc_lc); audit.append(f"spelling_flags:{n_spell}")
	struct, complete, order_score, pos = structure_analysis(lines, doc_lc); audit.append(f"completeness:{round(complete,3)};order:{round(order_score,3)}")
	tmpl = template_match(doc_lc); audit.append(f"template_match:{round(tmpl,3)}")

	issues = ds+rf+ind+cont+struct
	counts={"double":n_ds,"fonts":n_rf,"indent":n_ind,"spelling":n_spell,"missing":len(missing),
			"order": (1 if 0<order_score<1 else 0), "template":tmpl, "completeness":complete}
	score=risk_score(counts)

	report={
		"file": str(p),
		"summary": {"lines":len(lines),"tokens":len(items),"template_match":round(tmpl,3),"completeness":round(complete,3),"order_score":round(order_score,3)},
		"risk": {"score":score, "factors":counts},
		"issues": issues,
		"structure_positions": pos,
		"checks": {
			"format_validation": {"double_spacing":n_ds, "irregular_fonts":n_rf, "indent_inconsistent":n_ind},
			"content_validation": {"spelling_flags":n_spell, "missing_sections":missing},
			"structure_analysis": {"order_score":round(order_score,3), "completeness":round(complete,3)},
			"template_matching": {"headers":Hdr, "match":round(tmpl,3)}
		},
		"audit": audit
	}

	rep_json = json.dumps(report, ensure_ascii=False, indent=2)
	if out is not None:
		out_p = Path(out)
		out_p.parent.mkdir(parents=True, exist_ok=True)
		with out_p.open("w", encoding="utf-8") as f: f.write(rep_json)
	if out_txt is not None:
		out_txt_p = Path(out_txt)
		out_txt_p.parent.mkdir(parents=True, exist_ok=True)
		with out_txt_p.open("w", encoding="utf-8") as f:
			f.write(f"Risk Score: {score}\n")
			f.write(f"Template Match: {round(tmpl,3)} Completeness: {round(complete,3)} Order: {round(order_score,3)}\n")
			f.write(f"Formatting: double={n_ds}, irregular-font={n_rf}, indent={n_ind}\n")
			f.write(f"Content: spelling={n_spell}, missing={missing}\n")
			for i,iss in enumerate(issues,1): f.write(f"{i}. {iss['type']}: { {k:v for k,v in iss.items() if k!='type'} }\n")
	return rep_json

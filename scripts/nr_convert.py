#!/usr/bin/env python3
"""Convert RONLAW API dumps (see nr_fetch.py) into LawCodex Markdown.

Usage: nr_convert.py RAW_DIR OUT_DIR
"""
import datetime, glob, json, os, re, sys, unicodedata
from urllib.parse import quote

RAW, OUT = sys.argv[1], sys.argv[2]
TODAY = datetime.date.today().isoformat()

PART = re.compile(r"^(PART|Part)\s+([0-9IVXLC]+[A-Z]?)\b\s*(—|–|-|$)")
DIVISION = re.compile(r"^(DIVISION|Division)\s+(\d+(\.\d+)?[A-Z]?)\b\s*(—|–|-|$)")
SCHEDULE = re.compile(r"^(SCHEDULE|FIRST SCHEDULE|SECOND SCHEDULE|THIRD SCHEDULE|FOURTH SCHEDULE)\b")
SECTION = re.compile(r"^(\d{1,4}[A-Z]{0,2})\s+(\S.{0,180})$")
LABEL = re.compile(r"^(\(\w{1,6}\)|\[|‘|“|\")")
DOTS = re.compile(r"(\.\s?){6,}\s*[\d,]*\s*$")


def slug(s, n=90):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:n].rstrip("-")


def yq(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def clean_title(fn):
    t = re.sub(r"\.pdf$", "", fn.strip(), flags=re.I)
    t = t.replace("_", " ")
    t = re.sub(r"\s*\(\d\)\s*$", "", t)
    m = re.search(r"\s*serv(ice)?\s*(\d+)\s*(\(\d\))?\s*$", t, re.I)
    serv = None
    if m:
        serv = m.group(2)
        t = t[:m.start()]
    t = re.sub(r"\s*\(\d\)\s*$", "", t)
    return re.sub(r"\s+", " ", t).strip(" -_"), serv


def page_lines(text, title_up):
    lines = [l.rstrip() for l in text.split("\n")]
    # footer: from the last "Service N" line onwards (consolidated 'serv' editions)
    idx = [i for i, l in enumerate(lines) if re.match(r"^\s*Service\s*\d", l)]
    if idx and any(l.startswith("bwpageid::") or l.startswith("Job:") for l in lines[idx[-1]:]):
        lines = lines[:idx[-1]]
        while lines and lines[-1].strip() and lines[-1].upper() == lines[-1] and len(lines[-1]) < 140 and (
                "LAWS OF THE REPUBLIC" in lines[-1] or (title_up and title_up[:25] in lines[-1])):
            lines.pop()
    out = []
    for l in lines:
        s = l.strip()
        if not s or re.fullmatch(r"\[The next page is [\d,]+\]", s) or re.fullmatch(r"\d{1,3}", s):
            continue
        if DOTS.search(s):
            continue
        out.append(s)
    return out


def structure(lines):
    out, para = [], []
    last = 0
    in_toa = False

    def flush():
        if para:
            out.append(" ".join(para))
            para.clear()

    skip = False
    for i, s in enumerate(lines):
        if skip:
            skip = False
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if PART.match(s) and len(s) < 160:
            if nxt and nxt.upper() == nxt and len(nxt) < 60 and not nxt.startswith("[") and re.search(r"[A-Z]", nxt) \
                    and not PART.match(nxt) and not DIVISION.match(nxt) and not SECTION.match(nxt):
                s = s + " " + nxt
                skip = True
            flush(); out.append("## " + s); continue
        if DIVISION.match(s) and len(s) < 160:
            flush(); out.append("### " + s); continue
        if SCHEDULE.match(s) and len(s) < 140:
            flush(); out.append("## " + s); last = 0; continue
        if re.fullmatch(r"TABLE OF AMENDMENTS", s):
            flush(); out.append("## Table of Amendments"); in_toa = True; continue
        if in_toa and re.match(r"^(An Act|AN ACT|Enacted|ENACTED|PART|1 [A-Z]|WHEREAS|Article 1 )", s):
            flush(); in_toa = False; last = 0
        a = re.match(r"^Article (\d{1,3}[A-Z]?) (\S.{0,150})$", s)
        if a and not in_toa and not re.search(r"[;,:—-]$", s):
            n = int(re.match(r"\d+", a.group(1)).group())
            if last <= n <= last + 15:
                flush(); out.append(f"#### Article {a.group(1)} {a.group(2)}"); last = n; continue
        m = SECTION.match(s)
        if m and not in_toa and not re.match(r"(January|February|March|April|May|June|July|August|September|October|November|December)\b", m.group(2)) and len(s) < 160 and not re.search(r"[;,:—-]$", s) and (m.group(2)[0].isupper() or m.group(2)[0] in "‘'“\"("):
            n = int(re.match(r"\d+", m.group(1)).group())
            if last <= n <= last + 15 and not (n == last and not re.search(r"[A-Z]$", m.group(1))):
                flush()
                out.append(f"#### {m.group(1)} {m.group(2)}")
                last = n
                continue
        if LABEL.match(s):
            flush()
        para.append(s)
        if re.search(r"[.:;\]]$", s) and nxt and (LABEL.match(nxt) or nxt[:1].isupper()):
            flush()
    flush()
    return "\n\n".join(out)


def convert(src):
    title, serv = clean_title(src["title"])
    tu = title.upper()
    pages = sorted(src.get("pages") or [], key=lambda p: p["page_number"])
    consolidated = bool(serv) or any("bwpageid::" in (p.get("page_content") or "") for p in pages)
    lines = []
    started = False
    for p in pages:
        pl = page_lines(p.get("page_content") or "", tu)
        if not pl:
            continue
        head = " ".join(pl[:3])
        if consolidated and not started:
            # skip cover/contents and table-of-provisions pages of consolidated editions
            if re.search(r"Table of Contents|TABLE OF PROVISIONS|^Section Title", head) and "TABLE OF AMENDMENTS" not in head:
                continue
        if pl and re.fullmatch(r"((Section|Regulation|Rule|Article|Clause|1) )?Title", pl[0]):
            continue
        started = True
        lines += pl
    # drop a duplicated title line at the very start
    while lines and (lines[0].upper() == tu or lines[0] == title or lines[0] in ("Table of Contents", "REPUBLIC OF NAURU")):
        lines.pop(0)
    return title, (serv or ("?" if consolidated else None)), structure(lines)


def main():
    counts, used, problems = {}, set(), []
    for cat, sub in (("acts", "acts"), ("laws", "subsidiary")):
        for f in sorted(glob.glob(os.path.join(RAW, "api", f"{cat}-*.json"))):
            for h in json.load(open(f))["hits"]["hits"]:
                src = h["_source"]
                if src.get("is_deleted"):
                    continue
                title, serv, body = convert(src)
                if len(body) < 150:
                    problems.append(src["file_path"])
                    continue
                year = src.get("year")
                is_const = cat == "acts" and re.match(r"Constitution of Na(uru|oero) 1968$", title)
                d = "constitution" if is_const else f"{sub}/{year}"
                name = slug(title)
                p = f"{d}/{name}.md"
                if p in used:
                    p = f"{d}/{name}-{h['_id'][:8]}.md"
                used.add(p)
                kind = "constitution" if is_const else ("act" if cat == "acts" and " Act" in title else "regulation" if cat == "laws" else "act")
                fm = ["---", f"title: {yq(title)}", f"identifier: {yq(h['_id'])}", f"type: {kind}",
                      "jurisdiction: nr", "language: en", f"year: {year}"]
                if serv == "?":
                    fm.append('consolidation: "Laws of the Republic of Naoero (consolidated reprint)"')
                elif serv:
                    fm.append(f"consolidation: {yq('Laws of the Republic of Naoero, Service ' + serv)}")
                else:
                    fm.append('consolidation: "none (text as published)"')
                fm += ["status: unknown" if not serv else "status: in_force",
                       f"source: {yq('https://ronlaw.gov.nr/pdfviewer/' + quote(quote(src['file_path'].lstrip('/'), safe='')))}",
                       f"source_file: {yq(src['file_path'])}",
                       'format_note: "text extracted (by RONLAW) from the official PDF; layout not preserved"',
                       f"retrieved: {TODAY}", "---", ""]
                out = os.path.join(OUT, p)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("\n".join(fm) + f"# {title}\n\n" + body + "\n")
                k = d.split("/")[0]
                counts[k] = counts.get(k, 0) + 1
    print(counts)
    print(len(problems), "empty/unusable:", problems[:20])


if __name__ == "__main__":
    main()

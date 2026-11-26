import json,urllib.request,urllib.parse,time,sys,os
terms=[t.strip() for t in open('out/glossary_build/wd_terms.txt') if t.strip()]
res={}
def run(q):
    for attempt in range(6):
        req=urllib.request.Request("https://query.wikidata.org/sparql",data=urllib.parse.urlencode({"query":q,"format":"json"}).encode(),
            headers={"User-Agent":"research-glossary-script/0.1","Accept":"application/sparql-results+json"})
        try: return json.load(urllib.request.urlopen(req,timeout=120))
        except urllib.error.HTTPError as e:
            if e.code!=429: raise
            w=int(e.headers.get("Retry-After") or 60); print("429, waiting",w,flush=True); time.sleep(w+5)
    raise SystemExit("still rate-limited")
for i in range(0,len(terms),15):
    vals=" ".join(f'"{t}"@en' for t in terms[i:i+15])
    q=f'''SELECT ?l ?item ?km ?lo ?vi ?mesh ?icd WHERE {{ VALUES ?l {{ {vals} }} ?item rdfs:label ?l .
 OPTIONAL{{?item wdt:P486 ?mesh}} OPTIONAL{{?item wdt:P494 ?icd}}
 OPTIONAL{{?item rdfs:label ?km FILTER(lang(?km)="km")}} OPTIONAL{{?item rdfs:label ?lo FILTER(lang(?lo)="lo")}} OPTIONAL{{?item rdfs:label ?vi FILTER(lang(?vi)="vi")}} }}'''
    for b in run(q)['results']['bindings']:
        g=lambda k:b.get(k,{}).get('value')
        res.setdefault(g('l'),[]).append({"item":g('item').rsplit('/',1)[1],"km":g('km'),"lo":g('lo'),"vi":g('vi'),"medical":bool(g('mesh') or g('icd'))})
    print("batch",i//15,"ok",flush=True); time.sleep(10)
out={}
for t in terms:
    c=[x for x in res.get(t,[]) if x['vi']]; c.sort(key=lambda x:(not x['medical'],int(x['item'][1:]))); out[t]=c[0] if c else None
json.dump({"chosen":out,"all":res},open('out/glossary_build/wikidata.json','w'),ensure_ascii=False,indent=0)
print('vi:',sum(1 for v in out.values() if v),'/',len(terms),' km:',sum(1 for v in out.values() if v and v['km']),' lo:',sum(1 for v in out.values() if v and v['lo']))
for t,v in out.items(): print(f"{t:28}", (f"{v['vi']:32} {'MED' if v['medical'] else '   '} {v['item']}" if v else '—'))

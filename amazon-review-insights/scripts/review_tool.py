#!/usr/bin/env python3
"""Local preparation, evidence validation and offline reporting; no AI/network calls."""
import argparse, csv, datetime as dt, hashlib, json, re, sys
from pathlib import Path

ALIASES={
 'id':['Review ID','review_id','评论ID'], 'product':['ASIN','Product','产品','产品ASIN'],
 'variant':['Variant','Variation','变体','款式'], 'title':['Title','Review Title','标题','评论标题'],
 'body':['Content','Review Text','Review Content','Body','评论内容','正文','内容'],
 'country':['Country','国家','评论国家'], 'date':['Date','Review Date','日期','评论时间'],
 'rating':['Rating','Stars','评分','星级'], 'verified':['Verified Purchase','Verified','已验证购买'],
 'helpful':['Helpful','Helpful Votes','有用票','点赞数'], 'photo':['Photo URLs','Images','图片链接'],
 'video':['Video URLs','Videos','视频链接']}
def norm(v): return re.sub(r'\s+',' ',str(v or '')).strip()
def key(v): return re.sub(r'[\s_\-]+','',norm(v)).casefold()
def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def fingerprint(reviews,quality):
    return hashlib.sha256(json.dumps([reviews,quality],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def parse_date(v):
    if isinstance(v,(dt.datetime,dt.date)):return v.date().isoformat() if isinstance(v,dt.datetime) else v.isoformat()
    v=norm(v);v=v.split(' on ')[-1]
    for fmt in ['%Y-%m-%d','%Y/%m/%d','%Y-%m-%d %H:%M:%S','%B %d, %Y']:
        try:return dt.datetime.strptime(v,fmt).date().isoformat()
        except ValueError:pass
    return None
def parse_rating(v):
    if v is None or norm(v)=='':return None
    s=norm(v);m=re.fullmatch(r'([1-5](?:\.0)?)(?:\s*(?:out of 5 stars?|stars?|星))?',s,re.I)
    return int(float(m[1])) if m else None
def tables(path,args):
    if path.suffix.lower()=='.xlsx':
        try:import openpyxl
        except ImportError:raise ValueError('XLSX requires openpyxl; install requirements.txt or use a bundled Python runtime.')
        w=openpyxl.load_workbook(path,read_only=True,data_only=True)
        try:
            sheets=[w[args.sheet]] if args.sheet else list(w)
            for s in sheets:yield s.title,list(s.values)
        finally:w.close()
    elif path.suffix.lower() in ('.csv','.tsv'):
        with path.open(encoding=args.encoding,newline='') as f:yield '',list(csv.reader(f,delimiter='\t' if path.suffix.lower()=='.tsv' else ','))
    else:raise ValueError('Supported input extensions: .csv, .tsv, .xlsx')
def prepare(args):
    mapping=read(args.mapping) if args.mapping else {};unknown=set(mapping)-set(ALIASES)
    if unknown:raise ValueError('Unknown mapping fields: '+str(sorted(unknown)))
    reviews=[];seen={};quality={'input_rows':0,'blank_rows':0,'duplicate_ids':0,'conflicts':[],'warnings':[],'sources':[]}
    for filename in args.inputs:
        path=Path(filename);sha=hashlib.sha256(path.read_bytes()).hexdigest();quality['sources'].append({'name':path.name,'sha256':sha})
        for sheet,rows in tables(path,args):
            if len(rows)<args.header_row:continue
            headers=[norm(v) for v in rows[args.header_row-1]];cols={}
            for field,aliases in ALIASES.items():
                targets=[mapping[field]] if field in mapping else aliases
                matches=[i for i,h in enumerate(headers) if key(h) in {key(t) for t in targets}]
                if len(matches)>1:raise ValueError(f'Ambiguous {field} columns in {path.name}/{sheet}; provide a mapping.')
                if field in mapping and not matches:raise ValueError(f'Mapped header not found: {mapping[field]}')
                if matches:cols[field]=matches[0]
            if 'body' not in cols:raise ValueError(f'No review body in {path.name}/{sheet}; use --mapping or --sheet.')
            for rownum,row in enumerate(rows[args.header_row:],args.header_row+1):
                if not any(v is not None and str(v).strip() for v in row):quality['blank_rows']+=1;continue
                quality['input_rows']+=1
                get=lambda f:row[cols[f]] if f in cols and cols[f]<len(row) else None
                rawdate=get('date');country=norm(get('country'));match=re.search(r'Reviewed in (?:the )?(.+?) on ',norm(rawdate))
                if not country and match:country=match[1]
                source={'file':path.name,'sheet':sheet,'row':rownum}
                rid=norm(get('id')) or 'row-'+hashlib.sha256(f'{sha}|{sheet}|{rownum}'.encode()).hexdigest()[:20]
                rawbody=str(get('body') or '');body=norm(rawbody.replace('The media could not be loaded.',''))
                verified=norm(get('verified')).casefold();vp=True if verified in ['yes','true','1','是','已验证购买'] else False if verified in ['no','false','0','否'] else None
                rating=parse_rating(get('rating'));date=parse_date(rawdate)
                r={'id':rid,'product':norm(get('product')) or '未提供产品标识','variant':norm(get('variant')) or '未提供变体',
                   'title':norm(get('title')),'body':body,'country':country or '未知','date':date,'rating':rating,
                   'verified':vp,'photo':bool(norm(get('photo'))),'video':bool(norm(get('video'))),'sources':[source]}
                try:r['helpful']=max(0,int(get('helpful') or 0))
                except (ValueError,TypeError):r['helpful']=0;quality['warnings'].append({'id':rid,'issue':'invalid_helpful'})
                for problem,flag in [('empty_body',not body),('invalid_or_missing_rating',rating is None),('invalid_or_missing_date',date is None)]:
                    if flag:quality['warnings'].append({'id':rid,'issue':problem})
                if rid in seen:
                    old=seen[rid];quality['duplicate_ids']+=1
                    # Votes, media flags and provenance can evolve; semantic conflicts need resolution.
                    fields=['product','variant','title','body','country','date','rating','verified']
                    changed=[k for k in fields if old[k]!=r[k]]
                    if changed:quality['conflicts'].append({'id':rid,'fields':changed,'source':source})
                    old['sources'].append(source);old['helpful']=max(old['helpful'],r['helpful']);old['photo']|=r['photo'];old['video']|=r['video']
                else:seen[rid]=r;reviews.append(r)
    if not reviews:raise ValueError('No reviews found.')
    obj={'schema_version':1,'reviews':reviews,'quality':quality,'review_set_sha256':fingerprint(reviews,quality)};dump(args.out,obj)
    print(json.dumps({'unique_reviews':len(reviews),'quality':quality,'review_set_sha256':obj['review_set_sha256']},ensure_ascii=False))
    return obj
def validate(data,annotations,allow_partial=False):
    errors=[];reviews=data.get('reviews',[]);index={r['id']:r for r in reviews};decisions=annotations.get('decisions',[]);seen=set();analyzed=set()
    if data.get('schema_version')!=1 or annotations.get('schema_version')!=1:errors.append('schema_version must be 1')
    if data.get('review_set_sha256')!=fingerprint(reviews,data.get('quality')):errors.append('prepared data fingerprint is stale')
    if annotations.get('review_set_sha256')!=data.get('review_set_sha256'):errors.append('annotation fingerprint mismatch')
    if data.get('quality',{}).get('conflicts'):errors.append('resolve conflicting duplicate IDs before publication')
    for decision in decisions:
        rid=decision.get('id');r=index.get(rid)
        if not r:errors.append(f'unknown review: {rid}');continue
        if rid in seen:errors.append(f'duplicate decision: {rid}')
        seen.add(rid);status=decision.get('status');obs=decision.get('observations',[])
        if status not in ['analyzed','excluded']:errors.append(f'{rid}: invalid status')
        if status=='excluded':
            if not norm(decision.get('reason')) or obs:errors.append(f'{rid}: excluded needs reason and no observations')
        if status=='analyzed':analyzed.add(rid)
        slots=set()
        for o in obs:
            kind=o.get('kind');label=norm(o.get('label'));sent=o.get('sentiment','');slot=(kind,label,sent)
            if kind not in ['aspect','scenario','motive','need'] or not label:errors.append(f'{rid}: invalid kind/label')
            if kind=='aspect' and sent not in ['positive','negative','neutral']:errors.append(f'{rid}: aspect needs sentiment')
            if kind!='aspect' and sent:errors.append(f'{rid}: non-aspect should omit sentiment')
            if slot in slots:errors.append(f'{rid}: duplicate observation {slot}')
            slots.add(slot);evidence=o.get('evidence',[])
            if not evidence:errors.append(f'{rid}: missing evidence')
            for e in evidence:
                field=e.get('field');quote=norm(e.get('quote'))
                if field not in ['title','body'] or not quote or quote not in norm(r.get(field,'')):errors.append(f'{rid}: evidence not found in {field}: {quote[:60]}')
    pending=set(index)-seen
    if pending and not allow_partial:errors.append(f'{len(pending)} reviews pending; analyze/exclude them or explicitly use --allow-partial')
    for recommendation in annotations.get('report',{}).get('recommendations',[]):
        ids=recommendation.get('support_ids',[])
        if not norm(recommendation.get('text')) or not ids or not set(ids)<=analyzed:errors.append('recommendation needs text and analyzed support IDs')
    if not analyzed:errors.append('no analyzed reviews')
    if errors:raise ValueError('\n'.join(errors))
    return {'prepared':len(index),'analyzed':len(analyzed),'excluded':sum(d.get('status')=='excluded' for d in decisions),'pending':len(pending)}
def csvcell(v):
    s=str(v if v is not None else '')
    return "'"+s if re.match(r'^\s*[=+@-]',s) else s
def render(args):
    data=read(args.data);a=read(args.annotations);coverage=validate(data,a,args.allow_partial);decisions={d['id']:d for d in a['decisions']}
    merged=[dict(r,decision=decisions.get(r['id'],{'status':'pending','observations':[]})) for r in data['reviews']]
    payload={'reviews':merged,'coverage':coverage,'report':a.get('report',{}),'quality':data['quality']}
    safe=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=(Path(__file__).resolve().parents[1]/'assets/report.html').read_text(encoding='utf-8')
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(template.replace('__DATA__',safe),encoding='utf-8')
    with out.with_suffix('.audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['review_id','product','variant','country','date','rating','status','reason','kind','label','sentiment','evidence','title','body','sources'])
        for r in merged:
            for o in r['decision'].get('observations',[]) or [{}]:
                row=[r['id'],r['product'],r['variant'],r['country'],r['date'],r['rating'],r['decision']['status'],r['decision'].get('reason',''),o.get('kind',''),o.get('label',''),o.get('sentiment',''),json.dumps(o.get('evidence',[]),ensure_ascii=False),r['title'],r['body'],json.dumps(r['sources'],ensure_ascii=False)]
                w.writerow([csvcell(v) for v in row])
    print(json.dumps({'coverage':coverage,'html':str(out),'audit_csv':str(out.with_suffix('.audit.csv'))},ensure_ascii=False))
def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('inputs',nargs='+');p.add_argument('--out',required=True);p.add_argument('--mapping');p.add_argument('--encoding',default='utf-8-sig');p.add_argument('--sheet');p.add_argument('--header-row',type=int,default=1)
    for command in ['validate','render']:
        p=sub.add_parser(command);p.add_argument('--data',required=True);p.add_argument('--annotations',required=True);p.add_argument('--allow-partial',action='store_true')
        if command=='render':p.add_argument('--out',required=True)
    args=parser.parse_args()
    try:
        if args.command=='prepare':prepare(args)
        elif args.command=='validate':print(json.dumps(validate(read(args.data),read(args.annotations),args.allow_partial),ensure_ascii=False))
        else:render(args)
    except (ValueError,KeyError,OSError,TypeError) as e:print('ERROR: '+str(e),file=sys.stderr);return 1
    return 0
if __name__=='__main__':sys.exit(main())

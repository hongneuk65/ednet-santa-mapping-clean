"""Rebuild from raw inputs only. Standard library; no legacy imports or dictionaries."""
import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
AXES=('task','grammar','topic','format','accent')


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def parse_tags(value):
    return sorted({int(t) for t in value.split(';') if t.strip() and int(t)>=0})


def extract_text(block):
    if not isinstance(block,dict):return ''
    data=block.get('oneOfData',block)
    if not isinstance(data,dict):return ''
    if data.get('text'):return data['text'].strip()
    if data.get('html'):return re.sub('<[^>]+>',' ',data['html']).strip()
    def walk(node):
        if isinstance(node,dict):
            if isinstance(node.get('value'),str):yield node['value']
            for v in node.values():yield from walk(v)
        elif isinstance(node,list):
            for v in node:yield from walk(v)
    for key,value in data.items():
        if key.endswith('Json') and value:
            try:result=' '.join(walk(json.loads(value)))
            except (TypeError,ValueError):continue
            if result:return result.strip()
    return ''


def text_task(stem,part):
    s=re.sub(r'\s+',' ',stem).strip().lower()
    if part=='p2':
        for word in ('who','where','when','why','which','what','how'):
            if re.match(word+r'\b',s):return 'stem_'+word
        if re.match(r'^(is|are|was|were|do|does|did|has|have|had|can|could|will|would|should|may|must)\b',s):return 'stem_auxiliary'
    if part in ('p3','p4','p6','p7'):
        for name,pattern in (
            ('word_meaning',r'closest in meaning|most nearly means'),
            ('sentence_insertion',r'best fit|following sentence|\[1\]'),
            ('speaker_intent',r'mean when|imply when|why does .* say'),
            ('next_action',r'do next|asked to do|encouraged to|will .* most likely'),
            ('main_topic',r'mainly|primarily|main topic|mostly about|purpose of'),
            ('inference',r'suggested|implied|inferred|most likely|probably'),
            ('negative_detail',r'not (?:mentioned|indicated|stated|included|true)')):
            if re.search(pattern,s):return name
    return None


def load_config():
    policy=json.loads((ROOT/'config/policy.json').read_text(encoding='utf-8'))
    families=json.loads((ROOT/'config/label_families.json').read_text(encoding='utf-8'))
    for rule in families['rules']:re.compile(rule['pattern'])
    return policy,families


def family(code,part,families,field='metadata'):
    """One family per source code; multiple source codes can yield multiple axes."""
    if not code or code in families['exclude']:return None
    for rule in families['rules']:
        if part in rule['parts'] and re.search(rule['pattern'],code):
            return rule['axis'],rule['id'],rule['name']
    if field=='pronounce':return 'accent','accent:'+code,'Mã giọng đọc '+code
    if field=='text_task':return 'task','task:'+code,code.replace('_',' ')
    if part=='p2':axis='task'
    elif part in ('p5','p6'):axis='grammar' if not code.startswith('passage_') else 'format'
    elif part=='p7':axis='format' if code.startswith('passage_') or code.endswith('_passage') else 'task'
    else:axis='topic'
    return axis,'source:'+code,code.replace('_',' ')


def derive_features(meta,stem,families):
    features={axis:set() for axis in AXES};evidence=defaultdict(set);names={}
    codes=set(meta.get('sectionList') or [])|set(meta.get('chapterList') or [])
    if meta.get('chapter'):codes.add(meta['chapter'])
    for code in sorted(codes):
        mapped=family(str(code),meta.get('part'),families)
        if mapped:
            axis,label,name=mapped;features[axis].add(label);names[label]=name;evidence[label].add('metadata:'+code)
    task=text_task(stem,meta.get('part'))
    if task:
        axis,label,name=family(task,meta.get('part'),families,'text_task')
        features[axis].add(label);names[label]=name;evidence[label].add('text_rule:'+task)
    if meta.get('pronounce'):
        axis,label,name=family(meta['pronounce'],meta.get('part'),families,'pronounce')
        features[axis].add(label);names[label]=name;evidence[label].add('pronounce:'+meta['pronounce'])
    return {k:sorted(v) for k,v in features.items()},{k:sorted(v) for k,v in evidence.items()},names


def normalized_question(raw,meta,source,members,families):
    obj=(raw.get('oneOfTypeSpec') or {}).get('objective') or {}
    answer=(obj.get('oneOfAnswers') or {}).get('andAnswers') or []
    choices=[extract_text(c).strip().rstrip('*').strip() for c in obj.get('choices',[])]
    valid=len(answer)==1 and type(answer[0]) is int and 0<=answer[0]<len(choices)
    stem=extract_text(raw.get('description'))
    exp=raw.get('oneOfExplanationType') or {}
    exp=exp.get('explanation') or (exp.get('branchingExplanations') or {}).get('correctCase') or {}
    features,evidence,names=derive_features(meta,stem,families)
    return {'question_id':'q'+str(raw['id']),'part':meta.get('part'),'answer_indices':answer,
        'answer_valid':valid,'correct_answer':chr(97+answer[0]) if valid else None,
        'question':stem,'choices':choices,'correct_text':choices[answer[0]] if valid else '',
        'explanation':extract_text(exp),'source_raw':source,'members':sorted(members),
        'audio_resource_id':raw.get('audioResourceId'), 'raw_tag_ids':raw.get('tagIds'),
        'features':features,'feature_evidence':evidence,'label_names':names}


def load_sources(families,verify_hash=True):
    manifest=json.loads((ROOT/'data/source_manifest.json').read_text(encoding='utf-8'))
    refs=read_csv(ROOT/'data/raw/ednet/questions.csv')
    lectures=read_csv(ROOT/'data/raw/ednet/lectures.csv')
    refmap={q['question_id']:q for q in refs};lectmap={l['lecture_id']:l for l in lectures}
    if len(refmap)!=len(refs) or len(lectmap)!=len(lectures):raise ValueError('Duplicate EdNet reference ID')
    variants=defaultdict(list);lecture_matches=[];names={};raw_types=Counter();part_occurrences=Counter()
    for entry in manifest['files']:
        path=ROOT/entry['path'];raw=path.read_bytes()
        if verify_hash and hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Source hash changed: '+entry['path'])
        if path.suffix!='.json':continue
        data=json.loads(raw.decode('utf-8-sig'));meta=(data.get('oneOfDomainContent') or {}).get('toeicContent') or {}
        typed=meta.get('oneOfType') or {};raw_types[typed.get('oneOfCase','unknown')]+=1
        questions=(typed.get('questionSet') or {}).get('questions') or []
        members={'q'+str(q['id']) for q in questions}
        for q in questions:
            row=normalized_question(q,meta,entry['path'],members,families)
            row['content_id']=data['baseContent']['contentId']
            variants[row['question_id']].append(row);part_occurrences[row['part']]+=1;names.update(row.pop('label_names'))
        lesson=typed.get('lesson')
        if lesson:
            lid='l'+str(lesson['id']);ref=lectmap.get(lid)
            if ref and meta.get('part')=='p'+ref['part']:
                features,ev,nn=derive_features(meta,'',families);names.update(nn)
                lecture_matches.append({'lecture_id':lid,'part':meta['part'],'tags':parse_tags(ref['tags']),
                    'title':lesson.get('title',''),'body':extract_text(lesson.get('body')),
                    'source_raw':entry['path'],'features':features,'feature_evidence':ev,
                    'historical_identity_verified':False})
    # No duplicate lecture voting from repeated copies of a response.
    unique_lectures={}
    for l in lecture_matches:
        lid=l['lecture_id']
        if lid in unique_lectures and l!=unique_lectures[lid]:raise ValueError('Conflicting lecture source: '+lid)
        unique_lectures[lid]=l
    return refs,variants,list(unique_lectures.values()),names,manifest,dict(raw_types),dict(part_occurrences)


def signature(q):
    return json.dumps([q['part'],q['question'],q['answer_indices'],q['choices'],q['features']],sort_keys=True,ensure_ascii=False)


def join_questions(refs,variants):
    reference={q['question_id']:q for q in refs};bundle_members=defaultdict(set)
    for q in refs:bundle_members[q['bundle_id']].add(q['question_id'])
    matched=[];rejected=[];three_key_ids=set();overlap=0;conflicts=[]
    for qid,copies in sorted(variants.items()):
        ref=reference.get(qid)
        if ref is None:continue
        overlap+=1;valid=[]
        for q in copies:
            checks={'part':q['part']=='p'+ref['part'],'answer':q['answer_valid'] and q['correct_answer']==ref['correct_answer'],
                'bundle':set(q['members'])==bundle_members[ref['bundle_id']]}
            if checks['part'] and checks['answer']:three_key_ids.add(qid)
            if all(checks.values()):valid.append(q)
            else:rejected.append({'question_id':qid,'source_raw':q['source_raw'],**checks})
        if not valid:continue
        if len({signature(q) for q in valid})>1:
            conflicts.append(qid);continue
        q={k:v for k,v in valid[0].items() if k!='members'}
        q.update(tags=parse_tags(ref['tags']),bundle_id=ref['bundle_id'],all_sources=sorted({r['source_raw'] for r in valid}))
        matched.append(q)
    return matched,{'id_overlap':overlap,'three_key_matches':len(three_key_ids),'strict_matches':len(matched),
        'conflicting_valid_ids':conflicts,'rejected_variants':rejected}


def wilson(hits,n):
    if not n:return None
    z=1.96;p=hits/n
    return (p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n)


def label_rates(refs,matched,policy):
    by_tagpart=defaultdict(list);population=defaultdict(list);ref_counts=Counter()
    for q in refs:
        for tag in parse_tags(q['tags']):ref_counts[tag,'p'+q['part']]+=1
    for q in matched:
        population[q['part']].append(q)
        for tag in q['tags']:by_tagpart[tag,q['part']].append(q)
    rates=[];decisions=[]
    for (tag,part),nref in sorted(ref_counts.items()):
        subset=by_tagpart[tag,part]
        for axis in AXES:
            observed=[q for q in subset if q['features'][axis]]
            counts=Counter(label for q in observed for label in q['features'][axis])
            options=[]
            pool=[q for q in population[part] if q['features'][axis]]
            for label,hits in counts.most_common():
                label_pop=sum(label in q['features'][axis] for q in pool)
                bundles={q['bundle_id'] for q in observed if label in q['features'][axis]}
                row={'tag_id':tag,'part':part,'axis':axis,'label':label,'hits':hits,'observed':len(observed),
                    'bridge_questions':len(subset),'reference_questions':nref,'precision_observed':hits/len(observed),
                    'observed_fraction':len(observed)/len(subset),'bridge_coverage':len(subset)/nref,
                    'reference_bundle_support':len(bundles),'recall_same_part_observed':hits/label_pop,
                    'lift':(hits/len(observed))/(label_pop/len(pool)),
                    'wilson_lower_question_iid_only':wilson(hits,len(observed)),
                    'example_ids':[q['question_id'] for q in observed if label in q['features'][axis]][:5]}
                rates.append(row);options.append(row)
            if not options:continue
            options.sort(key=lambda x:(-x['precision_observed'],-x['hits'],x['label']))
            eligible=[r for r in options if r['precision_observed']>=policy['min_ratio'] and r['observed_fraction']>=policy['min_observed_fraction']]
            if not eligible:continue
            top=eligible[0];ties=[r for r in eligible if top['precision_observed']-r['precision_observed']<policy['near_tie_margin']]
            for r in ties:
                strong=r['observed']>=policy['min_questions_for_supported'] and r['reference_bundle_support']>=policy['min_bundles_for_supported']
                decisions.append({**r,'source':'question_proxy','status':'proxy_supported_not_gold' if strong else 'provisional_small_support',
                    'small_sample':r['observed']<policy['small_sample_below'],'near_tie_labels':[t['label'] for t in ties],
                    'semantic_validated':False})
    return rates,decisions,ref_counts


def add_lecture_anchors(lectures,decisions,ref_counts):
    occupied={(r['tag_id'],r['part'],r['axis']) for r in decisions}
    grouped=defaultdict(list)
    for l in lectures:
        for tag in l['tags']:
            if (tag,l['part']) in ref_counts:grouped[tag,l['part']].append(l)
    anchors=[]
    for (tag,part),ls in sorted(grouped.items()):
        found=False
        for axis in AXES:
            if (tag,part,axis) in occupied:continue
            observed=[l for l in ls if l['features'][axis]]
            if not observed:continue
            counts=Counter(label for l in observed for label in l['features'][axis])
            # Unanimous source metadata only. A single anchor stays explicitly weak.
            labels=[label for label,n in counts.items() if n==len(observed)]
            for label in labels:
                anchors.append({'tag_id':tag,'part':part,'axis':axis,'label':label,'source':'lecture_metadata',
                    'status':'lecture_anchor_pending_review','lecture_count':len(observed),
                    'lecture_ids':[l['lecture_id'] for l in observed], 'titles':[l['title'] for l in observed],
                    'source_raws':[l['source_raw'] for l in observed], 'semantic_validated':False,
                    'historical_identity_verified':False,'precision_observed':None})
                found=True
        # Preserve titles as evidence, not automatically a new fine-grained skill name.
        if not found and not any((tag,part,a) in occupied for a in AXES):
            anchors.append({'tag_id':tag,'part':part,'axis':'unassigned_title','label':None,'source':'lecture_title_evidence_only',
                'status':'title_only_pending_review','lecture_count':len(ls), 'lecture_ids':[l['lecture_id'] for l in ls],
                'titles':[l['title'] for l in ls],'source_raws':[l['source_raw'] for l in ls],
                'semantic_validated':False,'precision_observed':None})
    return anchors


def profile(qs):
    result={}
    for axis in AXES[:-1]:
        counts=Counter(l for q in qs for l in q['features'][axis]);n=sum(counts.values())
        result[axis]={k:v/n for k,v in counts.items()} if n else {}
    return result


def profile_similarity(a,b):
    values=[]
    for axis in AXES[:-1]:
        x,y=a[axis],b[axis]
        if x and y:values.append(sum(math.sqrt(x[k]*y[k]) for k in x.keys()&y.keys()))
    return sum(values)/len(values) if values else None


def make_clusters(decisions,matched,ref_counts,policy,reserved_attributes=None):
    # Reversible semantic parents: no direct transfer to unknown numeric tags.
    groups=defaultdict(list)
    for r in decisions:
        if r.get('label') and r['axis']!='accent':groups[r['axis'],r['label']].append(r)
    clusters=[]
    for (axis,label),rows in sorted(groups.items()):
        members=sorted({r['tag_id'] for r in rows})
        if len(members)<2:continue
        scopes=sorted({(r['tag_id'],r['part']) for r in rows})
        clusters.append({'cluster_id':'parent:'+axis+':'+label,'kind':'same_coarse_label_parent','axis':axis,
            'label':label,'members':members,'member_part_scopes':[{'tag_id':t,'part':p} for t,p in scopes],
            'status':'candidate_parent_not_semantic_equivalence','semantic_validated':False})
    # Cluster weak question-supported tags without inventing a skill name.
    has_semantic={(r['tag_id'],r['part']) for r in decisions if r.get('label') and r['axis'] not in ('accent','unassigned_title')}
    by_tagpart=defaultdict(list)
    for q in matched:
        for t in q['tags']:by_tagpart[t,q['part']].append(q)
    weak={k:qs for k,qs in by_tagpart.items() if k not in has_semantic and k[0] not in (reserved_attributes or set()) and len(qs)>=policy['min_cluster_questions']
          and len({q['bundle_id'] for q in qs})>=policy['min_cluster_bundles']}
    prof={k:profile(qs) for k,qs in weak.items()};scores={}
    for a,b in combinations(sorted(weak),2):
        if a[1]!=b[1]:continue
        value=profile_similarity(prof[a],prof[b])
        if value is not None:scores[a,b]=value
    components=[{k} for k in sorted(weak)]
    for (a,b),s in sorted(scores.items(),key=lambda x:(-x[1],x[0])):
        if s<policy['profile_similarity']:continue
        left=next(c for c in components if a in c);right=next(c for c in components if b in c)
        if left is right or len(left|right)>policy['max_cluster_members']:continue
        cross=[scores.get(tuple(sorted((x,y)))) for x in left for y in right]
        if all(v is not None and v>=policy['profile_similarity'] for v in cross):
            components.remove(left);components.remove(right);components.append(left|right)
    for component in components:
        if len(component)<2:continue
        members=sorted(t for t,p in component);part=next(iter(component))[1]
        sim=min(scores[tuple(sorted((a,b)))] for a,b in combinations(sorted(component),2))
        clusters.append({'cluster_id':'weak:'+part+':'+','.join(map(str,members)),
            'kind':'weak_profile_family','axis':'unassigned','label':None,'part':part,'members':members,
            'member_part_scopes':[{'tag_id':t,'part':p} for t,p in sorted(component)],
            'min_pair_similarity':sim,'status':'unnamed_family_pending_review','semantic_validated':False})
    return clusters


def evaluate(refs,decisions,clusters):
    semantic={(r['tag_id'],r['part']) for r in decisions if r.get('label') and r['axis'] not in ('accent','unassigned_title')}
    any_descriptor={(r['tag_id'],r['part']) for r in decisions if r.get('label')}
    family_only={(r['tag_id'],r['part']) for c in clusters if c['kind']=='weak_profile_family' for r in c['member_part_scopes']}
    result=[]
    for part in ['all']+['p'+str(i) for i in range(1,8)]:
        qs=refs if part=='all' else [q for q in refs if 'p'+q['part']==part]
        count=Counter()
        for q in qs:
            p='p'+q['part'];tt=set(parse_tags(q['tags']))
            known={t for t in tt if (t,p) in semantic};desc={t for t in tt if (t,p) in any_descriptor}
            count['any_semantic']+=bool(known);count['any_descriptor']+=bool(desc)
            count['all_original_tags_semantic']+=bool(tt) and tt<=known
            count['any_semantic_or_unnamed_family']+=bool(known or {t for t in tt if (t,p) in family_only})
        result.append({'part':part,'questions':len(qs),**dict(count)})
    return result


def project_questions(refs,decisions):
    """Project reviewed-in-future candidates, never claim original question labels."""
    by_tagpart=defaultdict(list)
    for decision in decisions:
        if decision.get('label'):by_tagpart[decision['tag_id'],decision['part']].append(decision)
    result=[]
    for q in refs:
        part='p'+q['part'];original=parse_tags(q['tags']);labels={a:set() for a in AXES};unknown=[]
        evidence=[]
        for t in original:
            matches=by_tagpart[t,part]
            if not any(d['axis']!='accent' for d in matches):unknown.append(t)
            for d in matches:
                labels[d['axis']].add(d['label'])
                evidence.append({'tag_id':t,'axis':d['axis'],'label':d['label'],'source':d['source'],'status':d['status']})
        result.append({'question_id':q['question_id'],'bundle_id':q['bundle_id'],'part':part,
            'original_tags':original,'proposed_labels':{a:sorted(v) for a,v in labels.items()},
            'tags_without_semantic_proposal_in_part':unknown,'projection_evidence':evidence,
            'semantic_validated':False,'basis':'tag_projection_not_original_question_content_annotation'})
    return result


def write_json(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def write_csv(name,rows,fields=None):
    fields=fields or sorted({k for r in rows for k in r})
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(row.get(k),ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k) for k in fields})


def run(verify_hash=True):
    OUT.mkdir(exist_ok=True)
    policy,families=load_config()
    refs,variants,lectures,names,manifest,raw_types,occurrences=load_sources(families,verify_hash)
    matched,audit=join_questions(refs,variants)
    rates,question_decisions,ref_counts=label_rates(refs,matched,policy)
    # A strongly attribute-associated tag is not turned into a skill because
    # a content/topic proxy happens to co-occur. This is a reservation, NOT
    # extrapolation of its accent value to other Parts.
    reserved_attributes={r['tag_id'] for r in question_decisions if r['axis']=='accent'
        and r['status']=='proxy_supported_not_gold' and r['precision_observed']>=policy['attribute_reservation_ratio']}
    suppressed=[{**r,'status':'attribute_correlate_pending_review'} for r in question_decisions
        if r['tag_id'] in reserved_attributes and r['axis']!='accent']
    question_decisions=[r for r in question_decisions if r['tag_id'] not in reserved_attributes or r['axis']=='accent']
    anchors=add_lecture_anchors(lectures,question_decisions,ref_counts)
    anchors=[r for r in anchors if r['tag_id'] not in reserved_attributes or r['axis']=='accent']
    decisions=question_decisions+anchors
    clusters=make_clusters(decisions,matched,ref_counts,policy,reserved_attributes)
    coverage=evaluate(refs,decisions,clusters)
    alltags=sorted({t for q in refs for t in parse_tags(q['tags'])})
    semantic={r['tag_id'] for r in decisions if r.get('label') and r['axis'] not in ('accent','unassigned_title')}
    descriptor={r['tag_id'] for r in decisions if r.get('label')}
    family_tags={t for c in clusters if c['kind']=='weak_profile_family' for t in c['members']}
    inventory=[]
    for t in alltags:
        qs=[q for q in refs if t in parse_tags(q['tags'])]
        maps=[r for r in decisions if r['tag_id']==t]
        inventory.append({'tag_id':t,'reference_questions':len(qs),'reference_parts':sorted({'p'+q['part'] for q in qs}),
            'bridge_questions':sum(t in q['tags'] for q in matched),
            'mappings':maps,'has_semantic_label':t in semantic,'has_any_descriptor':t in descriptor,
            'has_unnamed_family':t in family_tags,'original_tag_preserved':True})
    normalization=[]
    for qid,copies in sorted(variants.items()):
        conflict=len({signature(q) for q in copies})>1
        row={k:v for k,v in copies[0].items() if k!='members'}
        row.update(all_sources=sorted({q['source_raw'] for q in copies}),duplicate_conflict=conflict)
        normalization.append(row)
    input_hashes={entry['path']:entry['sha256'] for entry in manifest['files']}
    for p in [ROOT/'config/policy.json',ROOT/'config/label_families.json',Path(__file__)]:
        input_hashes[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    snapshot=hashlib.sha256(json.dumps(input_hashes,sort_keys=True).encode()).hexdigest()
    known_units={(r['tag_id'],r['part'],r['axis']) for r in decisions if r.get('label') and r['axis']!='accent'}
    coarse_units={(r['axis'],r['label']) for r in decisions if r.get('label') and r['axis']!='accent'}
    summary={'snapshot':snapshot,'reference_questions':len(refs),'reference_tags':len(alltags),
        'raw_content_files':sum(v for v in raw_types.values()),'raw_content_types':raw_types,
        'crawl_question_occurrences':sum(occurrences.values()),'crawl_unique_questions':len(variants),
        'crawl_questions_by_part':dict(Counter(q['part'] for q in normalization)),
        'id_overlap':audit['id_overlap'],'three_key_matches':audit['three_key_matches'],'strict_question_matches':len(matched),
        'lecture_matches':len(lectures),'tags_with_semantic_proposal':len(semantic),'tags_with_any_descriptor':len(descriptor),
        'tags_unnamed_family_only':sorted(family_tags-descriptor),'tags_without_semantic_proposal':sorted(set(alltags)-semantic),
        'question_proxy_decisions':len(question_decisions),'lecture_decisions':len(anchors),
        'reserved_attribute_tags':sorted(reserved_attributes),'suppressed_attribute_correlates':len(suppressed),
        'decision_statuses':dict(Counter(r['status'] for r in decisions)),
        'parent_clusters':sum(c['kind']=='same_coarse_label_parent' for c in clusters),
        'weak_unnamed_clusters':sum(c['kind']=='weak_profile_family' for c in clusters),
        'named_tag_part_axis_units':len(known_units),'distinct_coarse_axis_labels':len(coarse_units),
        'unit_note':'These two counts describe different resolutions, not 188 minus number of merged tags. A tag may map to multiple axes and Parts.',
        'gold_accuracy':None,'historical_identity_verified':False,'coverage':coverage}
    write_json('summary.json',summary);write_json('join_audit.json',audit)
    write_json('normalized_santa.json',normalization);write_json('matched_questions.json',matched)
    write_json('lecture_bridge.json',lectures);write_json('label_names.json',names)
    write_json('attribute_audit.json',{'reserved_attribute_tags':sorted(reserved_attributes),
        'suppressed_correlates':suppressed,'note':'Do not extrapolate accent values across Parts. Reservation prevents unrelated skill merges.'})
    write_json('tag_mapping.json',{'schema_version':1,'snapshot':snapshot,'policy':policy,'tags':inventory,'clusters':clusters,
        'limits':['No old mappings read.','Part1 question content not identified by lecture bridges.',
            'Metadata and text rules are proxies, not gold semantic skills.','Unknown labels and missing axes remain unknown.',
            'Conditional observed rates are not accuracy on all EdNet questions.','Accent codes are separate attributes.']})
    write_csv('matched_questions.csv',matched);write_csv('tag_label_rates.csv',rates)
    write_csv('mapping_decisions.csv',decisions);write_csv('clusters.csv',clusters)
    write_csv('coverage.csv',coverage);write_csv('all_tags.csv',inventory)
    write_csv('join_rejections.csv',audit['rejected_variants'])
    projections=project_questions(refs,decisions)
    write_json('ednet_question_mapping.json',projections)
    write_csv('ednet_question_mapping.csv',projections)
    write_json('run_manifest.json',{'snapshot':snapshot,'input_sha256':input_hashes,
        'reproducible':True,'external_requests':0,'legacy_mapping_inputs':0})
    write_results(summary,inventory,clusters)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


def write_results(summary,inventory,clusters):
    lines=['# Kết quả lượt chạy mới','',
        'File sinh từ pipeline hiện tại; không lấy số liệu hoặc nhãn từ báo cáo cũ.','',
        f"Snapshot: `{summary['snapshot']}`",'',
        f"- EdNet: {summary['reference_questions']:,} câu, {summary['reference_tags']} tag.",
        f"- Santa: {summary['crawl_question_occurrences']:,} lượt câu → {summary['crawl_unique_questions']:,} ID khác nhau.",
        f"- Trùng ID: {summary['id_overlap']:,}; khớp ID + Part + đáp án: {summary['three_key_matches']:,}; thêm bundle chính xác: {summary['strict_question_matches']:,}.",
        f"- Neo bài giảng ID + Part: {summary['lecture_matches']}.",
        f"- Tag có đề xuất nội dung/kỹ năng/định dạng: {summary['tags_with_semantic_proposal']}; có bất kỳ mô tả (kể cả accent): {summary['tags_with_any_descriptor']}.",
        f"- Nhóm cha cùng nhãn thô: {summary['parent_clusters']}; nhóm profile chưa đặt tên: {summary['weak_unnamed_clusters']}.",'',
        'Tag được giữ riêng vì có neo thuộc tính mạnh: '+', '.join(map(str,summary['reserved_attribute_tags']))+'. Không chuyển giá trị giọng đọc sang Part khác.','',
        '## Độ phủ theo Part','',
        'Đếm câu có ít nhất một mô tả nội dung/kỹ năng/định dạng áp dụng đúng Part; không tính riêng accent là kỹ năng.','']
    for c in summary['coverage']:
        lines.append(f"- {c['part']}: {c['any_semantic']}/{c['questions']} = {c['any_semantic']/c['questions']:.2%}; mọi tag gốc có mô tả: {c['all_original_tags_semantic']}/{c['questions']}.")
    lines+=['','## Nhóm cha có thể duyệt','',
        'Một tag có thể thuộc nhiều trục. Các nhóm có thể giao thành viên; không cộng mức giảm như các cluster rời nhau. Đây là proposal, không phải tương đương đã xác nhận.','']
    for c in clusters:
        lines.append('- '+c['cluster_id']+': tag '+', '.join(map(str,c['members']))+'; '+c['status']+'.')
    lines+=['','## Chưa chốt','',
        'Tag chưa có đề xuất nội dung/kỹ năng/định dạng: '+', '.join(map(str,summary['tags_without_semantic_proposal']))+'.','',
        'Part 1 không có question bridge. Nhãn từ metadata bài giảng chỉ là neo giả thuyết; chưa xem ảnh/nghe audio hoặc xác minh nội dung lịch sử.',
        'Các tỷ lệ là P(proxy label | tag, Part, observed). Không phải độ chính xác ngữ nghĩa của toàn EdNet. Nhãn ít mẫu được đánh dấu riêng.',
        'Chưa có independent gold hoặc đánh giá downstream. Thu gọn không tự động làm tăng chất lượng.',
        'Duyệt taxonomy và mẫu phản chứng trước khi chốt. Giữ tag gốc để đảo ngược phép chiếu.','']
    (ROOT/'docs/RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--skip-hash-check',action='store_true')
    run(not parser.parse_args().skip_hash_check)

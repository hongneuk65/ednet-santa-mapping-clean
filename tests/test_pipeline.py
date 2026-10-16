import ast
import copy
import json
import unittest
from pathlib import Path

from src.pipeline import (ROOT,AXES,extract_text,family,load_config,normalized_question,
    join_questions,label_rates,make_clusters,profile_similarity,parse_tags,project_questions)


def features(**labels):
    return {axis:labels.get(axis,[]) for axis in AXES}


def question(qid='q1',part='p2',answer='a',bundle='b1',labels=None,tag=1):
    return {'question_id':qid,'part':part,'correct_answer':answer,'answer_valid':True,
        'answer_indices':[ord(answer)-97],'question':'How are you?','choices':['A','B','C'],
        'features':features(task=['p2_how']) if labels is None else labels,
        'source_raw':'fixture.json','members':[qid],'tags':[tag],'bundle_id':bundle}


class UnitTests(unittest.TestCase):
    def test_extract_and_numeric_tags(self):
        block={'oneOfData':{'rrtV2BlockElementsJson':json.dumps({'children':[['text',{'value':'abc'}]]})}}
        self.assertEqual(extract_text(block),'abc')
        self.assertEqual(extract_text({'oneOfData':None}),'')
        self.assertEqual(parse_tags('3;2;3;-1'),[2,3])

    def test_single_choice_not_star_and_out_of_range(self):
        _,fam=load_config()
        obj={'id':'1','oneOfTypeSpec':{'objective':{'oneOfAnswers':{'andAnswers':[1]},
            'choices':[{'oneOfData':{'text':'wrong*'}},{'oneOfData':{'text':'right'}}]}}}
        q=normalized_question(obj,{'part':'p2'},'fixture',{'q1'},fam)
        self.assertEqual(q['correct_text'],'right');self.assertEqual(q['correct_answer'],'b')
        obj['oneOfTypeSpec']['objective']['oneOfAnswers']['andAnswers']=[5]
        self.assertFalse(normalized_question(obj,{'part':'p2'},'fixture',{'q1'},fam)['answer_valid'])

    def test_family_not_hardcoded_tag_and_specific_before_generic(self):
        _,fam=load_config()
        self.assertEqual(family('present_vs_past_participle','p5',fam)[1],'participle')
        self.assertEqual(family('portrait_garden','p1',fam)[1],'p1_work_care')
        self.assertIsNone(family('listening','p4',fam))
        self.assertNotEqual(family('portrait_garden','p4',fam)[1],'p1_work_care')
        for rule in fam['rules']:self.assertNotIn('tags',rule)

    def test_strict_bundle_rejection(self):
        refs=[{'question_id':'q1','bundle_id':'b1','part':'2','correct_answer':'a','tags':'1'},
              {'question_id':'q2','bundle_id':'b1','part':'2','correct_answer':'a','tags':'1'}]
        row=question();matched,audit=join_questions(refs,{'q1':[row]})
        self.assertEqual(len(matched),0)
        self.assertEqual(audit['three_key_matches'],1)
        self.assertFalse(audit['rejected_variants'][0]['bundle'])

    def test_conflicts_fail_closed_and_opaque_ids_not_recast(self):
        refs=[{'question_id':'q1','bundle_id':'b1','part':'2','correct_answer':'a','tags':'1'}]
        a=question();b=copy.deepcopy(a);b['choices']=['X','B','C']
        matched,audit=join_questions(refs,{'q1':[a,b],'qabc-1':[a]})
        self.assertEqual(matched,[]);self.assertEqual(audit['id_overlap'],1)
        self.assertEqual(audit['conflicting_valid_ids'],['q1'])

    def test_denominator_missingness_not_zero_or_perfect(self):
        policy,_=load_config()
        rows=[question('q'+str(i),bundle='b'+str(i),labels=features(task=['p2_how']) if i==0 else features()) for i in range(8)]
        refs=[{'question_id':r['question_id'],'bundle_id':r['bundle_id'],'part':'2','correct_answer':'a','tags':'1'} for r in rows]
        rates,decisions,_=label_rates(refs,rows,policy)
        self.assertEqual(rates[0]['precision_observed'],1)
        self.assertEqual(rates[0]['observed_fraction'],1/8)
        self.assertEqual(decisions,[])

    def test_near_ties_keep_both(self):
        policy,_=load_config()
        rows=[question('q'+str(i),bundle='b'+str(i),labels=features(task=['a','b'])) for i in range(4)]
        refs=[{'question_id':r['question_id'],'bundle_id':r['bundle_id'],'part':'2','correct_answer':'a','tags':'1'} for r in rows]
        _,decisions,_=label_rates(refs,rows,policy)
        self.assertEqual({r['label'] for r in decisions},{'a','b'})
        self.assertTrue(all(r['small_sample'] for r in decisions))

    def test_empty_profiles_are_not_identical(self):
        empty={axis:{} for axis in AXES[:-1]}
        self.assertIsNone(profile_similarity(empty,empty))

    def test_reserved_attribute_tags_cannot_join_weak_skill_families(self):
        policy,_=load_config()
        rows=[]
        for i in range(6):
            q=question('q'+str(i),bundle='b'+str(i));q['tags']=[1,2];rows.append(q)
        groups=make_clusters([],rows,{},policy,reserved_attributes={2})
        self.assertFalse(any(2 in g['members'] for g in groups))

    def test_parent_axes_and_scopes_not_erased(self):
        policy,_=load_config()
        decisions=[{'tag_id':1,'part':'p2','axis':'task','label':'x'},
                   {'tag_id':2,'part':'p2','axis':'task','label':'x'},
                   {'tag_id':3,'part':'p4','axis':'accent','label':'accent:amw'}]
        clusters=make_clusters(decisions,[],{},policy)
        self.assertEqual(len(clusters),1)
        self.assertEqual(clusters[0]['members'],[1,2])
        self.assertEqual(clusters[0]['member_part_scopes'],[{'tag_id':1,'part':'p2'},{'tag_id':2,'part':'p2'}])

    def test_no_legacy_imports_or_absolute_input_paths(self):
        source=(ROOT/'src/pipeline.py').read_text(encoding='utf-8')
        tree=ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                self.assertNotIn(node.module or '',['map_tags','refine_mapping','build_inventory'])
        self.assertNotIn('tag_mapping_research',source)
        self.assertNotIn('reverse_tag_pipeline',source)
        self.assertNotIn('D:\\NEU',source)

    def test_question_projection_does_not_widen_part_or_hide_unknown(self):
        refs=[{'question_id':'q1','bundle_id':'b1','part':'1','tags':'1;2'},
              {'question_id':'q2','bundle_id':'b2','part':'4','tags':'1;2'}]
        ds=[{'tag_id':1,'part':'p1','axis':'topic','label':'x','source':'fixture','status':'pending'},
            {'tag_id':2,'part':'p4','axis':'accent','label':'y','source':'fixture','status':'pending'}]
        projected=project_questions(refs,ds)
        self.assertEqual(projected[0]['original_tags'],[1,2])
        self.assertEqual(projected[0]['tags_without_semantic_proposal_in_part'],[2])
        self.assertEqual(projected[1]['proposed_labels']['topic'],[])
        self.assertEqual(projected[1]['tags_without_semantic_proposal_in_part'],[1,2])


@unittest.skipUnless((ROOT/'outputs/summary.json').exists(),'Run pipeline for integration tests')
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=json.loads((ROOT/'outputs/summary.json').read_text(encoding='utf-8'))
        cls.mapping=json.loads((ROOT/'outputs/tag_mapping.json').read_text(encoding='utf-8'))
        cls.matched=json.loads((ROOT/'outputs/matched_questions.json').read_text(encoding='utf-8'))

    def test_dedup_and_independent_reference_counts(self):
        self.assertEqual(len(self.matched),len({q['question_id'] for q in self.matched}))
        self.assertFalse(any(q['part']=='p1' for q in self.matched))
        from src.pipeline import read_csv
        refs=read_csv(ROOT/'data/raw/ednet/questions.csv')
        self.assertEqual(len(refs),self.summary['reference_questions'])
        self.assertEqual({t for q in refs for t in parse_tags(q['tags'])},{r['tag_id'] for r in self.mapping['tags']})

    def test_scope_exact_and_no_false_gold(self):
        for row in self.mapping['tags']:
            for decision in row['mappings']:
                self.assertIn(decision['part'],row['reference_parts'])
                self.assertFalse(decision['semantic_validated'])
        self.assertIsNone(self.summary['gold_accuracy'])
        reserved=set(self.summary['reserved_attribute_tags'])
        for group in self.mapping['clusters']:
            self.assertFalse(set(group['members']) & reserved)

    def test_coverage_recomputed_without_dropping_unknown(self):
        from src.pipeline import read_csv
        refs=read_csv(ROOT/'data/raw/ednet/questions.csv')
        semantic={(r['tag_id'],d['part']) for r in self.mapping['tags'] for d in r['mappings']
            if d.get('label') and d['axis'] not in ('accent','unassigned_title')}
        for c in self.summary['coverage']:
            rows=refs if c['part']=='all' else [q for q in refs if 'p'+q['part']==c['part']]
            known=lambda q:{t for t in parse_tags(q['tags']) if (t,'p'+q['part']) in semantic}
            self.assertEqual(c['any_semantic'],sum(bool(known(q)) for q in rows))
            self.assertEqual(c['all_original_tags_semantic'],sum(bool(parse_tags(q['tags'])) and set(parse_tags(q['tags']))<=known(q) for q in rows))


if __name__=='__main__':unittest.main()

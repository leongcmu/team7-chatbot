"""Evaluate the 13 knowledge-base questions plus three rewordings each."""
import argparse
import json
from pathlib import Path

from backend.config import ROOT
from backend.embeddings import embedding_search
from backend.knowledge_base import approved, records
from backend.retrieval import search


def lexical_ids(question: str) -> list[str]:
    matches=[]
    matches+=search(question,records('faqs.json'),kind='faq',limit=3,min_score=0.30)
    matches+=search(question,records('courses.json'),kind='course',limit=3,min_score=0.30)
    return [item['id'] for item in sorted(matches,key=lambda item:-item['score'])]


def approved_ids(record_ids: list[str]) -> list[str]:
    allowed={
        item['id'] for filename in ('faqs.json','courses.json','blog_posts.json')
        for item in records(filename) if approved(item)
    }
    return [record_id for record_id in record_ids if record_id in allowed]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lexical',action='store_true',help='Run the old spelling baseline')
    parser.add_argument('--output',type=Path,help='Optionally write the complete JSON report')
    args=parser.parse_args()
    cases=json.loads((ROOT/'data'/'evaluation_questions.json').read_text())
    flattened=[(case,question) for case in cases for question in case['questions']]
    rows=[]
    for case,question in flattened:
        actual=approved_ids(
            lexical_ids(question) if args.lexical else
            [hit.record_id for hit in embedding_search(question)]
        )
        expected=case['expected_id']
        passed=(expected in actual) if expected else not actual
        rows.append({'question':question,'expected':expected,'actual':actual,'passed':passed})
    passed=sum(row['passed'] for row in rows)
    mode='lexical baseline' if args.lexical else 'embedding search'
    print(f'{mode}: {passed}/{len(rows)} ({passed/len(rows):.1%})')
    for row in rows:
        if not row['passed']:
            print(json.dumps(row,ensure_ascii=False))
    if args.output:
        report={'mode':mode,'passed':passed,'total':len(rows),'accuracy':passed/len(rows),'rows':rows}
        args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()

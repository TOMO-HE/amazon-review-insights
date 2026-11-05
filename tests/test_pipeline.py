import argparse, contextlib, copy, importlib.util, io, json, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review_tool',ROOT/'amazon-review-insights/scripts/review_tool.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)

class PipelineTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'work').mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'work');self.work=Path(self.tmp.name)
        args=argparse.Namespace(inputs=[str(ROOT/'examples/reviews.csv')],out=self.work/'prepared.json',mapping=None,encoding='utf-8-sig',sheet=None,header_row=1)
        with contextlib.redirect_stdout(io.StringIO()):self.data=tool.prepare(args)
        self.annotations=tool.read(ROOT/'examples/annotations.json')
    def tearDown(self):
        self.assertTrue(self.work.resolve().is_relative_to((ROOT/'work').resolve()))
        self.tmp.cleanup()
    def test_example_and_duplicate_ids(self):
        self.assertEqual(tool.validate(self.data,self.annotations),{'prepared':5,'analyzed':4,'excluded':1,'pending':0})
        self.assertEqual(self.data['quality']['duplicate_ids'],1)
        self.assertEqual(len(self.data['reviews'][0]['sources']),2)
        self.assertIsNone(self.data['reviews'][-1]['rating'])
    def test_fabricated_quote_rejected(self):
        self.annotations['decisions'][0]['observations'][0]['evidence'][0]['quote']='an invented quotation'
        with self.assertRaisesRegex(ValueError,'evidence not found'):tool.validate(self.data,self.annotations)
    def test_partial_is_explicit(self):
        self.annotations['decisions'].pop()
        with self.assertRaisesRegex(ValueError,'pending'):tool.validate(self.data,self.annotations)
        self.assertEqual(tool.validate(self.data,self.annotations,True)['pending'],1)
    def test_stale_data_rejected(self):
        self.data['reviews'][0]['body']='Changed text'
        with self.assertRaisesRegex(ValueError,'fingerprint'):tool.validate(self.data,self.annotations)
    def test_duplicate_polarity_rejected(self):
        obs=self.annotations['decisions'][0]['observations'];obs.append(copy.deepcopy(obs[0]))
        with self.assertRaisesRegex(ValueError,'duplicate observation'):tool.validate(self.data,self.annotations)
    def test_conflicting_id_blocks_publication(self):
        self.data['quality']['conflicts']=[{'id':'demo-1'}]
        self.data['review_set_sha256']=tool.fingerprint(self.data['reviews'],self.data['quality'])
        self.annotations['review_set_sha256']=self.data['review_set_sha256']
        with self.assertRaisesRegex(ValueError,'conflicting duplicate'):tool.validate(self.data,self.annotations)
    def test_render_and_export_escape(self):
        tool.dump(self.work/'a.json',self.annotations)
        with contextlib.redirect_stdout(io.StringIO()):tool.render(argparse.Namespace(data=self.work/'prepared.json',annotations=self.work/'a.json',out=self.work/'report.html',allow_partial=False))
        text=(self.work/'report.html').read_text(encoding='utf-8')
        self.assertNotIn('</script><script>window.injected',text)
        self.assertIn('\\u003c/script',text)
        self.assertNotIn('__DATA__',text)
        self.assertIn("'=DEMO()",(self.work/'report.audit.csv').read_text(encoding='utf-8-sig'))
    def test_unknown_and_dates(self):
        self.assertEqual(tool.parse_rating('4.0 out of 5 stars'),4)
        self.assertIsNone(tool.parse_rating('7'))
        self.assertEqual(tool.parse_date('2026/10/01'),'2026-10-01')
        self.assertIsNone(tool.parse_date('01/02/26'))

if __name__=='__main__':unittest.main()

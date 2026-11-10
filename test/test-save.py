import importlib.util,json,tempfile,unittest,urllib.error
from pathlib import Path
s=importlib.util.spec_from_file_location('save',Path(__file__).resolve().parents[1]/'save-invoices.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Response:
 status=201
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,n):return b'{"id":"saved"}'
class Tests(unittest.TestCase):
 def test_default_never_uploads(self):
  self.assertEqual(m.save(['missing'],{},lambda *a,**kw:self.fail('upload')),0)
 def test_explicit_upload_exact_input(self):
  with tempfile.TemporaryDirectory()as t:
   p=Path(t)/'invoice.xml';p.write_text('<Invoice>exact</Invoice>');seen=[]
   def send(req,**kw):seen.append(req);return Response()
   self.assertEqual(m.save([str(p),str(p)],{'INPUT_SAVE_FOR_RULE_CHANGES':'true','INPUT_XSDHUB_API_KEY':'test','INPUT_INVOICE_STANDARD':'xrechnung'},send),1)
   self.assertEqual(json.loads(seen[0].data)['xml'],p.read_text());self.assertTrue(json.loads(seen[0].data)['consent']);self.assertEqual(seen[0].full_url,m.URL)
 def test_missing_key_no_upload(self):
  with self.assertRaises(ValueError):m.save(['missing'],{'INPUT_SAVE_FOR_RULE_CHANGES':'true'},lambda *a:self.fail('upload'))
 def test_no_redirect(self):self.assertIsNone(m.NoRedirect().redirect_request(None,None,302,None,None,'https://elsewhere.example'))
unittest.main()

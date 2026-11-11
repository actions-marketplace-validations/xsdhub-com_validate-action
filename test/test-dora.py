import contextlib,importlib.util,io,json,os,tempfile,unittest,urllib.request
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location('dora',Path(__file__).resolve().parents[1]/'dora.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Response(io.BytesIO):
 def __enter__(self):return self
 def __exit__(self,*a):pass
class Tests(unittest.TestCase):
 def run_case(self,env,answer=None):
  seen=[]
  class Opener:
   def open(self,req,**kwargs):seen.append(req);return Response(json.dumps(answer).encode())
  out=io.StringIO()
  with patch.dict(os.environ,env,clear=True),patch.object(urllib.request,'build_opener',return_value=Opener()),contextlib.redirect_stdout(out):code=m.main()
  return code,out.getvalue(),seen
 def test_consent_before_file_access_or_network(self):
  code,out,seen=self.run_case({'INPUT_FILES':'missing.zip'});self.assertEqual(code,2);self.assertFalse(seen);self.assertIn('allow-upload',out)
 def test_exact_request_and_no_source_content_in_logs(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'register.zip';p.write_bytes(b'PRIVATE_REGISTER_BYTES');output=Path(d)/'out';summary=Path(d)/'summary'
   answer={'ok':True,'dora':{'findingCount':0,'coverage':[{'state':'checked'}]*14,'findings':[{'message':'PRIVATE_RESPONSE'}]}}
   code,out,seen=self.run_case({'INPUT_FILES':str(p),'INPUT_ALLOW_UPLOAD':'true','INPUT_DORA_PROFILE':'eba-4.0','GITHUB_OUTPUT':str(output),'GITHUB_STEP_SUMMARY':str(summary)},answer)
   self.assertEqual(code,0);self.assertEqual(json.loads(seen[0].data)['files'][0]['contentBase64'],'UFJJVkFURV9SRUdJU1RFUl9CWVRFUw==');self.assertNotIn('PRIVATE',out+summary.read_text());self.assertIn('checked=1',output.read_text());self.assertEqual(seen[0].full_url,'https://xsdhub.com/api/validate')
 def test_findings_and_incomplete_coverage_fail(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'register.zip';p.write_bytes(b'x')
   for answer in [{'ok':False,'dora':{'findingCount':1,'coverage':[{'state':'checked'}]*14}},{'ok':True,'dora':{'findingCount':0,'coverage':[{'state':'missing'}]*14}}]:
    code,_,_=self.run_case({'INPUT_FILES':str(p),'INPUT_ALLOW_UPLOAD':'true'},answer);self.assertEqual(code,1)
 def test_explicit_findings_override_keeps_failure_count(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'register.zip';p.write_bytes(b'x');output=Path(d)/'outputs'
   code,_,_=self.run_case({'INPUT_FILES':str(p),'INPUT_ALLOW_UPLOAD':'true','INPUT_FAIL_ON_ERROR':'false','GITHUB_OUTPUT':str(output)},{'ok':False,'dora':{'findingCount':1,'coverage':[{'state':'checked'}]*14}})
   self.assertEqual(code,0);self.assertIn('failed=1',output.read_text())
 def test_no_false_success_from_failed_or_malformed_response(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'register.zip';p.write_bytes(b'x')
   code,_,_=self.run_case({'INPUT_FILES':str(p),'INPUT_ALLOW_UPLOAD':'true','INPUT_FAIL_ON_ERROR':'false'},{'error':'PRIVATE_ERROR'});self.assertEqual(code,2)
 def test_mixed_schema_or_saving_never_uploads(self):
  for more in [{'INPUT_SCHEMA':'schema.xsd'},{'INPUT_SAVE_FOR_RULE_CHANGES':'true'}]:
   code,_,seen=self.run_case({'INPUT_ALLOW_UPLOAD':'true',**more});self.assertEqual(code,2);self.assertFalse(seen)
 def test_symlink_and_mixed_formats_never_upload(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'register.zip';p.write_bytes(b'x');link=Path(d)/'other.zip';link.symlink_to(p)
   code,_,seen=self.run_case({'INPUT_FILES':str(link),'INPUT_ALLOW_UPLOAD':'true'});self.assertEqual(code,2);self.assertFalse(seen)
if __name__=='__main__':unittest.main(verbosity=2)

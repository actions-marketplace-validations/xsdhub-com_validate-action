"""Explicit transient DORA API mode. CI logs contain aggregate counts only."""
import base64,glob,json,os,re,sys,urllib.request
from pathlib import Path

def main():
 try:
  if os.environ.get('INPUT_ALLOW_UPLOAD','false')!='true':raise ValueError('Set allow-upload: true to send this register to XSDHub, or use the private browser check at https://xsdhub.com/standards/dora-roi.')
  if os.environ.get('INPUT_SCHEMA','')or os.environ.get('INPUT_SAVE_FOR_RULE_CHANGES','false')!='false':raise ValueError('Use DORA separately from XML schemas and invoice saving.')
  profile=os.environ.get('INPUT_DORA_PROFILE','eba-4.0');fail=os.environ.get('INPUT_FAIL_ON_ERROR','true')
  if profile not in ('eba-4.0','dnb-4.0')or fail not in ('true','false'):raise ValueError('Choose a supported DORA profile and true/false fail-on-error.')
  patterns=os.environ.get('INPUT_FILES','').splitlines();paths=[];seen=set()
  for pattern in patterns:
   pattern=pattern.strip()
   if not pattern:continue
   for f in glob.iglob(pattern,recursive=True):
    p=Path(f)
    if p.is_symlink()or not p.is_file():raise ValueError('Choose ordinary register files, without symlinks.')
    if p.resolve()in seen:continue
    seen.add(p.resolve());paths.append(p)
    if len(paths)>32:raise ValueError('Choose one ZIP/workbook or up to 32 CSV tables.')
  if not paths:raise ValueError('No register files matched. Use one glob pattern per line.')
  names=[p.name.lower()for p in paths]
  if len(set(names))!=len(names):raise ValueError('Each selected register table must have a unique file name.')
  if not ((len(paths)==1 and names[0].endswith('.xlsx')and profile=='dnb-4.0')or(profile=='eba-4.0'and((len(paths)==1 and names[0].endswith('.zip'))or all(n.endswith('.csv')for n in names)))):raise ValueError('Choose one DNB XLSX or an EBA ZIP/CSV table set with its matching profile.')
  files=[];total=0
  for p in paths:
   if not 0<p.stat().st_size<=2097152:raise ValueError('Select nonempty register files up to 2 MiB.')
   with p.open('rb')as handle:b=handle.read(2097153)
   total+=len(b)
   if total>2097152:raise ValueError('Maximum combined size is 2 MiB. Check one entity at a time.')
   files.append({'name':p.name,'contentBase64':base64.b64encode(b).decode('ascii')})
  key=os.environ.get('INPUT_XSDHUB_API_KEY','')
  if key and not re.fullmatch(r'xsdh_[a-f0-9]{32}_[a-f0-9]{64}',key):raise ValueError('Use the existing API key from an Actions secret.')
  req=urllib.request.Request('https://xsdhub.com/api/validate',data=json.dumps({'engine':'dora','consent':True,'profile':profile,'files':files}).encode(),headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+key}if key else{})},method='POST')
  try:
   class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
   with urllib.request.build_opener(NoRedirect()).open(req,timeout=25)as r:raw=r.read(500001)
   if len(raw)>500000:raise ValueError()
   result=json.loads(raw);report=result['dora'];count=report['findingCount'];coverage=report['coverage']
   if type(count)is not int or count<0 or not isinstance(coverage,list)or len(coverage)!=14 or type(result.get('ok'))is not bool:raise ValueError()
  except Exception:raise ValueError('DORA check did not complete. Check the file/profile, quota reset and API key, then retry. No response content was logged.')
  failed=0 if result['ok']is True and count==0 and not report.get('truncated')and all(c.get('state')=='checked'for c in coverage)else 1
  output=os.environ.get('GITHUB_OUTPUT')
  if output:
   with open(output,'a')as f:f.write('checked=1\nfailed='+str(failed)+'\n')
  msg=f'DORA limited check: {count} findings; {sum(c.get("state")=="checked"for c in coverage)}/14 tables checked.'
  print(msg)
  if failed:print('::'+('error'if fail=='true'else'warning')+'::The register has findings or incomplete coverage. Review its source cells in https://xsdhub.com/standards/dora-roi and rerun your authority filing tests.')
  summary=os.environ.get('GITHUB_STEP_SUMMARY')
  if summary:
   with open(summary,'a')as f:f.write('### DORA register check\n\n'+msg+'\n\nYou authorised a transient XSDHub server check. This checks keys and listed references, not every DORA rule. Correct the source register, rerun the check, then use your authority filing tests. [Open the DORA validator](https://xsdhub.com/standards/dora-roi). No register content or result artifact was saved by this Action.\n')
  return 1 if failed and fail=='true'else 0
 except ValueError as e:print('::error::'+str(e));return 2
 except Exception:print('::error::Could not read the selected register files. Check their size and permissions.');return 2
if __name__=='__main__':sys.exit(main())

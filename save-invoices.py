#!/usr/bin/env python3
"""Explicit invoice retention for the existing XSDHub account API."""
import json, os, sys, urllib.error, urllib.request
from pathlib import Path
STANDARDS={'en16931','xrechnung','facturx','ksef','ro','hr'}
URL='https://xsdhub.com/api/account/saved-invoices'

def save(files,env=os.environ,opener=urllib.request.urlopen):
    if env.get('INPUT_SAVE_FOR_RULE_CHANGES')!='true':return 0
    key=env.get('INPUT_XSDHUB_API_KEY','');standard=env.get('INPUT_INVOICE_STANDARD','')
    if not key or standard not in STANDARDS:raise ValueError('Choose an invoice standard and pass your existing XSDHub Pro or Team API key as a secret.')
    # Preflight every byte before the first upload; defaults never send a document.
    invoices=[]
    for name in dict.fromkeys(files):
        p=Path(name)
        if not p.is_file()or p.stat().st_size>1048576:raise ValueError('Choose invoice XML files up to 1 MB each.')
        try:xml=p.read_bytes().decode('utf-8')
        except UnicodeDecodeError:raise ValueError('Save invoice XML as UTF-8 before choosing automatic checks.')
        invoices.append({'name':p.name[:100],'standard':standard,'xml':xml,'consent':True,**({'projectId':env['INPUT_PROJECT_ID']}if env.get('INPUT_PROJECT_ID')else{})})
    for invoice in invoices:
        req=urllib.request.Request(URL,data=json.dumps(invoice).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
        try:
            # Never follow a redirect with the API credential or invoice content.
            with opener(req,timeout=55)as response:
                if response.status!=201:raise ValueError('The invoice was not saved. Open your XSDHub account and try again.')
                result=json.loads(response.read(2*1048576))
                if not result.get('id'):raise ValueError('XSDHub did not confirm invoice saving.')
        except urllib.error.HTTPError as e:
            route={401:'Check your XSDHub API key.',402:'Choose Pro or Team in your XSDHub account.',409:'Review your saved invoices and delete an older one before saving again.'}.get(e.code,'Open your XSDHub account to retry invoice saving.')
            raise ValueError(f'Invoice saving returned HTTP {e.code}. '+route)
    return len(invoices)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

if __name__=='__main__':
    try:
        opener=urllib.request.build_opener(NoRedirect())
        count=save(sys.argv[1:],opener=opener.open)
        print(f'XSDHub: {count} invoice(s) saved for automatic checks after official rule changes.')
    except Exception as e:
        print('::error::'+(str(e)if isinstance(e,ValueError)else'Invoice saving could not finish. Review your account before retrying.'));sys.exit(1)

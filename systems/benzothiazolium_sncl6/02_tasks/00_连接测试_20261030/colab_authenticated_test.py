"""Use the project-specific ADC to inspect existing Colab runtimes; never allocate one."""
import os,json,pathlib,argparse,datetime
import google.auth
from google.auth.transport.requests import AuthorizedSession,Request
from colab_cli.client import Client,Prod
from colab_cli.runtime import ColabRuntime
root=pathlib.Path(__file__).resolve().parent
project=root.parent.parent
authroot=project/'连接配置'/'colab-cli'/'gcloud-auth'
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=str(authroot/'application_default_credentials.json')
os.environ['CLOUDSDK_CONFIG']=str(authroot)
os.environ['COLAB_CLI_REQUEST_TIMEOUT']='25'
p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');args=p.parse_args()
result={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime_created':False}
try:
 creds,_=google.auth.default();creds.refresh(Request())
 sess=AuthorizedSession(creds);client=Client(Prod(),sess)
 identity=sess.get('https://www.googleapis.com/oauth2/v2/userinfo',timeout=20)
 result['identity_http_status']=identity.status_code
 if identity.ok: result['email']=identity.json().get('email')
 assignments=client.list_assignments()
 result['sessions']=[{'endpoint':a.endpoint,'accelerator':a.accelerator.value,'machine_shape':a.machine_shape.name} for a in assignments]
 result['connection_ok']=True
 try: result['consumption']=client.get_consumption_user_info().model_dump(mode='json')
 except Exception as e: result['consumption_error_type']=type(e).__name__
 if args.execute:
  if len(assignments)!=1:
   result['execution_status']='needs_one_unambiguous_existing_runtime'
  else:
   a=assignments[0]
   runtime=ColabRuntime(a.runtime_proxy_info.url,a.runtime_proxy_info.token)
   code=(root/'colab_runtime_diagnostics.py').read_text(encoding='utf-8')
   outputs=runtime.execute_code(code,timeout=50)
   result['diagnostic_outputs']=outputs
   result['execution_status']='error' if any(x.get('output_type')=='error' for x in outputs) else 'completed'
except Exception as e:
 result['connection_ok']=False
 result['error_type']=type(e).__name__
 result['http_status']=getattr(getattr(e,'response',None),'status_code',None)
(root/'colab_authenticated_test.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
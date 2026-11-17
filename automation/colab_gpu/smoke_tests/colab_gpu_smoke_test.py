import os,json,pathlib,uuid,datetime,time,logging
import google.auth
from google.auth.transport.requests import AuthorizedSession,Request
from colab_cli.client import Client,Prod,Variant,Accelerator,Assignment
from colab_cli.runtime import ColabRuntime
from colab_cli.contents import ContentsClient
from colab_cli.state import SessionState
root=pathlib.Path(__file__).resolve().parent
project=root.parent.parent
authroot=project/'连接配置'/'colab-cli'/'gcloud-auth'
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=str(authroot/'application_default_credentials.json')
os.environ['CLOUDSDK_CONFIG']=str(authroot)
os.environ['COLAB_CLI_REQUEST_TIMEOUT']='45'
os.environ['COLAB_CLI_ASSIGN_RETRIES']='1'
logging.basicConfig(level=logging.ERROR)
creds,_=google.auth.default();creds.refresh(Request())
client=Client(Prod(),AuthorizedSession(creds))
notebook_id=uuid.uuid4();endpoint=None;runtime=None
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'notebook_request_id':str(notebook_id),'requested_gpu':'T4','runtime_created':False}
reportfile=root/'colab_gpu_smoke_test.json'
def save(): reportfile.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def stage(message): print(message,flush=True);report['stage']=message;save()
try:
 before=client.list_assignments()
 report['assignments_before']=len(before)
 if before: raise RuntimeError('Existing runtimes appeared; test allocation skipped to preserve them')
 report['consumption_before']=client.get_consumption_user_info().model_dump(mode='json')
 stage('Allocating one temporary T4 runtime')
 a=client.assign(notebook_id,variant=Variant.GPU,accelerator=Accelerator.T4)
 endpoint=a.endpoint
 report.update(runtime_created=True,endpoint=endpoint)
 stage('Runtime allocated; testing file upload and Python execution')
 s=SessionState(name='codex-connection-test',token=a.runtime_proxy_info.token,url=a.runtime_proxy_info.url,endpoint=endpoint,variant='GPU',accelerator='T4')
 contents=ContentsClient(s)
 nonce=str(uuid.uuid4())
 inputfile=root/'colab_roundtrip_input.json';inputfile.write_text(json.dumps({'connection_test_nonce':nonce}),encoding='utf-8')
 contents.upload(str(inputfile),'content/codex_connection_test_input.json')
 report['upload_ok']=True
 runtime=ColabRuntime(s.url,s.token,session_name=s.name)
 code=(root/'colab_runtime_diagnostics.py').read_text(encoding='utf-8')
 code+='\ntry:\n import torch\n report["torch_cuda_available"]=torch.cuda.is_available()\n if report["torch_cuda_available"]:\n  report["cuda_sum_0_to_1023"]=torch.arange(1024,device="cuda").sum().item()\nexcept Exception as e:\n report["cuda_test_error_type"]=type(e).__name__\n'
 code+='\nreport["connection_test_nonce"]=json.loads(pathlib.Path("/content/codex_connection_test_input.json").read_text())["connection_test_nonce"]\npathlib.Path("/content/codex_connection_test_result.json").write_text(json.dumps(report,indent=2))\nprint("GPU_DIAGNOSTICS",json.dumps(report))\n'
 outputs=runtime.execute_code(code,timeout=90)
 report['execution_output']=outputs
 report['python_execution_ok']=not any(o.get('output_type')=='error' for o in outputs)
 if not report['python_execution_ok']: raise RuntimeError('Remote diagnostic execution returned an error')
 stage('Python execution completed; downloading diagnostic result')
 resultfile=root/'colab_gpu_remote_result.json'
 contents.download('content/codex_connection_test_result.json',str(resultfile))
 result=json.loads(resultfile.read_text())
 report['download_ok']=True
 report['roundtrip_ok']=result['connection_test_nonce']==nonce
 report['remote_diagnostics']=result
 if not report['roundtrip_ok']: raise RuntimeError('Roundtrip content mismatch')
 stage('GPU and file roundtrip test completed')
except Exception as e:
 report['error_type']=type(e).__name__
 report['http_status']=getattr(getattr(e,'response',None),'status_code',None)
 print('TEST_ERROR',report['error_type'],'http_status',report['http_status'],flush=True)
finally:
 if runtime is not None and runtime._kernel_client is not None:
  try: runtime._kernel_client.stop(shutdown_kernel=False)
  except Exception: pass
 if endpoint is None and report.get('stage')=='Allocating one temporary T4 runtime':
  try:
   a=client._get_assignment(notebook_id,variant=Variant.GPU,accelerator=Accelerator.T4)
   if isinstance(a,Assignment): endpoint=a.endpoint;report.update(runtime_created=True,endpoint=endpoint)
  except Exception as e: report['reconcile_error_type']=type(e).__name__
 if endpoint:
  stage('Releasing the temporary test runtime')
  try:
   client.unassign(endpoint)
   remaining=client.list_assignments()
   report['test_runtime_released']=all(x.endpoint!=endpoint for x in remaining)
   report['assignments_after']=len(remaining)
  except Exception as e: report['release_error_type']=type(e).__name__
 try: report['consumption_after']=client.get_consumption_user_info().model_dump(mode='json')
 except Exception as e: report['consumption_after_error_type']=type(e).__name__
 report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 save()
 print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
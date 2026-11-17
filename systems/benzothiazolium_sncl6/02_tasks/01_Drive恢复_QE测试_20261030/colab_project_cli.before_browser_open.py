import os,sys,pathlib
root=pathlib.Path(__file__).resolve().parent
project=root.parent.parent
tool=project/'连接配置'/'colab-cli'
os.environ['CLOUDSDK_CONFIG']=str(tool/'gcloud-auth')
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=str(tool/'gcloud-auth'/'application_default_credentials.json')
os.environ['COLAB_CLI_REQUEST_TIMEOUT']='45'
from colab_cli.common import state
from colab_cli.history import HistoryLogger
state._history=HistoryLogger(str(root/'cli_history'))
from colab_cli.cli import app
app(args=['--auth','adc','--config',str(tool/'sessions.json')]+sys.argv[1:])
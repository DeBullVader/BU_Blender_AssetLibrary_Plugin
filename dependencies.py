import pip
import sys
import bpy
import subprocess
import os
from os import environ, makedirs, path, pathsep

def ensure_deps():
  """Make sure that dependencies which need installation are available. Install dependencies if needed."""
  tried = 0
  while tried < 2:
    tried = tried + 1
    try:
      print('TRYING OUT PACKAGES')
      import moralis
      import oauth2client
      from moralis import evm_api
      return
    except:
      install_dependencies()
      print('INSTALLING DEPENDENCIES')

def install_dependencies():
    py_dir = os.path.join(sys.prefix, 'bin', 'python.exe')
    print('THE CURRENT PYTHON DIR IS : ' + py_dir)
    v = bpy.app.version
    packages = [
      'moralis',
      'google-api-python-client',
      'google-auth-httplib2', 
      'google-auth-oauthlib',
      'oauth2client', 
    ]
    print('INSTALLING DEPENDENCIES')
    subprocess.call([py_dir, "-m", "ensurepip"])
    subprocess.call([py_dir, "-m", "pip", "install", "--upgrade", "pip"])
    for package in packages:
        subprocess.call([py_dir, "-m", "pip", "install", package])

    # env  = environ.copy()
    # command = [sys.executable, '-m', 'ensurepip', '--user']
    # result = subprocess.run(command, env=env, capture_output=True, text=True)
    # print(f"PIP INSTALLATION:\ncommand {command} exited: {result.returncode},\nstdout: {result.stdout},\nstderr: {result.stderr}")
    # command = [sys.executable, '-m ', 'pip,''install','google-api-python-client','--user']

    # #command = [sys.executable, '-m ', 'pip,''install','moralis','google-api-python-client','google-auth-httplib2', 'google-auth-oauthlib','oauth2client','--user']
    # result = subprocess.run(command, env=env, capture_output=True, text=True)
    # print(f"UNCONSTRAINED INSTALLATION:\ncommand {command} exited: {result.returncode},\nstdout: {result.stdout},\nstderr: {result.stderr}")
import runpy, os
os.chdir(os.path.dirname(__file__))
runpy.run_path('agent/agent.py', run_name='__main__')

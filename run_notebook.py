"""Execute a notebook in place (for runai jobs, where jupyter CLI isn't on PATH).
Usage: python run_notebook.py <notebook.ipynb>"""
import os, sys
import nbformat
from nbclient import NotebookClient

path = os.path.abspath(sys.argv[1])
nb = nbformat.read(path, as_version=4)
client = NotebookClient(nb, timeout=1800, kernel_name="python3",
                        resources={"metadata": {"path": os.path.dirname(path)}})
try:
    client.execute()
finally:
    nbformat.write(nb, path)  # save outputs even if a cell fails
    print("wrote", path)

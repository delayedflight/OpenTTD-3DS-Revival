"""Current vehicle layout regression; includes both native and wide layouts."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('compact-vehicles.py')),run_name='__main__')

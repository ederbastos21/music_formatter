#logger.py
import sys

class ColoredLogger:
    def __init__(self, module_name):
        self.module_name = module_name
        self.colors = {
            'MODULE': '\033[94m',  # Blue
            'INFO': '\033[36m',    # Cyan
            'SUCCESS': '\033[92m', # Green
            'ERROR': '\033[91m',   # Red
            'ENDC': '\033[0m',
        }
    
    def module_start(self):
        print(f"\n{self.colors['MODULE']}=== {self.module_name} ==={self.colors['ENDC']}")
    
    def info(self, message):
        print(f"{self.colors['INFO']}[{self.module_name}] INFO: {message}{self.colors['ENDC']}", file=sys.stderr)
    
    def success(self, message):
        print(f"{self.colors['SUCCESS']}[{self.module_name}] SUCCESS: {message}{self.colors['ENDC']}", file=sys.stderr)
    
    def error(self, message):
        print(f"{self.colors['ERROR']}[{self.module_name}] ERROR: {message}{self.colors['ENDC']}", file=sys.stderr)

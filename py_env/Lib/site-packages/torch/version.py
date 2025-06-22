from typing import Optional

__all__ = ['__version__', 'debug', 'cuda', 'git_version', 'hip']
__version__ = '2.4.1+cu121'
debug = False
cuda: Optional[str] = '12.1'
git_version = '38b96d3399a695e704ed39b60dac733c3fbf20e2'
hip: Optional[str] = None

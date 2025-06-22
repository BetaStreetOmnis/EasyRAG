__version__ = '0.19.1+cu121'
git_version = '61943691d3390bd3148a7003b4a501f0e2b7ac6e'
from torchvision.extension import _check_cuda_version
if _check_cuda_version() > 0:
    cuda = _check_cuda_version()

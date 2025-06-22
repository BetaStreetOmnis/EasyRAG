# Copyright (c) 2018-2019, Intel Corporation
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import pytest
import mkl


def test_get_version():
    v = mkl.get_version()
    assert isinstance(v, dict)
    assert 'MajorVersion' in v
    assert 'MinorVersion' in v
    assert 'UpdateVersion' in v


def test_get_version_string():
    v = mkl.get_version_string()
    assert isinstance(v, str)
    assert 'Math Kernel Library' in v


def test_set_num_threads():
    saved = mkl.get_max_threads()
    half_nt = int( (1 + saved) / 2 ) 
    mkl.set_num_threads(half_nt)
    assert mkl.get_max_threads() == half_nt
    mkl.set_num_threads(saved)

def test_domain_set_num_threads_blas():
    saved_blas_nt = mkl.domain_get_max_threads(domain='blas')
    saved_fft_nt = mkl.domain_get_max_threads(domain='fft')
    saved_vml_nt = mkl.domain_get_max_threads(domain='vml')
    # set
    blas_nt = int( (3 + saved_blas_nt)/4 )
    fft_nt = int( (3 + 2*saved_fft_nt)/4 )
    vml_nt = int( (3 + 3*saved_vml_nt)/4 )
    status = mkl.domain_set_num_threads(blas_nt, domain='blas')
    assert status == 'success'
    status = mkl.domain_set_num_threads(fft_nt, domain='fft')
    assert status == 'success'
    status = mkl.domain_set_num_threads(vml_nt, domain='vml')
    assert status == 'success'
    # check
    assert mkl.domain_get_max_threads(domain='blas') == blas_nt
    assert mkl.domain_get_max_threads(domain='fft') == fft_nt
    assert mkl.domain_get_max_threads(domain='vml') == vml_nt
    # restore
    status = mkl.domain_set_num_threads(saved_blas_nt, domain='blas')
    assert status == 'success'
    status = mkl.domain_set_num_threads(saved_fft_nt, domain='fft')
    assert status == 'success'
    status = mkl.domain_set_num_threads(saved_vml_nt, domain='vml')
    assert status == 'success'

def test_domain_set_num_threads_fft():
    status = mkl.domain_set_num_threads(4, domain='fft')
    assert status == 'success'

def test_domain_set_num_threads_vml():
    status = mkl.domain_set_num_threads(4, domain='vml')
    assert status == 'success'

def test_domain_set_num_threads_pardiso():
    status = mkl.domain_set_num_threads(4, domain='pardiso')
    assert status == 'success'

def test_domain_set_num_threads_all():
    status = mkl.domain_set_num_threads(4, domain='all')
    assert status == 'success'

def test_set_num_threads_local():
    mkl.set_num_threads(1)
    status = mkl.set_num_threads_local(2)
    assert status == 'global_num_threads'
    status = mkl.set_num_threads_local(4)
    assert status == 2
    status = mkl.set_num_threads_local(0)
    assert status == 4
    status = mkl.set_num_threads_local(8)
    assert status == 'global_num_threads'

def test_set_dynamic():
    mkl.set_dynamic(True)

def test_get_max_threads():
    mkl.get_max_threads()

def test_domain_get_max_threads_blas():
    mkl.domain_get_max_threads(domain='blas')

def test_domain_get_max_threads_fft():
    mkl.domain_get_max_threads(domain='fft')

def test_domain_get_max_threads_vml():
    mkl.domain_get_max_threads(domain='vml')

def test_domain_get_max_threads_pardiso():
    mkl.domain_get_max_threads(domain='pardiso')

def test_domain_get_max_threads_all():
    mkl.domain_get_max_threads(domain='all')

def test_get_dynamic():
    mkl.get_dynamic()


# https://software.intel.com/en-us/mkl-developer-reference-c-timing
def test_second():
    s1 = mkl.second()
    s2 = mkl.second()
    delta = s2 - s1
    assert delta >= 0

def test_dsecnd():
    d1 = mkl.dsecnd()
    d2 = mkl.dsecnd()
    delta = d2 - d1
    assert delta >= 0

def test_get_cpu_clocks():
    c1 = mkl.get_cpu_clocks()
    c2 = mkl.get_cpu_clocks()
    delta = c2 - c1
    assert delta >= 0

def test_get_cpu_frequency():
    assert mkl.get_cpu_frequency() >= 0

def test_get_max_cpu_frequency():
    assert mkl.get_max_cpu_frequency() >= 0

def test_get_clocks_frequency():
    assert mkl.get_clocks_frequency() >= 0


def test_free_buffers():
    mkl.free_buffers()

def test_thread_free_buffers():
    mkl.thread_free_buffers()

def test_disable_fast_mm():
    mkl.disable_fast_mm()

def test_mem_stat():
    mkl.mem_stat()

def test_peak_mem_usage_enable():
    mkl.peak_mem_usage('enable')

def test_peak_mem_usage_disable():
    mkl.peak_mem_usage('disable')

def test_peak_mem_usage_peak_mem():
    mkl.peak_mem_usage('peak_mem')

def test_peak_mem_usage_peak_mem_reset():
    mkl.peak_mem_usage('peak_mem_reset')

def test_set_memory_limit():
    mkl.set_memory_limit(128)


branches = [
    'off',
    'branch_off',
    'auto',
    'compatible',
    'sse2',
    'ssse3',
    'sse4_1',
    'sse4_2',
    'avx',
    'avx2',
    'avx512_mic',
    'avx512',
    'avx512_mic_e1',
    'avx512_e1',
]
strict = [
    'avx2,strict',
    'avx512_mic,strict',
    'avx512,strict',
    'avx512_e1,strict',
]
@pytest.mark.parametrize('branch', branches)
def test_cbwr_branch(branch):
    check_cbwr(branch, 'branch')

@pytest.mark.parametrize('branch', branches + strict)
def test_cbwr_all(branch):
    check_cbwr(branch, 'all')

def check_cbwr(branch, cnr_const):
    status = mkl.cbwr_set(branch=branch)
    if status == 'success':
        expected_value = 'branch_off' if branch == 'off' else branch
        actual_value = mkl.cbwr_get(cnr_const=cnr_const)
        assert actual_value == expected_value, \
            f"Round-trip failure for CNR branch '{branch}', CNR const '{cnr_const}"
    elif status != 'err_unsupported_branch':
        pytest.fail(status)

def test_cbwr_get_auto_branch():
    mkl.cbwr_get_auto_branch()


def test_enable_instructions_avx512_mic_e1():
    mkl.enable_instructions('avx512_mic_e1')

def test_enable_instructions_avx512():
    mkl.enable_instructions('avx512')

def test_enable_instructions_avx512_mic():
    mkl.enable_instructions('avx512_mic')

def test_enable_instructions_avx2():
    mkl.enable_instructions('avx2')

def test_enable_instructions_avx():
    mkl.enable_instructions('avx')

def test_enable_instructions_sse4_2():
    mkl.enable_instructions('sse4_2')

def test_set_env_mode():
    mkl.set_env_mode()

def test_get_env_mode():
    mkl.get_env_mode()

def test_verbose_false():
    mkl.verbose(False)

def test_verbose_true():
    mkl.verbose(True)

@pytest.mark.skip(reason="Skipping MPI-related test")
def test_set_mpi_custom():
    mkl.set_mpi('custom', 'custom_library_name')

@pytest.mark.skip(reason="Skipping MPI-related test")
def test_set_mpi_msmpi():
    mkl.set_mpi('msmpi')

@pytest.mark.skip(reason="Skipping MPI-related test")
def test_set_mpi_intelmpi():
    mkl.set_mpi('intelmpi')

@pytest.mark.skip(reason="Skipping MPI-related test")
def test_set_mpi_mpich2():
    mkl.set_mpi('mpich2')


def test_vml_set_get_mode_roundtrip():
    saved = mkl.vml_get_mode()
    mkl.vml_set_mode(*saved) # should not raise errors

def test_vml_set_mode_ha_on_ignore():
    mkl.vml_set_mode('ha', 'on', 'ignore')

def test_vml_set_mode_ha_on_errno():
    mkl.vml_set_mode('ha', 'on', 'errno')

def test_vml_set_mode_la_on_stderr():
    mkl.vml_set_mode('la', 'on', 'stderr')

def test_vml_set_mode_la_off_except():
    mkl.vml_set_mode('la', 'off', 'except')

def test_vml_set_mode_op_off_callback():
    mkl.vml_set_mode('ep', 'off', 'callback')

def test_vml_set_mode_ep_off_default():
    mkl.vml_set_mode('ep', 'off', 'default')

def test_vml_get_mode():
    mkl.vml_get_mode()

def test_vml_set_err_status_ok():
    mkl.vml_set_err_status('ok')

def test_vml_set_err_status_accuracywarning():
    mkl.vml_set_err_status('accuracywarning')

def test_vml_set_err_status_badsize():
    mkl.vml_set_err_status('badsize')

def test_vml_set_err_status_badmem():
    mkl.vml_set_err_status('badmem')

def test_vml_set_err_status_errdom():
    mkl.vml_set_err_status('errdom')

def test_vml_set_err_status_sing():
    mkl.vml_set_err_status('sing')

def test_vml_set_err_status_overflow():
    mkl.vml_set_err_status('overflow')

def test_vml_set_err_status_underflow():
    mkl.vml_set_err_status('underflow')

def test_vml_get_err_status():
    mkl.vml_get_err_status()

def test_vml_clear_err_status():
    mkl.vml_clear_err_status()

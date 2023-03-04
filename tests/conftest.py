import sys
import pytest
import shutil
from pathlib import Path
from cookiecutter import main

CCDS_ROOT = Path(__file__).parents[1].resolve()

PROJECT_NAME = 'DrivenData'
AUTHOR_NAME = 'DrivenData'

args = {
        'project_name': PROJECT_NAME,
        'author_name': AUTHOR_NAME,
        'open_source_license': 'BSD-3-Clause',
        'package_manager': 'pip',
        }
use_poetry = {
    'project_name': PROJECT_NAME,
    'author_name': AUTHOR_NAME,
    'package_manager': 'poetry'
}


def system_check(basename):
    platform = sys.platform
    if 'linux' in platform:
        basename = basename.lower()
    return basename


@pytest.fixture(scope='class', params=[{'package_manager': 'pip'}, args, use_poetry])
def default_baked_project(tmpdir_factory, request):
    temp = tmpdir_factory.mktemp('data-project')
    out_dir = Path(temp).resolve()

    pytest.param = request.param
    main.cookiecutter(
        str(CCDS_ROOT),
        no_input=True,
        extra_context=pytest.param,
        output_dir=out_dir
    )

    pn = pytest.param.get('project_name') or 'project_name'
    
    # project name gets converted to lower case on Linux but not Mac
    pn = system_check(pn)

    proj = out_dir / pn
    request.cls.path = proj
    yield 

    # cleanup after
    shutil.rmtree(out_dir)
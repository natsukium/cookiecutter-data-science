import os
import pytest
import subprocess
from subprocess import check_output
from conftest import system_check
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def no_curlies(filepath):
    """ Utility to make sure no curly braces appear in a file.
        That is, was Jinja able to render everything?
    """
    with open(filepath, 'r') as f:
        data = f.read()

    template_strings = [
        '{{',
        '}}',
        '{%',
        '%}'
    ]

    template_strings_in_file = [s in data for s in template_strings]
    return not any(template_strings_in_file)


@pytest.mark.usefixtures("default_baked_project")
class TestCookieSetup(object):
    @property
    def pyproject_toml_path(self) -> Path:
        return self.path / 'pyproject.toml'

    @property
    def reqs_path(self) -> Path:
        return self.path / 'requirements.txt'

    @property
    def setup_(self) -> Path:
        return self.path / 'setup.py'

    @property
    def test_environment_path(self) -> Path:
        return self.path / 'test_environment.py'

    @property
    def package_manager(self) -> str:
        return pytest.param.get('package_manager')

    def test_project_name(self):
        project = self.path
        if pytest.param.get('project_name'):
            name = system_check('DrivenData')
            assert project.name == name
        else:
            assert project.name == 'project_name'

    def test_author(self):
        default = 'Your name (or your organization/company/team)'
        if self.package_manager == 'pip':
            args = ['python', str(self.setup_), '--author']
            p = check_output(args).decode('ascii').strip()
            if pytest.param.get('author_name'):
                assert p == 'DrivenData'
            else:
                assert p == default
        else:
            with self.pyproject_toml_path.open('rb') as f:
                p = tomllib.load(f)['tool']['poetry']['authors'][0]

            if pytest.param.get('author_name'):
                assert p == 'DrivenData <email@example.com>'
            else:
                assert p == f'{default} <email@example.com>'


    def test_readme(self):
        readme_path = self.path / 'README.md'
        assert readme_path.exists()
        assert no_curlies(readme_path)
        if pytest.param.get('project_name'):
            with open(readme_path) as fin:
                assert 'DrivenData' == next(fin).strip()

    def test_pyproject_toml(self):
        assert self.pyproject_toml_path.exists()

        with self.pyproject_toml_path.open('rb') as f:
            try:
                tomllib.load(f)
            except tomllib.TOMLDecodeError:
                assert False

        if self.package_manager == 'poetry':
            assert subprocess.run(["poetry", "check"], cwd=self.path).returncode == 0

    def test_setup(self):
        if self.package_manager != 'pip':
            pytest.skip('there is no setup.py')
        args = ['python', str(self.setup_), '--version']
        p = check_output(args).decode('ascii').strip()
        assert p == '0.1.0'

    def test_license(self):
        license_path = self.path / 'LICENSE'
        assert license_path.exists()
        assert no_curlies(license_path)

    def test_license_type(self):
        license = pytest.param.get('open_source_license')
        if self.package_manager == 'pip':
            args = ['python', str(self.setup_), '--license']
            p = check_output(args).decode('ascii').strip()
            if license:
                assert p == 'BSD-3'
            else:
                assert p == 'MIT'
        else:
            with self.pyproject_toml_path.open('rb') as f:
                content = tomllib.load(f)
            actual: str = content.get('tool').get('poetry').get('license')
            if license:
                assert actual == license

    def test_requirements(self):
        if self.package_manager != 'pip':
            pytest.skip('there is no requirements.txt')
        assert self.reqs_path.exists()
        assert no_curlies(self.reqs_path)

    def test_makefile(self):
        makefile_path = self.path / 'Makefile'
        assert makefile_path.exists()
        assert no_curlies(makefile_path)

    def test_interpreter(self):
        makefile_path = self.path / 'Makefile'
        with open(makefile_path) as fin:
            if self.package_manager == 'pip':
                assert 'PYTHON_INTERPRETER = python3\n' in fin.readlines()
            else:
                assert ('PYTHON_INTERPRETER = $(PYTHON_PACKAGE_MANAGER) run python\n'
                        in fin.readlines())

    def test_containerfile_exists(self):
        containerfile_path = self.path / 'Containerfile'
        assert containerfile_path.exists()
        assert no_curlies(containerfile_path)

    @pytest.mark.slow
    def test_build_image(self):
        if self.package_manager != 'pip':
            subprocess.run(['make', 'lockfile'], cwd=self.path)
        exit_code_build = subprocess.run(['make', 'image'], cwd=self.path).returncode
        assert exit_code_build == 0
        exit_code_import_check = subprocess.run(['make', 'container_import_check'], cwd=self.path).returncode
        assert exit_code_import_check == 0

    def test_folders(self):
        expected_dirs = [
            'data',
            'data/external',
            'data/interim',
            'data/processed',
            'data/raw',
            'docs',
            'models',
            'notebooks',
            'references',
            'reports',
            'reports/figures',
            'src',
            'src/data',
            'src/features',
            'src/models',
            'src/visualization',
        ]

        ignored_dirs = [
            str(self.path)
        ]

        abs_expected_dirs = [str(self.path / d) for d in expected_dirs]
        abs_dirs, _, _ = list(zip(*os.walk(self.path)))
        assert len(set(abs_expected_dirs + ignored_dirs) - set(abs_dirs)) == 0

    def test_post_hook(self):
        if self.package_manager == 'pip':
            pytest.skip('post hook is not executed')
        assert not self.reqs_path.exists()
        assert not self.setup_.exists()
        assert not self.test_environment_path.exists()

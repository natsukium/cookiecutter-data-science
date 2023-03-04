import os
import pytest
import subprocess
from subprocess import check_output
from conftest import system_check

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
    def pyproject_toml_path(self):
        return self.path / 'pyproject.toml'

    def test_project_name(self):
        project = self.path
        if pytest.param.get('project_name'):
            name = system_check('DrivenData')
            assert project.name == name
        else:
            assert project.name == 'project_name'

    def test_author(self):
        default = 'Your name (or your organization/company/team)'
        if pytest.param.get('package_manager') == 'pip':
            setup_ = self.path / 'setup.py'
            args = ['python', str(setup_), '--author']
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
        if pytest.param.get('package_manager') == 'pip':
            return
        assert self.pyproject_toml_path.exists()
        assert subprocess.run(["poetry", "check"], cwd=self.path).returncode == 0

    def test_setup(self):
        if pytest.param.get('package_manager') != 'pip':
            return
        setup_ = self.path / 'setup.py'
        args = ['python', str(setup_), '--version']
        p = check_output(args).decode('ascii').strip()
        assert p == '0.1.0'

    def test_license(self):
        license_path = self.path / 'LICENSE'
        assert license_path.exists()
        assert no_curlies(license_path)

    def test_license_type(self):
        if pytest.param.get('package_manager') == 'pip':
            setup_ = self.path / 'setup.py'
            args = ['python', str(setup_), '--license']
            p = check_output(args).decode('ascii').strip()
            if pytest.param.get('open_source_license'):
                assert p == 'BSD-3'
            else:
                assert p == 'MIT'
        else:
            with self.pyproject_toml_path.open('rb') as f:
                content = tomllib.load(f)
            _license: str = content.get('tool').get('poetry').get('license')
            if pytest.param.get('open_source_license'):
                assert _license == pytest.param.get('open_source_licesnse')

    def test_requirements(self):
        if pytest.param.get('package_manager') != 'pip':
            return
        reqs_path = self.path / 'requirements.txt'
        assert reqs_path.exists()
        assert no_curlies(reqs_path)

    def test_makefile(self):
        makefile_path = self.path / 'Makefile'
        assert makefile_path.exists()
        assert no_curlies(makefile_path)

    def test_interpreter(self):
        makefile_path = self.path / "Makefile"
        package_manager = pytest.param.get('package_manager')
        with open(makefile_path) as fin:
            if package_manager == 'pip':
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
        exit_code = subprocess.run(["make", "image"], cwd=self.path).returncode
        assert exit_code == 0

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

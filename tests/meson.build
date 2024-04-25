# SPDX-License-Identifier: GPL-3.0-or-later
pytest = find_program('pytest', required: false)

if pytest.found()
  build_tests_dir = join_paths(meson.project_build_root(), 'run_tests')
  install_subdir('.',
    install_dir: build_tests_dir,
  )
  test('pytest', pytest,
    args: [build_tests_dir],
     env: [
      'pkgdatadir=' + pkgdatadir,
      'application_id=' + application_id,
    ],
  )
endif

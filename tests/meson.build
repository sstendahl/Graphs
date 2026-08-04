# SPDX-License-Identifier: GPL-3.0-or-later
check_pytest = run_command([python, '-c', 'import pytest'],
  check: false,
)
if check_pytest.returncode() == 0
  test('Run Python test suite', python,
       args: ['-m', 'pytest', meson.current_source_dir()],
    depends: [graphs_lib, graphs_typelib],
        env: devenv,
  )
endif

test_sources = files(
  'main.vala',
  'test_math_parser.vala',
)
test_executable = executable('unittest', test_sources, dependencies: [
    gobject_dep,
    gtk_dep,
    adwaita_dep,
    gee_dep,
  ],
            link_with: graphs_lib,
  include_directories: source_include,
               c_args: ['-w'], # suppress vala generated c warnings
     build_by_default: false,
)
test('Run vala test suite', test_executable,
   depends: [test_executable, graphs_lib],
  protocol: 'tap',
       env: [
         'G_TEST_SRCDIR=@0@'.format(meson.current_source_dir()),
         'G_TEST_BUILDDIR=@0@'.format(meson.current_build_dir()),
       ],
)
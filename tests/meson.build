# SPDX-License-Identifier: GPL-3.0-or-later
pytest = find_program('pytest', required: false)

if pytest.found()
  test('Run Python test suite', pytest,
       args: [meson.current_source_dir()],
    depends: [graphs_lib, graphs_typelib],
        env: devenv,
  )
endif

test_sources = files(
  'main.vala',
  'test_math_parser.vala',
)
test_executable = executable('unittest', test_sources,
         dependencies: dependencies,
            link_with: graphs_lib,
  include_directories: source_include,
               c_args: ['-w'], # suppress vala generated c warnings
)
test('Run vala test suite', test_executable,
  depends: [test_executable, graphs_lib],
)
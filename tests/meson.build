# SPDX-License-Identifier: GPL-3.0-or-later
pytest = find_program('pytest', required: false)

if pytest.found()
  test('pytest', pytest,
       args: [meson.current_source_dir()],
    depends: [graphs_lib, graphs_typelib],
        env: devenv,
  )
endif

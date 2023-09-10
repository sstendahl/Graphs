pytest = find_program('pytest', required: false)
if pytest.found()
  test(
      'pytest',
      find_program('pytest'),
      args: [meson.project_source_root() + '/tests'],
      env: [
          'pkgdatadir=' + pkgdatadir,
          'application_id=' + application_id,
      ],
  )
endif

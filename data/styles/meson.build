# SPDX-License-Identifier: GPL-3.0-or-later
adwaita = 'adwaita.mplstyle'
adwaita_dark = 'adwaita-dark.mplstyle'
yaru = 'yaru.mplstyle'
yaru_dark = 'yaru-dark.mplstyle'

style_infos = {
  'Adwaita': adwaita,
  'Adwaita Dark': adwaita_dark,
  'BMH': 'bmh.mplstyle',
  'Classic': 'classic.mplstyle',
  'Dark Background': 'dark-background.mplstyle',
  'FiveThirtyEight': 'fivethirtyeight.mplstyle',
  'ggplot': 'ggplot.mplstyle',
  'Grayscale': 'grayscale.mplstyle',
  'Matplotlib': 'matplotlib.mplstyle',
  'Seaborn': 'seaborn.mplstyle',
  'Seaborn White': 'seaborn-white.mplstyle',
  'Seaborn Whitegrid': 'seaborn-whitegrid.mplstyle',
  'Solarized Light': 'solarized-light.mplstyle',
  'Tableau Colorblind10': 'tableau-colorblind10.mplstyle',
  'Thesis': 'thesis.mplstyle',
  'Yaru': yaru,
  'Yaru Dark': yaru_dark,
}

style_io = files('../../graphs/style_io.py')
preview_generator = files('generate_preview.py')
styles = []
previews = []
style_info = ''
format = '{ "@0@", "/se/sjoerd/Graphs/styles/@1@", "/se/sjoerd/Graphs/@2@" },'

foreach name, path : style_infos
  preview_file = path.replace('.mplstyle', '.png')
  info_file = path.replace('.mplstyle', '.txt')
  style_file = files(path)
  styles += style_file
  previews += custom_target(preview_file,
           input: style_file,
          output: preview_file,
    depend_files: [style_io, preview_generator],
         command: [
           python,
           preview_generator,
           style_io,
           'preview',
           '@INPUT@',
           '@OUTPUT@',
         ],
  )
  style_info += format.format(name, path, preview_file)
endforeach

conf.set('STYLES', style_info)

system_style_adwaita = custom_target('Adwaita system style preview',
         input: [adwaita, adwaita_dark],
        output: 'system-style-adwaita.png',
  depend_files: [style_io, preview_generator],
       command: [
         python,
         preview_generator,
         style_io,
         'system',
         files(adwaita),
         files(adwaita_dark),
         '@OUTPUT@',
       ],
  )
system_style_yaru = custom_target('Yaru system style preview',
         input: [yaru, yaru_dark],
        output: 'system-style-yaru.png',
  depend_files: [style_io, preview_generator],
       command: [
         python,
         preview_generator,
         style_io,
         'system',
         files(yaru),
         files(yaru_dark),
         '@OUTPUT@',
       ],
  )
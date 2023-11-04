// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {

    public const string[] limit_names = {
        "min-bottom", "max-bottom", "min-top", "max-top",
        "min-left", "max-left", "min-right", "max-right",
    };

    public class Style : Object {
        public string name { get; construct set; default = ""; }
        public File? preview { get; set; }
        public File? file { get; construct set; }
        public bool mutable { get; construct set; }

        public Style (string name, File? file, File? preview, bool mutable) {
         Object (
           name: name, file: file, preview: preview, mutable: mutable
         );
        }
    }
}

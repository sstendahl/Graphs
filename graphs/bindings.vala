[CCode (cprefix = "", lower_case_cprefix = "", cheader_filename = "utilities.h")]
namespace Graphs.CUtilities {

    [CCode (cname = "array_minmax")]
    public extern bool array_minmax (
        double[] data,
        bool ignore_zero,
        out double out_min,
        out double out_max
    );
}

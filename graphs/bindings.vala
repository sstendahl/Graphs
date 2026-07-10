[CCode (cprefix = "", lower_case_cprefix = "", cheader_filename = "utilities.h")]
namespace Graphs.CUtilities {

    [CCode (cname = "array_minmax")]
    private extern bool array_minmax (
        [CCode (array_length = true)]
        double[] data,
        bool ignore_zero,
        out double out_min,
        out double out_max
    );

    [CCode (cname = "finite_double")]
    private extern bool finite_double (
        [CCode (array_length = true)]
        double[] data
    );

    [CCode (cname = "arange")]
    private extern bool arange (
        [CCode (array_length = true)]
        double[] output
    );

    [CCode (cname = "create_equidistant_data")]
    private extern bool create_equidistant_data (
        double start,
        double stop,
        Scale scale,
        [CCode (array_length = true)]
        double[] out
    );

    [CCode (cname = "filter_nonfinite")]
    private extern int filter_nonfinite (
        [CCode (array_length = false)]
        double[] xdata,
        [CCode (array_length = false)]
        double[] ydata,
        size_t n
    );
}

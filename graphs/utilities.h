#pragma once

#include <stdbool.h>
#include <stddef.h>

#include "graphs.h"

gboolean array_minmax (const gdouble *data, gsize len, gboolean ignore_zero,
                       gdouble *out_min, gdouble *out_max);

gboolean finite_double (const gdouble *data, gsize len);

gboolean arange (gdouble *out, gsize steps);

gboolean create_equidistant_data (gdouble start, gdouble stop,
                                  GraphsScale scale, gdouble *out, gsize steps);

gsize filter_nonfinite (gdouble *xdata, gdouble *ydata, gsize n);

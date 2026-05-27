#pragma once

#include <stdbool.h>
#include <stddef.h>

typedef enum
{
  SCALE_LINEAR = 0,
  SCALE_RADIANS,
  SCALE_LOG,
  SCALE_LOG2,
  SCALE_SQUAREROOT,
  SCALE_INVERSE,
} Scale;

bool array_minmax (const double *data, size_t len, bool ignore_zero,
                   double *out_min, double *out_max);

bool finite_double (const double *data, size_t len);

bool arange (double *out, size_t steps);

bool create_equidistant_data (double start, double stop, Scale scale,
                              double *out, size_t steps);

size_t filter_nonfinite (double *xdata, double *ydata, size_t n);

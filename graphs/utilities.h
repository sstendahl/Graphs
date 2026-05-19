#pragma once

#include <stdbool.h>
#include <stddef.h>

bool array_minmax (const double *data, size_t len, bool ignore_zero,
                          double *out_min, double *out_max);

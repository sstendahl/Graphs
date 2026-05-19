#include "utilities.h"

#include <math.h>
#include <omp.h>

bool
array_minmax (const double *restrict data, size_t len, bool ignore_zero,
              double *restrict out_min, double *restrict out_max)
{
  if (!data || !out_min || !out_max || len == 0)
    return false;

  double minv = INFINITY;
  double maxv = -INFINITY;
  bool found = false;

/*
 * OpenMP SIMD reductions:
 * - reduction(min:maxv)
 * - reduction(max:minv)
 *
 * We cannot safely reduce a bool, so track validity separately.
 */
#pragma omp simd reduction(min : minv) reduction(max : maxv)
  for (size_t i = 0; i < len; i++)
    {
      double v = data[i];

      if (!isfinite (v))
        continue;

      if (ignore_zero && v == 0.0)
        continue;

      if (v < minv)
        minv = v;

      if (v > maxv)
        maxv = v;
    }

/*
 * Second pass to determine whether at least one
 * valid value existed.
 *
 * This keeps the SIMD loop vectorizable.
 */
#pragma omp simd reduction(|| : found)
  for (size_t i = 0; i < len; i++)
    {
      double v = data[i];

      if (!isfinite (v))
        continue;

      if (ignore_zero && v == 0.0)
        continue;

      found = true;
    }

  if (!found)
    return false;

  *out_min = minv;
  *out_max = maxv;

  return true;
}

#include "utilities.h"

#include <math.h>
#include <omp.h>
#include <stdlib.h>

#define MIN_LOG_VALUE 1e-300
#define MAX_LOG_VALUE 1e300

/*
 * Small helper to find the min and max value of a double array.
 */
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

      if (!isfinite (v) || (ignore_zero && v == 0.0))
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

      if (!isfinite (v) || (ignore_zero && v == 0.0))
        continue;

      found = true;
    }

  if (!found)
    return false;

  *out_min = minv;
  *out_max = maxv;

  return true;
}

bool
finite_double (const double *restrict data, size_t len)
{
  bool found = false;

#pragma omp simd reduction(|| : found)
  for (size_t i = 0; i < len; i++)
    {
      if (!isfinite (data[i]))
        continue;

      found = true;
    }

  return found;
}

bool
arange (double *restrict out, size_t steps)
{
  if (steps == 0)
    return false;

#pragma omp parallel for simd
  for (size_t i = 0; i < steps; i++)
    {
      out[i] = i;
    }

  return true;
}

static inline double
clamp_log_lower (double x)
{
  return x < MIN_LOG_VALUE ? MIN_LOG_VALUE : x;
}

bool
create_equidistant_data (double start, double stop, Scale scale, double *out,
                         size_t steps)
{
  if (steps < 2)
    return false;

  const double inv_steps = 1.0 / (double)(steps - 1);

  switch (scale)
    {

    case SCALE_LINEAR:
    case SCALE_RADIANS:
      {

        const double delta = stop - start;

#pragma omp parallel for simd
        for (size_t i = 0; i < steps; i++)
          {
            const double t = (double)i * inv_steps;
            out[i] = start + t * delta;
          }

        break;
      }

    case SCALE_LOG:
      {

        start = clamp_log_lower (start);

        if (!isfinite (stop))
          stop = MAX_LOG_VALUE;

        const double log_start = log10 (start);
        const double log_stop = log10 (stop);
        const double delta = log_stop - log_start;

#pragma omp parallel for simd
        for (size_t i = 0; i < steps; i++)
          {

            const double t = (double)i * inv_steps;

            out[i] = pow (10.0, log_start + t * delta);
          }

        break;
      }

    case SCALE_LOG2:
      {

        start = clamp_log_lower (start);

        if (!isfinite (stop))
          stop = MAX_LOG_VALUE;

        const double log_start = log2 (start);
        const double log_stop = log2 (stop);
        const double delta = log_stop - log_start;

#pragma omp parallel for simd
        for (size_t i = 0; i < steps; i++)
          {

            const double t = (double)i * inv_steps;

            out[i] = exp2 (log_start + t * delta);
          }

        break;
      }

    case SCALE_SQUAREROOT:
      {

        start = clamp_log_lower (start);

        const double sqrt_start = sqrt (start);
        const double sqrt_stop = sqrt (stop);
        const double delta = sqrt_stop - sqrt_start;

#pragma omp parallel for simd
        for (size_t i = 0; i < steps; i++)
          {

            const double t = (double)i * inv_steps;

            const double v = sqrt_start + t * delta;

            out[i] = v * v;
          }

        break;
      }

    case SCALE_INVERSE:
      {

        const double inv_start = 1.0 / start;
        const double inv_stop = 1.0 / stop;
        const double delta = inv_stop - inv_start;

#pragma omp parallel for simd
        for (size_t i = 0; i < steps; i++)
          {

            const double t = (double)i * inv_steps;

            out[i] = 1.0 / (inv_start + t * delta);
          }

        break;
      }

    default:
      return false;
    }

  return out;
}

size_t
filter_nonfinite (double *xdata, double *ydata, size_t n)
{
  if (!xdata || !ydata || n == 0)
    return 0;

  char *mask = (char *)malloc (n * sizeof (char));
  size_t *prefix = (size_t *)malloc (n * sizeof (size_t));

  if (!mask || !prefix)
    {
      free (mask);
      free (prefix);
      return 0;
    }

  /* Build a mask for finite values */
#pragma omp parallel for
  for (size_t i = 0; i < n; ++i)
    {
      mask[i] = isfinite (ydata[i]) ? 1 : 0;
    }

  /* Build a prefix sum - carries loop depenency */
  int count = 0;
  for (size_t i = 0; i < n; ++i)
    {
      prefix[i] = count;
      count += mask[i];
    }

  /* Compact data in place */
#pragma omp parallel for
  for (size_t i = 0; i < n; ++i)
    {
      if (mask[i])
        {
          size_t dst = prefix[i];
          xdata[dst] = xdata[i];
          ydata[dst] = ydata[i];
        }
    }

  free (mask);
  free (prefix);

  return count;
}

#include "utilities.h"

#include <math.h>
#include <omp.h>
#include <stdlib.h>

#define MIN_LOG_VALUE 1e-300
#define MAX_LOG_VALUE 1e300

/*
 * Small helper to find the min and max value of a double array.
 */
gboolean
array_minmax (const gdouble *restrict data, gsize len, gboolean ignore_zero,
              gdouble *restrict out_min, gdouble *restrict out_max)
{
  if (!data || !out_min || !out_max || len == 0)
    return FALSE;

  gdouble minv = INFINITY;
  gdouble maxv = -INFINITY;
  gboolean found = FALSE;

/*
 * OpenMP SIMD reductions:
 * - reduction(min:maxv)
 * - reduction(max:minv)
 *
 * We cannot safely reduce a bool, so track validity separately.
 */
#pragma omp simd reduction(min : minv) reduction(max : maxv)
  for (gsize i = 0; i < len; i++)
    {
      gdouble v = data[i];

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
  for (gsize i = 0; i < len; i++)
    {
      gdouble v = data[i];

      if (!isfinite (v) || (ignore_zero && v == 0.0))
        continue;

      found = TRUE;
    }

  if (!found)
    return FALSE;

  *out_min = minv;
  *out_max = maxv;

  return TRUE;
}

gboolean
finite_double (const gdouble *restrict data, gsize len)
{
  gboolean found = FALSE;

#pragma omp simd reduction(|| : found)
  for (gsize i = 0; i < len; i++)
    {
      if (!isfinite (data[i]))
        continue;

      found = TRUE;
    }

  return found;
}

gboolean
arange (gdouble *restrict out, gsize steps)
{
  if (steps == 0)
    return FALSE;

#pragma omp parallel for simd
  for (gsize i = 0; i < steps; i++)
    {
      out[i] = i;
    }

  return TRUE;
}

static inline gdouble
clamp_log_lower (gdouble x)
{
  return x < MIN_LOG_VALUE ? MIN_LOG_VALUE : x;
}

gboolean
create_equidistant_data (gdouble start, gdouble stop, GraphsScale scale,
                         gdouble *out, gsize steps)
{
  if (steps < 2)
    return FALSE;

  const gdouble inv_steps = 1.0 / (gdouble)(steps - 1);

  switch (scale)
    {

    case GRAPHS_SCALE_LINEAR:
    case GRAPHS_SCALE_RADIANS:
      {

        const gdouble delta = stop - start;

#pragma omp parallel for simd
        for (gsize i = 0; i < steps; i++)
          {
            const double t = (double)i * inv_steps;
            out[i] = start + t * delta;
          }

        break;
      }

    case GRAPHS_SCALE_LOG:
      {

        start = clamp_log_lower (start);

        if (!isfinite (stop))
          stop = MAX_LOG_VALUE;

        const gdouble log_start = log10 (start);
        const gdouble log_stop = log10 (stop);
        const gdouble delta = log_stop - log_start;

#pragma omp parallel for simd
        for (gsize i = 0; i < steps; i++)
          {

            const gdouble t = (gdouble)i * inv_steps;

            out[i] = pow (10.0, log_start + t * delta);
          }

        break;
      }

    case GRAPHS_SCALE_LOG2:
      {

        start = clamp_log_lower (start);

        if (!isfinite (stop))
          stop = MAX_LOG_VALUE;

        const gdouble log_start = log2 (start);
        const gdouble log_stop = log2 (stop);
        const gdouble delta = log_stop - log_start;

#pragma omp parallel for simd
        for (gsize i = 0; i < steps; i++)
          {

            const gdouble t = (gdouble)i * inv_steps;

            out[i] = exp2 (log_start + t * delta);
          }

        break;
      }

    case GRAPHS_SCALE_SQUAREROOT:
      {

        start = clamp_log_lower (start);

        const gdouble sqrt_start = sqrt (start);
        const gdouble sqrt_stop = sqrt (stop);
        const gdouble delta = sqrt_stop - sqrt_start;

#pragma omp parallel for simd
        for (gsize i = 0; i < steps; i++)
          {

            const gdouble t = (double)i * inv_steps;

            const gdouble v = sqrt_start + t * delta;

            out[i] = v * v;
          }

        break;
      }

    case GRAPHS_SCALE_INVERSE:
      {

        const gdouble inv_start = 1.0 / start;
        const gdouble inv_stop = 1.0 / stop;
        const gdouble delta = inv_stop - inv_start;

#pragma omp parallel for simd
        for (gsize i = 0; i < steps; i++)
          {

            const gdouble t = (double)i * inv_steps;

            out[i] = 1.0 / (inv_start + t * delta);
          }

        break;
      }

    default:
      return FALSE;
    }

  return TRUE;
}

gsize
filter_nonfinite (gdouble *xdata, gdouble *ydata, gsize n)
{
  if (!xdata || !ydata || n == 0)
    return 0;

  gchar *mask = (gchar *)g_malloc_n (n, sizeof (gchar));
  gsize *prefix = (gsize *)g_malloc_n (n, sizeof (gsize));

  if (!mask || !prefix)
    {
      free (mask);
      free (prefix);
      return 0;
    }

    /* Build a mask for finite values */
#pragma omp parallel for
  for (gsize i = 0; i < n; ++i)
    {
      mask[i] = isfinite (ydata[i]) ? 1 : 0;
    }

  /* Build a prefix sum - carries loop depenency */
  int count = 0;
  for (gsize i = 0; i < n; ++i)
    {
      prefix[i] = count;
      count += mask[i];
    }

    /* Compact data in place */
#pragma omp parallel for
  for (gsize i = 0; i < n; ++i)
    {
      if (mask[i])
        {
          gsize dst = prefix[i];
          xdata[dst] = xdata[i];
          ydata[dst] = ydata[i];
        }
    }

  g_free (mask);
  g_free (prefix);

  return count;
}

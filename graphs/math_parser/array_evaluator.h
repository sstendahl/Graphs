#pragma once

#include <stddef.h>

#include "../graphs.h"

gdouble factorial (gdouble x);

gdouble ipow (gdouble base, gint exp);

void eval_array (const GraphsOpCode *program, const gdouble *data, gsize plen,
                 const gdouble *restrict xdata, gdouble *restrict ydata,
                 gsize n);

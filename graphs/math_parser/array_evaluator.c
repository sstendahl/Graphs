#include "array_evaluator.h"

#include <math.h>
#include <omp.h>

#define STACK_MAX 128

gdouble
factorial (gdouble x)
{
  if (x < 0.0)
    return NAN;

  return tgamma (x + 1.0);
}

gdouble
ipow (gdouble base, gint exp)
{
  gdouble result = 1;

  while (exp > 0)
    {
      if (exp & 1)
        result *= base;
      base *= base;
      exp >>= 1;
    }

  return result;
}

void
eval_array (const GraphsOpCode *program, const gdouble *data, gsize plen,
            const gdouble *restrict xdata, gdouble *restrict ydata, gsize n)
{
#pragma omp parallel for schedule(static)
  for (gsize i = 0; i < n; i++)
    {

      gdouble stack[STACK_MAX] = { 0 };
      gsize sp = 0;

      gdouble x = xdata[i];

      gsize dc = 0;
#pragma omp simd
      for (gsize pc = 0; pc < plen; pc++)
        {

          gdouble a, b;

          switch (program[pc])
            {

            case GRAPHS_OP_CODE_PUSH_CONST:
              stack[sp++] = data[dc++];
              break;

            case GRAPHS_OP_CODE_PUSH_X:
              stack[sp++] = x;
              break;

            case GRAPHS_OP_CODE_ADD:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a + b;
              break;

            case GRAPHS_OP_CODE_SUB:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a - b;
              break;

            case GRAPHS_OP_CODE_MUL:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a * b;
              break;

            case GRAPHS_OP_CODE_DIV:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a / b;
              break;

            case GRAPHS_OP_CODE_POW:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = pow (a, b);
              break;

            case GRAPHS_OP_CODE_IPOW:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = ipow (a, b);
              break;

            case GRAPHS_OP_CODE_NEG:
              stack[sp - 1] = -stack[sp - 1];
              break;

            case GRAPHS_OP_CODE_INV:
              stack[sp - 1] = 1 / stack[sp - 1];
              break;

            case GRAPHS_OP_CODE_FACT:
              stack[sp - 1] = factorial (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_SIN:
              stack[sp - 1] = sin (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_COS:
              stack[sp - 1] = cos (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_TAN:
              stack[sp - 1] = tan (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_ASIN:
              stack[sp - 1] = asin (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_ACOS:
              stack[sp - 1] = acos (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_ATAN:
              stack[sp - 1] = atan (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_LN:
              stack[sp - 1] = log (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_LOG2:
              stack[sp - 1] = log2 (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_LOG10:
              stack[sp - 1] = log10 (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_SQRT:
              stack[sp - 1] = sqrt (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_EXP:
              stack[sp - 1] = exp (stack[sp - 1]);
              break;

            case GRAPHS_OP_CODE_ABS:
              stack[sp - 1] = fabs (stack[sp - 1]);
              break;
            }
        }

      ydata[i] = stack[0];
    }
}

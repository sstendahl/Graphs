#include "array_evaluator.h"

#include <math.h>
#include <omp.h>

#define STACK_MAX 128

double
factorial (double x)
{
  if (x < 0.0)
    return NAN;

  return tgamma (x + 1.0);
}

double
ipow (double base, int exp)
{
  double result = 1;

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
eval_array (const Instruction *program, size_t plen,
            const double *restrict xdata, double *restrict ydata, size_t n)
{
#pragma omp parallel for schedule(static)
  for (size_t i = 0; i < n; i++)
    {

      double stack[STACK_MAX] = { 0 };
      int sp = 0;

      double x = xdata[i];

#pragma omp simd
      for (size_t pc = 0; pc < plen; pc++)
        {

          Instruction ins = program[pc];

          double a, b;

          switch (ins.op)
            {

            case PUSH_CONST:
              stack[sp++] = ins.value;
              break;

            case PUSH_X:
              stack[sp++] = x;
              break;

            case ADD:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a + b;
              break;

            case SUB:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a - b;
              break;

            case MUL:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a * b;
              break;

            case DIV:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = a / b;
              break;

            case POW:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = pow (a, b);
              break;

            case IPOW:
              b = stack[--sp];
              a = stack[--sp];
              stack[sp++] = ipow (a, b);
              break;

            case NEG:
              stack[sp - 1] = -stack[sp - 1];
              break;

            case FACT:
              stack[sp - 1] = factorial (stack[sp - 1]);
              break;

            case SIN:
              stack[sp - 1] = sin (stack[sp - 1]);
              break;

            case COS:
              stack[sp - 1] = cos (stack[sp - 1]);
              break;

            case TAN:
              stack[sp - 1] = tan (stack[sp - 1]);
              break;

            case LOG:
              stack[sp - 1] = log (stack[sp - 1]);
              break;

            case LOG2:
              stack[sp - 1] = log2 (stack[sp - 1]);
              break;

            case LOG10:
              stack[sp - 1] = log10 (stack[sp - 1]);
              break;

            case SQRT:
              stack[sp - 1] = sqrt (stack[sp - 1]);
              break;

            case EXP:
              stack[sp - 1] = exp (stack[sp - 1]);
              break;

            case ABS:
              stack[sp - 1] = fabs (stack[sp - 1]);
              break;

            case END_OP:
              pc = plen;
              break;
            }
        }

      ydata[i] = stack[0];
    }
}

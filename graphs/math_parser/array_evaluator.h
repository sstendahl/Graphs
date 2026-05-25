#pragma once

#include <stddef.h>

/* This is a copy of the enum in ast.vala */
typedef enum
{
  PUSH_CONST,
  PUSH_X,

  ADD,
  SUB,
  MUL,
  DIV,
  POW,
  IPOW,

  NEG,
  FACT,

  SIN,
  COS,
  TAN,
  LOG,
  LOG2,
  LOG10,
  SQRT,
  EXP,
  ABS,

  END_OP
} OpCode;

typedef struct
{
  OpCode op;
  double value;
} Instruction;

double factorial (double x);

double ipow (double base, int exp);

void eval_array (const Instruction *program, size_t plen,
                 const double *restrict xdata, double *restrict ydata,
                 size_t n);

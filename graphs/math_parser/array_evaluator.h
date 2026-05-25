#pragma once

#include <stddef.h>

/* This is a copy of the enum in ast.vala */
typedef enum
{
  // control
  PUSH_CONST,
  PUSH_X,

  // basic operands
  ADD,
  SUB,
  MUL,
  DIV,
  POW,
  IPOW,

  // pre and postfix
  NEG,
  INV,
  FACT,

  // trig
  SIN,
  COS,
  TAN,
  ASIN,
  ACOS,
  ATAN,

  // misc
  LN,
  LOG2,
  LOG10,
  SQRT,
  EXP,
  ABS
} OpCode;

double factorial (double x);

double ipow (double base, int exp);

void eval_array (const OpCode *program, const double *data, size_t plen,
                 const double *restrict xdata, double *restrict ydata,
                 size_t n);

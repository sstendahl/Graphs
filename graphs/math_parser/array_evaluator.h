#pragma once

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

void eval_array (const Instruction *program, int plen,
                 const double *restrict xdata, int xn, double *restrict ydata,
                 int yn);

// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs.MathParser {
    private class VariableFinder {
        private string[] variables;

        private static Once<VariableFinder> _instance;
        private static Mutex _mutex;

        public static unowned VariableFinder instance () {
            return _instance.once (() => { return new VariableFinder (); });
        }

        public string[] find_variables (Ast ast) {
            _mutex.lock ();
            this.variables = {};
            visit (ast.root ());
            _mutex.unlock ();
            return (owned) variables;
        }

        private void visit (Expression? expr) {
            if (expr == null) return;
            visit (expr.left ());
            check (expr);
            visit (expr.right ());
        }

        private void check (Expression expr) {
            if (expr.type () != VARIABLE) return;
            unowned string variable = expr.name ();
            if (variable == "x") return;
            if (variable in variables) return;

            variables += variable;
        }
    }
}

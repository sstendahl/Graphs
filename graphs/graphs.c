// SPDX-License-Identifier: GPL-3.0-or-later
#include <gtk/gtk.h>
#include <signal.h>
#include <stdlib.h>

#include <Python.h>

#include "config.h"
#include "libgraphs.h"

static void
handle_sigint (int sig)
{
  (void)sig;

  g_application_quit (g_application_get_default ());
}

static void
on_startup (GApplication *app, gpointer user_data)
{
  (void)app;
  (void)user_data;

  PyStatus status;
  PyConfig config;
  PyConfig_InitPythonConfig (&config);

  config.isolated = 0;
  config.use_environment = 1;

  status = Py_InitializeFromConfig (&config);
  PyConfig_Clear (&config);

  if (PyStatus_Exception (status))
    Py_ExitStatusException (status);

  PyObject *app_module = PyImport_ImportModule ("graphs");
  if (!app_module)
    {
      PyErr_Print ();
      g_error ("Fatal: cannot import graphs");
    }

  PyObject *func = PyObject_GetAttrString (app_module, "startup");

  if (!func || !PyCallable_Check (func))
    {
      PyErr_Print ();
      g_error ("graphs.startup missing");
    }

#ifdef DEBUG
  PyObject *debug = Py_True;
#else
  PyObject *debug = Py_False;
#endif

  Py_INCREF (debug);
  PyObject *args = PyTuple_Pack (3, debug, PyUnicode_FromString (LOCALEDIR),
                                 PyUnicode_FromString (GETTEXT_PACKAGE));
  PyObject *result = PyObject_CallObject (func, args);

  Py_XDECREF (result);
  Py_DECREF (func);

  if (PyErr_Occurred ())
    {
      PyErr_Print ();
      g_error ("Python startup failed");
    }
}

int
main (int argc, char **argv)
{
  signal (SIGINT, handle_sigint);

  GraphsApplication *app = graphs_application_new ();

  g_signal_connect (app, "startup", G_CALLBACK (on_startup), NULL);

  int status = g_application_run (G_APPLICATION (app), argc, argv);

  g_object_unref (app);
  Py_Finalize ();

  return status;
}

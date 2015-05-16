#include "swig_helper.h"

int PyDict_SetItemString_Steal(PyObject *p, const char *key, PyObject *val) {
  int r = PyDict_SetItemString(p, key, val);
  assert(val->ob_refcnt > 1);
  Py_DECREF(val);
  return r;
}

int PyList_Append_Steal(PyObject *list, PyObject *item) {
  int r = PyList_Append(list, item);
  assert(val->ob_refcnt > 1);
  Py_DECREF(item);
  return r;
}


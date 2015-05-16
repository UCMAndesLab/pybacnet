#ifndef __SWIG_HELPER_H__
#define __SWIG_HELPER_H__

#include <Python.h>

int PyDict_SetItemString_Steal(PyObject *p, const char *key, PyObject *val);
int PyList_Append_Steal(PyObject *list, PyObject *item);

#endif

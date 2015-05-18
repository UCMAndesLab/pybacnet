#ifndef __READ_MULTIPLE_PROP_H__
#define __READ_MULTIPLE_PROP_H__
#include <Python.h>
#include "bacapp.h"
#include "rpm.h"
#include "bactext.h"
void print_value(BACNET_APPLICATION_DATA_VALUE *value);
PyObject * handleRPMData(BACNET_READ_ACCESS_DATA *rpm_data);
#endif

#ifndef __READ_MULTIPLE_PROP_H__
#define __READ_MULTIPLE_PROP_H__

#include "bacapp.h"
#include "rpm.h"
#include <Python.h>

void read_multiple_prop_decode(BACNET_READ_ACCESS_DATA *rpm, BACNET_PROPERTY_REFERENCE *listOfProperties, BACNET_APPLICATION_DATA_VALUE *value);
void print_value(BACNET_APPLICATION_DATA_VALUE *value);
PyObject * handleRPMData(BACNET_READ_ACCESS_DATA *rpm_data, bool successful);
#endif

#include <Python.h>
#define BACTEXT_PRINT_ENABLED 1
#include "bacapp.h"
#include "stdio.h"
#include "rpm.h"
#include "handlers.h"
#include "swig_helper.h"
#include "bactext.h"

#include "read_multiple_properties.h"

void print_value(BACNET_APPLICATION_DATA_VALUE *value){
   switch (value->tag) {
        case BACNET_APPLICATION_TAG_OBJECT_ID:
          break;
        case BACNET_APPLICATION_TAG_CHARACTER_STRING:
          printf("%s", value->type.Character_String.value);
          break;
        case BACNET_APPLICATION_TAG_NULL:
          break;
        case BACNET_APPLICATION_TAG_BOOLEAN:
           printf("%i", (int)value->type.Boolean);
          break;
        case BACNET_APPLICATION_TAG_UNSIGNED_INT:
           printf("%i", (int)value->type.Unsigned_Int);
          break;
        case BACNET_APPLICATION_TAG_SIGNED_INT:
           printf("%i", (int)value->type.Signed_Int);
          break;
        case BACNET_APPLICATION_TAG_REAL:
           printf("%f", (double)value->type.Real);
          break;
        case BACNET_APPLICATION_TAG_DOUBLE:
           printf("%f", (double)value->type.Double);
          break;
        case BACNET_APPLICATION_TAG_ENUMERATED:
          printf("%i", value->type.Enumerated);
          break;
        default:
          fprintf(stderr,"Unknown tag %d\n", value->tag);
   }
}

// Moving decode here
PyObject * bacnet_value_to_python(BACNET_APPLICATION_DATA_VALUE *value){
   switch (value->tag) {
      case BACNET_APPLICATION_TAG_OBJECT_ID:
      {
        PyObject *rec = PyDict_New();
        PyDict_SetItemString_Steal(rec, "type", Py_BuildValue("i",value->type.Object_Id.type));
        if (value->type.Object_Id.type < MAX_ASHRAE_OBJECT_TYPE) {
          PyDict_SetItemString_Steal(rec, "type_str", 
            Py_BuildValue("s",bactext_object_type_name(value->type.Object_Id.type)));
        }
        PyDict_SetItemString_Steal(rec, "instance", Py_BuildValue("i",value->type.Object_Id.instance));
        return rec;
      }
      case BACNET_APPLICATION_TAG_CHARACTER_STRING:
        return Py_BuildValue("s", value->type.Character_String.value);
        break;
      case BACNET_APPLICATION_TAG_NULL:
        return Py_None;
        break;
      case BACNET_APPLICATION_TAG_BOOLEAN:
        return Py_BuildValue("i", (int)value->type.Boolean);
        break;
      case BACNET_APPLICATION_TAG_UNSIGNED_INT:
        return Py_BuildValue("I", (int)value->type.Unsigned_Int);
        break;
      case BACNET_APPLICATION_TAG_SIGNED_INT:
        return Py_BuildValue("i", (int)value->type.Signed_Int);
        break;
      case BACNET_APPLICATION_TAG_REAL:
        return Py_BuildValue("d", (double)value->type.Real);
        break;
      case BACNET_APPLICATION_TAG_DOUBLE:
        return Py_BuildValue("d", (double)value->type.Double);
        break;
      case BACNET_APPLICATION_TAG_ENUMERATED:
        return Py_BuildValue("i", (int)value->type.Enumerated);
        break;
      default:
        fprintf(stderr,"Unknown tag %d\n", value->tag);
      
   }
   return Py_None;
}


// Free all rpm data and print if successful
PyObject * handleRPMData(BACNET_READ_ACCESS_DATA *rpm_data){
   BACNET_PROPERTY_REFERENCE *rpm_property;
   BACNET_PROPERTY_REFERENCE *old_rpm_property;
   BACNET_READ_ACCESS_DATA *old_rpm_data;
   BACNET_APPLICATION_DATA_VALUE *value;
   BACNET_APPLICATION_DATA_VALUE *old_value;     

   PyObject * returnData = PyList_New(0);
   // Bundle contains instance, property, type
   PyObject * bundle;
   PyObject * entryArray;
   PyObject * entry;

   // Get Data 
   while (rpm_data) {
      rpm_property = rpm_data->listOfProperties;
//      rpm_ack_print_data(rpm_data);
      // Get Properties
      while (rpm_property) {
         // Get new values
         entryArray = PyList_New(0);
         value = rpm_property->value;

          // This is for array support. We are just making new entries for each
          // value
         while (value) {
            entry = bacnet_value_to_python(value);
            PyList_Append_Steal(entryArray, entry);

            // Free value
            old_value = value;
            value = value->next;
            free(old_value);
         }
         // If we only have one value, turn the list to a single value
         if (PyList_Size(entryArray) == 1) {
             PyObject *new_ret = PyList_GetItem(entryArray, 0);
             Py_INCREF(new_ret);
             Py_DECREF(entryArray);
             entryArray = new_ret;
         } 

         // Create a data bundle to store
         bundle = PyDict_New();
         PyDict_SetItemString_Steal(bundle, "object_type", Py_BuildValue("i", rpm_data->object_type));
         PyDict_SetItemString_Steal(bundle, "object_instance",Py_BuildValue("i", rpm_data->object_instance));
         PyDict_SetItemString_Steal(bundle, "property", Py_BuildValue("i", rpm_property->propertyIdentifier));
         PyDict_SetItemString_Steal(bundle, "array_index", Py_BuildValue("i", rpm_property->propertyArrayIndex));
         PyDict_SetItemString_Steal(bundle, "data", entryArray);

         // Append Data Bundle
         PyList_Append_Steal(returnData, bundle);

         // release property
         old_rpm_property = rpm_property;
         rpm_property = rpm_property->next;
         free(old_rpm_property);
      }

      // release data
      old_rpm_data = rpm_data;
      rpm_data = rpm_data->next;
      free(old_rpm_data);
   }
   return returnData;
}

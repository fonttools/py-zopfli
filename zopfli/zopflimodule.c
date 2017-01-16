#define PY_SSIZE_T_CLEAN size_t
#include <Python.h>
#include <stdlib.h>
#include "zlib_container.h"
#include "gzip_container.h"
#include "util.h"


static PyObject *
zopfli_compress(PyObject *self, PyObject *args, PyObject *keywrds)
{
  const unsigned char *in;
  unsigned char *out;
  size_t insize=0; 
  size_t outsize=0;  
  Options options;
  InitOptions(&options);
  options.verbose = 0;
  options.numiterations = 15;
  options.blocksplitting = 1;
  options.blocksplittinglast = 0;
  options.blocksplittingmax = 15;
  int gzip_mode = 0;
  static char *kwlist[] = {"data", "verbose", "numiterations", "blocksplitting", "blocksplittinglast", "blocksplittingmax", "gzip_mode", NULL};
  
  if (!PyArg_ParseTupleAndKeywords(args, keywrds, "s#|iiiiii", kwlist, &in, &insize,
				   &options.verbose,
				   &options.numiterations,
				   &options.blocksplitting,
				   &options.blocksplittinglast,
				   &options.blocksplittingmax,
				   &gzip_mode))
    return NULL;
  if (args)
    Py_INCREF(args);
  if (keywrds)
    Py_INCREF(keywrds);
  Py_BEGIN_ALLOW_THREADS
    
  if (!gzip_mode) 
    ZlibCompress(&options, in, insize, &out, &outsize);
  else 
    GzipCompress(&options, in, insize, &out, &outsize);
  
  Py_END_ALLOW_THREADS
  if (args)
    Py_DECREF(args);

  if (keywrds)
    Py_DECREF(keywrds);
  
  PyObject *returnValue;
  returnValue = Py_BuildValue("s#", out, outsize);
  free(out);
  return returnValue;
}


static char docstring[] = "" 
  "zopfli.zopfli.compress applies zopfli zip or gzip compression to an obj." 
  "" \
  "zopfli.zopfli.compress("
  "  s, **keywrds, verbose=0, numiterations=15, blocksplitting=1, "
  "  blocksplittinglast=0, blocksplittingmax=15, gzip_mode=0)"
  ""
  "If gzip_mode is set to a non-zero value, a Gzip compatbile container will "
  "be generated, otherwise a zlib compatible container will be generated. ";


static PyObject *ZopfliError;

static PyMethodDef ZopfliMethods[] = {
  { "compress", zopfli_compress,  METH_KEYWORDS, docstring},

  { NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC
initzopfli(void)
{
  PyObject *m;

  m = Py_InitModule("zopfli", ZopfliMethods);
  if (m == NULL) 
    return;

  ZopfliError = PyErr_NewException("zopfli.error", NULL, NULL);
  Py_INCREF(ZopfliError);
  PyModule_AddObject(m, "error", ZopfliError);
}


#define PY_SSIZE_T_CLEAN size_t
#include <Python.h>
#include <bytesobject.h>
#include <stdlib.h>

#ifdef SYSTEM_ZOPFLI
#define ZOPFLI_H <zopfli.h>
#else
#define ZOPFLI_H "../zopfli/src/zopfli/zopfli.h"
#endif
#include ZOPFLI_H
#include "../zopfli/src/zopfli/deflate.h"

#if PY_MAJOR_VERSION >= 3
#define PyInt_Check PyLong_Check
#define PyInt_AsLong PyLong_AsLong
#endif

static PyObject *
zopfli_compress(PyObject *self, PyObject *args, PyObject *keywrds)
{
  const unsigned char *in;
  unsigned char *out;
  size_t insize=0; 
  size_t outsize=0;  
  ZopfliOptions options;
  int gzip_mode = 0;
  static char *kwlist[] = {"data", "verbose", "numiterations", "blocksplitting", "blocksplittinglast", "blocksplittingmax", "gzip_mode", NULL};
  PyObject *returnValue;

  ZopfliInitOptions(&options);
  options.verbose = 0;
  options.numiterations = 15;
  options.blocksplitting = 1;
  options.blocksplittinglast = 0;
  options.blocksplittingmax = 15;
  
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

  ZopfliFormat output_type = gzip_mode ? ZOPFLI_FORMAT_GZIP : ZOPFLI_FORMAT_ZLIB;
  ZopfliCompress(&options, output_type, in, insize, &out, &outsize);
  
  Py_END_ALLOW_THREADS
  if (args)
    Py_DECREF(args);

  if (keywrds)
    Py_DECREF(keywrds);
  
  returnValue = PyBytes_FromStringAndSize((char*)out, outsize);
  free(out);
  return returnValue;
}

static PyObject *
zopfli_deflate(PyObject *self, PyObject *args, PyObject *keywrds)
{
  const unsigned char *in, *out;
  unsigned char *in2, *out2;
  size_t insize=0;
  size_t prehist=0; 
  size_t outsize=0;  
  ZopfliOptions options;
  ZopfliInitOptions(&options);
  options.verbose = 0;
  options.numiterations = 15;
  options.blocksplitting = 1;
  options.blocksplittinglast = 0;
  options.blocksplittingmax = 15;
  int blocktype = 2;
  int blockfinal = 1;
  unsigned char bitpointer = 0;
  
  static char *kwlist[] = {"data", "verbose", "numiterations", "blocksplitting", "blocksplittinglast", "blocksplittingmax", "blocktype","blockfinal","bitpointer","old_tail","prehist", NULL};
  
  if (!PyArg_ParseTupleAndKeywords(args, keywrds, "y#|iiiiiiiBy#i", kwlist, &in, &insize,
				   &options.verbose,
				   &options.numiterations,
				   &options.blocksplitting,
				   &options.blocksplittinglast,
				   &options.blocksplittingmax,
				   &blocktype,
				   &blockfinal,
				   &bitpointer,
				   &out, &outsize,
				   &prehist))
    return NULL;

  Py_BEGIN_ALLOW_THREADS
  in2 = malloc(insize);
  memcpy(in2, in, insize);
  out2 = malloc(outsize);
  memcpy(out2, out, outsize);
  
  ZopfliDeflatePart(&options, blocktype, blockfinal, in2, prehist, insize, &bitpointer, &out2, &outsize);
  
  free(in2);
  Py_END_ALLOW_THREADS
  PyObject *returnValue;
  returnValue = Py_BuildValue("y#B", out2, outsize, bitpointer);
  free(out2);
  return returnValue;
}

PyDoc_STRVAR(compress__doc__,
  "zopfli.zopfli.compress applies zopfli zip or gzip compression to an obj." 
  "" \
  "zopfli.zopfli.compress("
  "  s, **keywrds, verbose=0, numiterations=15, blocksplitting=1, "
  "  blocksplittinglast=0, blocksplittingmax=15, gzip_mode=0)"
  ""
  "If gzip_mode is set to a non-zero value, a Gzip compatbile container will "
  "be generated, otherwise a zlib compatible container will be generated. ");

PyDoc_STRVAR(deflate__doc__,
  "zopfli.zopfli.deflate applies zopfli deflate compression to an obj."
  "" \
  "zopfli.zopfli.deflate("
  "  s, **kwargs, verbose=0, numiterations=15, blocksplitting=1, "
  "  blocksplittinglast=0, blocksplittingmax=15, "
  "  blocktype=2, blockfinal=1, bitpointer=0, oldtail='', prehist=0)"
  ""
  "Partitial compression also possible");

static PyObject *ZopfliError;

static PyMethodDef ZopfliMethods[] = {
  { "compress", (PyCFunction)zopfli_compress, METH_VARARGS | METH_KEYWORDS, compress__doc__},
  { "deflate", (PyCFunction)zopfli_deflate, METH_VARARGS | METH_KEYWORDS, deflate__doc__},
  { NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(zopfli__doc__,
"Wrapper around zopfli's ZlibCompress and GzipCompress methods.");

#if PY_MAJOR_VERSION >= 3
#define INIT_ZOPFLI   PyInit_zopfli
#define CREATE_ZOPFLI PyModule_Create(&zopfli_module)
#define RETURN_ZOPFLI return m

static struct PyModuleDef zopfli_module = {
  PyModuleDef_HEAD_INIT,
  "zopfli",
  zopfli__doc__,
  0,
  ZopfliMethods,
  NULL,
  NULL,
  NULL
};
#else
#define INIT_ZOPFLI   initzopfli
#define CREATE_ZOPFLI Py_InitModule3("zopfli", ZopfliMethods, zopfli__doc__)
#define RETURN_ZOPFLI return
#endif

PyMODINIT_FUNC INIT_ZOPFLI(void) {
  PyObject *m = CREATE_ZOPFLI;

  ZopfliError = PyErr_NewException((char*) "zopfli.error", NULL, NULL);
  if (ZopfliError != NULL) {
    Py_INCREF(ZopfliError);
    PyModule_AddObject(m, "error", ZopfliError);
  }

  RETURN_ZOPFLI;
}


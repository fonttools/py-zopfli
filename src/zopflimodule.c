#define PY_SSIZE_T_CLEAN size_t
#include <Python.h>
#include <bytesobject.h>
#include <stdlib.h>

#ifdef SYSTEM_ZOPFLI
#define ZOPFLI_H <zopfli.h>
#define ZOPFLIPNG_H <zopflipng_lib.h>
#else
#define ZOPFLI_H "../zopfli/src/zopfli/zopfli.h"
#define ZOPFLIPNG_H "../zopfli/src/zopflipng/zopflipng_lib.h"
#endif
#include ZOPFLI_H
#include ZOPFLIPNG_H

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

PyDoc_STRVAR(compress__doc__,
  "zopfli.zopfli.compress applies zopfli zip or gzip compression to an obj." 
  "" \
  "zopfli.zopfli.compress("
  "  s, **keywrds, verbose=0, numiterations=15, blocksplitting=1, "
  "  blocksplittinglast=0, blocksplittingmax=15, gzip_mode=0)"
  ""
  "If gzip_mode is set to a non-zero value, a Gzip compatbile container will "
  "be generated, otherwise a zlib compatible container will be generated. ");

static inline int
is_str(PyObject* v)
{
    if (PyUnicode_Check(v)) {
        return 1;
    }
    PyErr_Format(PyExc_TypeError, "expected str, got '%.200s'", Py_TYPE(v)->tp_name);
    return 0;
}

static int
parse_filter_strategies(CZopfliPNGOptions *options, PyObject *filter_strategies)
{
  int i, num_filter_strategies;
  PyObject* b = NULL;
  char* s;
  if (!is_str(filter_strategies)) {
    return -1;
  }
  b = PyUnicode_AsASCIIString(filter_strategies);
  if (b == NULL) {
    return -1;
  }
  s = PyBytes_AsString(b);
  if (s == NULL) {
    return -1;
  }
  num_filter_strategies = strlen(s);

  options->filter_strategies = (enum ZopfliPNGFilterStrategy*)malloc(num_filter_strategies * sizeof(enum ZopfliPNGFilterStrategy));
  if (options->filter_strategies == NULL) {
    PyErr_SetNone(PyExc_MemoryError);
    return -1;
  }

  for (i = 0; *s != '\0'; ++i, ++s) {
    enum ZopfliPNGFilterStrategy fs;
    switch (*s) {
    case '0':
      fs = kStrategyZero;
      break;
    case '1':
      fs = kStrategyOne;
      break;
    case '2':
      fs = kStrategyTwo;
      break;
    case '3':
      fs = kStrategyThree;
      break;
    case '4':
      fs = kStrategyFour;
      break;
    case 'm':
      fs = kStrategyMinSum;
      break;
    case 'e':
      fs = kStrategyEntropy;
      break;
    case 'p':
      fs = kStrategyPredefined;
      break;
    case 'b':
      fs = kStrategyBruteForce;
      break;
    default:
      PyErr_Format(PyExc_ValueError, "unknown filter strategy: %c", *s);
      free(options->filter_strategies);
      return -1;
    }
    options->filter_strategies[i] = fs;
  }

  options->num_filter_strategies = num_filter_strategies;
  options->auto_filter_strategy = 0;

  return 0;
}

static int
parse_keepchunks(CZopfliPNGOptions *options, PyObject *keepchunks)
{
  int j;
  PyObject* u = NULL;
  PyObject* b = NULL;
  Py_ssize_t i, n = PySequence_Size(keepchunks);
  if (n < 0) {
    goto err;
  }
  options->keepchunks = (char **)calloc(n, sizeof(char *));
  if (options->keepchunks == NULL) {
    options->num_keepchunks = 0;
    PyErr_SetNone(PyExc_MemoryError);
    goto err;
  }
  options->num_keepchunks = n;

  for (i = 0; i < n; ++i) {
    u = PySequence_GetItem(keepchunks, i);
    if (u == NULL || !is_str(u)) {
      goto err;
    }
    b = PyUnicode_AsASCIIString(u);
    if (b == NULL) {
      goto err;
    }
    char* s = PyBytes_AsString(b);
    if (s == NULL) {
      goto err;
    }
    options->keepchunks[i] = malloc(strlen(s) + 1);
    if (options->keepchunks[i] == NULL) {
      PyErr_SetNone(PyExc_MemoryError);
      goto err;
    }
    strcpy(options->keepchunks[i], s);
    Py_CLEAR(u);
    Py_CLEAR(b);
  }

  return 0;

err:
  Py_XDECREF(u);
  Py_XDECREF(b);
  for (j = 0; j < options->num_keepchunks; ++j) {
    free(options->keepchunks[j]);
  }
  free(options->keepchunks);
  return -1;
}

static PyObject *
zopfli_png_optimize(PyObject *self, PyObject *args, PyObject *keywrds)
{
  PyObject* returnValue = NULL;
  const unsigned char *in;
  unsigned char *out;
  size_t insize = 0;
  size_t outsize = 0;
  int err, i;
  int verbose = 0;
  PyObject* filter_strategies = Py_None;
  PyObject* keepchunks = Py_None;
  static char *kwlist[] = {
    "data",
    "verbose",
    "lossy_transparent",
    "lossy_8bit",
    "filter_strategies",
    "keepchunks",
    "use_zopfli",
    "num_iterations",
    "num_iterations_large",
    NULL,
  };
  CZopfliPNGOptions options;
  CZopfliPNGSetDefaults(&options);

  if (!PyArg_ParseTupleAndKeywords(args, keywrds,
                                   "s#|iiiOOiii", kwlist,
                                   &in, &insize,
                                   &verbose,
                                   &options.lossy_transparent,
                                   &options.lossy_8bit,
                                   &filter_strategies,
                                   &keepchunks,
                                   &options.use_zopfli,
                                   &options.num_iterations,
                                   &options.num_iterations_large))
    return NULL;
  if (args)
    Py_INCREF(args);
  if (keywrds)
    Py_INCREF(keywrds);

  if (filter_strategies != Py_None && parse_filter_strategies(&options, filter_strategies) != 0) {
    return returnValue;
  }
  if (keepchunks != Py_None && parse_keepchunks(&options, keepchunks) != 0) {
    return returnValue;
  }

  Py_BEGIN_ALLOW_THREADS
  err = CZopfliPNGOptimize(in, insize, &options, verbose, &out, &outsize);
  Py_END_ALLOW_THREADS

  if (err) {
    PyErr_SetString(PyExc_ValueError, "verification failed");
    return returnValue;
  }

  if (args)
    Py_DECREF(args);

  if (keywrds)
    Py_DECREF(keywrds);

  returnValue = PyBytes_FromStringAndSize((char*)out, outsize);
  free(out);
  free(options.filter_strategies);
  for (i = 0; i < options.num_keepchunks; ++i) {
    free(options.keepchunks[i]);
  }
  free(options.keepchunks);
  return returnValue;
}

PyDoc_STRVAR(png_optimize__doc__,
  "zopfli.png.optimize(\n"
  "    data,\n"
  "    *,\n"
  "    verbose=False,\n"
  "    lossy_transparent=False,\n"
  "    lossy_8bit=False,\n"
  "    filter_strategies=None,\n"
  "    keepchunks=None,\n"
  "    use_zopfli=True,\n"
  "    num_iterations=15,\n"
  "    num_iterations_large=5,\n"
  ")\n"
  "\n"
  "Args:\n"
  "    data (bytes): input PNG data.\n"
  "    verbose (bool): print more debugging info.\n"
  "    lossy_transparent (bool): remove colors behind alpha channel 0.\n"
  "    lossy_8bit (bool): convert 16-bit per channel image to 8-bit per channel.\n"
  "    filter_strategies (str): filter strategies to try (cf. zopflipng --help)\n"
  "    keepchunks (Sequence[str]): keep metadata chunks with these names that \n"
  "        would normally be removed (cf. zopflipng --help)\n"
  "    num_iterations (int): number of iterations for small files (default: 15).\n"
  "    num_iterations_large (int): number of iterations for large files (default: 5).\n"
  "Returns:\n"
  "    Bytes string containing the compressed PNG data.\n");

static PyObject *ZopfliError;

static PyMethodDef ZopfliMethods[] = {
  { "compress", (PyCFunction)zopfli_compress, METH_VARARGS | METH_KEYWORDS, compress__doc__},
  { "png_optimize", (PyCFunction)zopfli_png_optimize, METH_VARARGS | METH_KEYWORDS, png_optimize__doc__},
  { NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(zopfli__doc__,
"Wrapper around zopfli's ZlibCompress, GzipCompress and ZopfliPNGOptimize methods.");

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

PyMODINIT_FUNC INIT_ZOPFLI(void) {
  PyObject *m = CREATE_ZOPFLI;

  ZopfliError = PyErr_NewException((char*) "zopfli.error", NULL, NULL);
  if (ZopfliError != NULL) {
    Py_INCREF(ZopfliError);
    PyModule_AddObject(m, "error", ZopfliError);
  }

  RETURN_ZOPFLI;
}


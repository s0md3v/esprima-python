|Donate| |PyPI Version| |PyPI License| |PyPI Format| |PyPI Status|

**Esprima** (`esprima.org <https://esprima.org>`__, BSD license) is a
high performance, standard-compliant
`ECMAScript <https://www.ecma-international.org/publications-and-standards/standards/ecma-262/>`__
parser officially written in ECMAScript (also popularly known as
`JavaScript <https://en.wikipedia.org/wiki/JavaScript>`__) and ported to
Python. Esprima is created and maintained by `Ariya
Hidayat <https://twitter.com/ariyahidayat>`__, with the help of `many
contributors <https://github.com/jquery/esprima/contributors>`__.

Python port is a line-by-line manual translation and was created and is
maintained by `German Mendez Bravo
(Kronuz) <https://twitter.com/germbravo>`__.

Features
~~~~~~~~

-  Full support for ECMAScript 2024 (`ECMA-262 15th
   Edition <https://www.ecma-international.org/publications-and-standards/standards/ecma-262/>`__) including ES2018-ES2024 syntax features
-  Sensible `syntax tree
   format <https://github.com/estree/estree/blob/master/es5.md>`__ as
   standardized by `ESTree project <https://github.com/estree/estree>`__
-  Experimental support for `JSX <https://facebook.github.io/jsx/>`__, a
   syntax extension for `React <https://facebook.github.io/react/>`__
-  Optional tracking of syntax node location (index-based and
   line-column)
-  `Heavily tested <https://esprima.org/test/ci.html>`__ (~1500 `unit
   tests <https://github.com/jquery/esprima/tree/master/test/fixtures>`__
   with `full code
   coverage <https://codecov.io/github/jquery/esprima>`__)

Installation
~~~~~~~~~~~~

.. code:: shell

    pip install esprima

API
~~~

Esprima can be used to perform `lexical
analysis <https://en.wikipedia.org/wiki/Lexical_analysis>`__
(tokenization) or `syntactic
analysis <https://en.wikipedia.org/wiki/Parsing>`__ (parsing) of a
JavaScript program.

A simple example:

.. code:: javascript

    >>> import esprima
    >>> program = 'const answer = 42'

    >>> esprima.tokenize(program)
    [{
        type: "Keyword",
        value: "const"
    }, {
        type: "Identifier",
        value: "answer"
    }, {
        type: "Punctuator",
        value: "="
    }, {
        type: "Numeric",
        value: "42"
    }]

    >>> esprima.parseScript(program)
    {
        body: [
            {
                kind: "const",
                declarations: [
                    {
                        init: {
                            raw: "42",
                            type: "Literal",
                            value: 42
                        },
                        type: "VariableDeclarator",
                        id: {
                            type: "Identifier",
                            name: "answer"
                        }
                    }
                ],
                type: "VariableDeclaration"
            }
        ],
        type: "Program",
        sourceType: "script"
    }

Modern syntax support (ES2018-2024):

.. code:: javascript

    >>> # ES2020: BigInt and nullish coalescing
    >>> esprima.parseScript('const big = 123n; const x = a ?? b;', ecmaVersion=2020)
    
    >>> # ES2021: Private class fields and logical assignment
    >>> esprima.parseScript('class C { #private = 1; } a ||= b;', ecmaVersion=2021)
    
    >>> # ES2022: Top-level await (in modules)
    >>> esprima.parseModule('await import("module");', ecmaVersion=2022)

For more information, please read the `complete
documentation <https://esprima.org/doc/>`__.

.. |Donate| image:: https://img.shields.io/badge/Donate-PayPal-green.svg
   :target: https://www.paypal.me/Kronuz/25
.. |PyPI Version| image:: https://img.shields.io/pypi/v/esprima.svg
   :target: https://pypi.python.org/pypi/esprima
.. |PyPI License| image:: https://img.shields.io/pypi/l/esprima.svg
   :target: https://pypi.python.org/pypi/esprima
.. |PyPI Wheel| image:: https://img.shields.io/pypi/wheel/esprima.svg
   :target: https://pypi.python.org/pypi/esprima
.. |PyPI Format| image:: https://img.shields.io/pypi/format/esprima.svg
   :target: https://pypi.python.org/pypi/esprima
.. |PyPI Python Version| image:: https://img.shields.io/pypi/pyversions/esprima.svg
   :target: https://pypi.python.org/pypi/esprima
.. |PyPI Implementation| image:: https://img.shields.io/pypi/implementation/esprima.svg
   :target: https://pypi.python.org/pypi/esprima
.. |PyPI Status| image:: https://img.shields.io/pypi/status/esprima.svg
   :target: https://pypi.python.org/pypi/esprima
.. |PyPI Downloads| image:: https://img.shields.io/pypi/dm/esprima.svg
   :target: https://pypi.python.org/pypi/esprima

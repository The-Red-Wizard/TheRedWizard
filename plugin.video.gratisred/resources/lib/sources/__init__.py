# -*- coding: utf-8 -*-

import os
import pkgutil

from six import PY2, PY3

from resources.lib.modules import log_utils

__all__ = [x[1] for x in os.walk(os.path.dirname(__file__))][0]


def sources():
    sourceDict = []
    for i in __all__:
        for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.join(os.path.dirname(__file__), i)]):
            if is_pkg:
                continue
            try:
                if PY2:
                    module = loader.find_module(module_name).load_module(module_name)
                elif PY3:
                    module = loader.find_spec(module_name).loader.load_module(module_name)
                else: # Dummy finish maybe for future use lol.
                    module = loader.find_spec(module_name).loader.load_module(module_name)
                sourceDict.append((module_name, module.source()))
            except Exception as e:
                log_utils.log('Provider loading Error - "%s" : %s' % (module_name, e), 1)
    return sourceDict



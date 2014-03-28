# Copyright (C) 2013  Statoil ASA, Norway.
#   
#  The file 'test_work_area.py' is part of ERT - Ensemble based Reservoir Tool. 
#   
#  ERT is free software: you can redistribute it and/or modify 
#  it under the terms of the GNU General Public License as published by 
#  the Free Software Foundation, either version 3 of the License, or 
#  (at your option) any later version. 
#   
#  ERT is distributed in the hope that it will be useful, but WITHOUT ANY 
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or 
#  FITNESS FOR A PARTICULAR PURPOSE.   
#   
#  See the GNU General Public License at <http://www.gnu.org/licenses/gpl.html> 
#  for more details.

from ert.cwrap import BaseCClass, CWrapper
from ert.enkf import ENKF_LIB, EnKFMain


class ErtTest(BaseCClass):
    def __init__(self, test_name, model_config, site_config=None, store_area=False):
        c_ptr = ErtTest.cNamespace().alloc(test_name, model_config, site_config)
        super(ErtTest, self).__init__(c_ptr)
        self.setStore(store_area)

    def setStore(self, store):
        ErtTest.cNamespace().set_store(self, store)

    def getErt(self):
        """ @rtype: EnKFMain """
        return ErtTest.cNamespace().get_enkf_main(self)

    def free(self):
        ErtTest.cNamespace().free(self)


class ErtTestContext(object):
    def __init__(self, test_name, model_config, site_config=None, store_area=False):
        self.__test_name = test_name
        self.__model_config = model_config
        self.__site_config = site_config
        self.__store_area = store_area
        self.__test_context = None


    def __enter__(self):
        """ @rtype: ErtTest """
        self.__test_context = ErtTest(self.__test_name, self.__model_config, site_config=self.__site_config, store_area=self.__store_area)
        return self.__test_context


    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.__test_context
        return False


    def getErt(self):
        return self.__test_context.getErt()


cwrapper = CWrapper(ENKF_LIB)
cwrapper.registerObject("ert_test", ErtTest)

ErtTest.cNamespace().alloc = cwrapper.prototype("c_void_p ert_test_context_alloc( char* , char* , char*)")
ErtTest.cNamespace().set_store = cwrapper.prototype("c_void_p ert_test_context_set_store( ert_test , bool)")
ErtTest.cNamespace().free = cwrapper.prototype("void ert_test_context_free( ert_test )")
ErtTest.cNamespace().get_enkf_main = cwrapper.prototype("enkf_main_ref ert_test_context_get_main( ert_test )")


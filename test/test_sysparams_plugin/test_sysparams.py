##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from sysparams_plugin.sysparamsplugin import SysparamsPlugin
from sysparams_plugin.sysparamsplugin import (
    get_key_and_call_id
)
from sysparams_extension.sysparamsextension import SysparamsPluginExtension

from litp.core.plugin_context_api import PluginApiContext
from litp.extensions.core_extension import CoreExtension
from litp.core.model_manager import ModelManager
from litp.core.plugin_manager import PluginManager
from litp.core.model_item import ModelItem
from litp.core.task import ConfigTask
from litp.core.validators import ValidationError

import unittest

from litp.core.translator import Translator
t = Translator('ERIClitpsysparams_CXP9031229')
_ = t._


class TestSysparamsPlugin(unittest.TestCase):

    def setUp(self):
        self.model = ModelManager()
        self.plugin_manager = PluginManager(self.model)
        self.context = PluginApiContext(self.model)
        self.plugin_manager.add_property_types(
            CoreExtension().define_property_types())
        self.plugin_manager.add_item_types(
            CoreExtension().define_item_types())

        self.plugin_manager.add_default_model()
        self.plugin = SysparamsPlugin()
        self.plugin_manager.add_plugin('TestPlugin', 'some.test.plugin',
                                       '1.0.0', self.plugin)

        self.plugin_manager.add_property_types(
            SysparamsPluginExtension().define_property_types())
        self.plugin_manager.add_item_types(
            SysparamsPluginExtension().define_item_types())

    def setup_model(self):
        # Use ModelManager.crete_item and ModelManager.create_link
        # to create and reference (i.e.. link) items in the model.
        # These correspond to CLI/REST verbs to create or link
        # items.
        self.node1 = self.model.create_item("node", "/node1",
                                            hostname="node1")
        self.node2 = self.model.create_item("node", "/node2",
                                            hostname="special")

    def query(self, item_type=None, **kwargs):
        # Use PluginApiContext.query to find items in the model
        # properties to match desired item are passed as kwargs.
        # The use of this method is not required, but helps
        # plugin developer mimic the run-time environment
        # where plugin sees QueryItem-s.
        return self.context.query(item_type, **kwargs)

    def test_validate_model(self):
        self.setup_model()
        # Invoke plugin's methods to run test cases
        # and assert expected output.
        errors = self.plugin.validate_model(self)
        self.assertEqual(0, len(errors))

    def test_create_configuration(self):
        self.setup_model()
        # Invoke plugin's methods to run test cases
        # and assert expected output.
        tasks = self.plugin.create_configuration(self)
        self.assertEqual(0, len(tasks))

    def _create_standard_items_ok(self):
        self.sys1_url = "/infrastructure/systems/system1"
        self.cluster_url = "/deployments/local_vm/clusters/cluster1"
        self.node1_url = "/deployments/local_vm/clusters/cluster1/nodes/node1"
        self.model.create_root_item("root", "/")
        self.model.create_item('deployment', '/deployments/local_vm')
        self.model.create_item('cluster', self.cluster_url)

        # Nodes
        self.model.create_item("node", self.node1_url,
                            hostname="node1")

        # new network model
        self.model.create_item(
            'network',
            '/infrastructure/networking/networks/mgmt_network',
            name='mgmt',
            subnet='10.0.1.0/24',
            litp_management='true'
        )
        self.model.create_item(
            'network',
            '/infrastructure/networking/networks/hrbt_ntwk',
            name='heartbleed',
            subnet='10.0.2.0/24'
        )

        # MS NIC
        self.model.create_item(
            'eth',
            '/ms/network_interfaces/if0',
            network_name="mgmt",
            device_name="eth0",
            ipaddress="10.0.1.10",
            macaddress='08:00:27:5B:C1:3F'
        )

        # Node 1 NICs
        self.model.create_item(
            'eth',
            self.node1_url + "/network_interfaces/if0",
            network_name="mgmt",
            device_name="eth0",
            ipaddress="10.0.1.0",
            macaddress='08:00:27:5B:C1:3F'
        )
        self.model.create_item(
            'eth',
            self.node1_url + "/network_interfaces/if1",
            network_name="heartbleed",
            device_name="eth1",
            ipaddress="10.0.2.0",
            macaddress='08:00:27:5B:C1:3F'
        )

    def test_update_node_alias(self):
        self._create_standard_items_ok()

        self.model.create_item("sysparam-node-config",
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf")
        self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param1",
            key="11.11.11.1", value="master1")

        node1 = self.context.query_by_vpath(
            "/deployments/local_vm/clusters/cluster1/nodes/node1")

        config = self.context.query_by_vpath(
            "/deployments/local_vm/clusters/cluster1/nodes/"
            "node1/configs/sysparamconf/params/param1")

        tasks = self.plugin.create_configuration(self.context)

        test_task = ConfigTask(node1, config,
            "Set system parameter \"%s\" to \"%s\" on node \"%s\"" % (
                config.key, config.value, node1.hostname),
                               "sysparam::param",
                               "test_set_sysparam",
                               key=config.key,
                               value=config.value,
                               ensure="present")
        test_task.model_items = set([self.model.get_item(
            "/nodes/node1/configs/sysparamconf")])
        self.assertEquals(test_task.model_item, tasks[0].model_item)
        self.assertEquals(test_task.item_vpath, tasks[0].item_vpath)
        self.assertEquals(test_task.kwargs['ensure'],
                          tasks[0].kwargs['ensure'])
        self.assertEquals(test_task.description, tasks[0].description)

    def test_node_alias_validate_two_confs(self):
        self._create_standard_items_ok()

        self.model.create_item("sysparam-node-config",
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf")
        self.model.create_item("sysparam-node-config",
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf2")

        results = self.plugin.validate_model(self.context)
        only_one_config_err = _("ONLY_ONE_CONFIG_PER_NODE_ERR")

        err1 = ValidationError(item_path="/deployments/local_vm/clusters/"
                               "cluster1/nodes/node1/configs/sysparamconf2",
                               error_message=only_one_config_err)
        err2 = ValidationError(item_path="/deployments/local_vm/clusters/"
                               "cluster1/nodes/node1/configs/sysparamconf",
                               error_message=only_one_config_err)
        errors = set([err1, err2])
        self.assertEquals(2, len(results))
        self.assertEqual(errors, set(results))

    def test_node_alias_remove_single_param(self):
        self._create_standard_items_ok()

        config_vpath = ("/deployments/local_vm/clusters/cluster1"
                        "/nodes/node1/configs/sysparamconf")
        self.model.create_item("sysparam-node-config", config_vpath)

        item = self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param1",
            key="myKeyParam", value="master1")

        item.set_for_removal()

        tasks = self.plugin.create_configuration(self.context)
        self.assertEqual(1, len(tasks))
        self.assertEquals("absent", tasks[0].kwargs['ensure'])
        self.assertEqual([config_vpath],
                         [x.vpath for x in tasks[0].model_items])

    def test_node_alias_remove_containing_config(self):
        self._create_standard_items_ok()

        config_vpath = ("/deployments/local_vm/clusters/cluster1"
                        "/nodes/node1/configs/sysparamconf")
        item = self.model.create_item("sysparam-node-config", config_vpath)

        self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param1",
            key="myKeyParam", value="master1")

        self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param2",
            key="anotherKeyParam", value="master2")

        item.set_for_removal()
        tasks = self.plugin.create_configuration(self.context)
        self.assertEquals(2, len(tasks))
        for task in tasks:
            self.assertEquals("absent", task.kwargs['ensure'])
            self.assertEqual([config_vpath],
                             [x.vpath for x in task.model_items])


    def test_node_validate_duplicate_sysparams (self):
        self._create_standard_items_ok()

        self.model.create_item("sysparam-node-config",
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf")

        self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param1",
            key="myKeyParam", value="master1")
        self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param2",
            key="myKeyParam", value="master1")
        dup_err = (_("DUPLICATE_SYSPARAM_KEY_ERR") %"myKeyParam>")
        results = self.plugin.validate_model(self.context)
        self.assertEquals(("</deployments/local_vm/clusters/cluster1/nodes/"+
           "node1/configs/sysparamconf/params/param1 - ValidationError - "
            + dup_err) , str(results[0]))

        self.assertEquals(2, len(results))

    def test_node_validate_parameters (self):
        self._create_standard_items_ok()

        self.model.create_item("sysparam-node-config",
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf")

        result = self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param1",
            key="myKeyParam")
        self.assertFalse(isinstance(result, ModelItem))
        self.assertEqual(
            {'message': 'ItemType "sysparam" is required to have a'\
                ' property with name "value"',
             'property_name': 'value',
             'error': 'MissingRequiredPropertyError'},
            result[0].to_dict())

    def test_rename_key(self):
        self._create_standard_items_ok()

        self.model.create_item("sysparam-node-config",
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf")

        item = self.model.create_item("sysparam",
            "/deployments/local_vm/clusters/cluster1/nodes"
            "/node1/configs/sysparamconf/params/param1",
            key="test.key.to.rename", value="1")

        item.set_applied()

        self.model.update_item(
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf/params/param1",
            key="a.new.key")
        err = self.plugin.validate_model(self.context)[0]
        self.assertEquals("ValidationError", err.error_type)
        key_name_err = (_("KEY_NAME_CANT_BE_UPDATED_ERR") %"test.key.to.rename")
        self.assertEquals(key_name_err , err.error_message)
        self.assertEquals(
           "/deployments/local_vm/clusters/cluster1/nodes/node1/configs/sysparamconf/params/param1",
            err.item_path)

    def test__get_key_and_call_id(self):
        self._create_standard_items_ok()
        node = self.model.get_item(self.node1_url)
        self.model.create_item("sysparam-node-config",
            "/deployments/local_vm/clusters/cluster1"
            "/nodes/node1/configs/sysparamconf")

        param_vpath = ("/deployments/local_vm/clusters/cluster1/nodes"
                       "/node1/configs/sysparamconf/params/param1")
        key = "11.11.11.1"

        self.model.create_item("sysparam", param_vpath,
                               key=key, value="master1")
        from litp.core.model_manager import QueryItem
        param = QueryItem(self.model,
                          self.model.query_by_vpath(param_vpath))


        self.assertEqual(type(param), QueryItem)

        self.assert_(param is not None)
        self.assert_('key' not in param.applied_properties)

        expected = key, '%s_%s_%s' % (node.properties['hostname'],
                                          param_vpath,
                                          key)
        actual = get_key_and_call_id(param, node)
        self.assertEqual(expected, actual)

        param._model_item.set_applied()
        expected = key, '%s_%s_%s' % (node.properties['hostname'],
                                      param_vpath,
                                      key)
        actual = get_key_and_call_id(param, node)
        self.assertEqual(expected, actual)

        other_key = "11.11.11.2"
        self.model.update_item(param.vpath, key=other_key)
        self.assertNotEqual(param.key,
                            param.applied_properties['key'])

        expected = key, '%s_%s_%s' % (node.properties['hostname'],
                                      param_vpath,
                                      key)
        actual = get_key_and_call_id(param, node)
        self.assertEqual(expected, actual)

        param._model_item.set_applied()
        expected = other_key, '%s_%s_%s' % (node.properties['hostname'],
                                            param_vpath,
                                            other_key)
        actual = get_key_and_call_id(param, node)
        self.assertEqual(expected, actual)

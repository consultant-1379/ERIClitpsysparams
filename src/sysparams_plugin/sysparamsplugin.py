##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.plugin import Plugin
from litp.core.validators import ValidationError
from litp.core.task import ConfigTask
from litp.core.litp_logging import LitpLogger
log = LitpLogger()

from litp.core.translator import Translator
t = Translator('ERIClitpsysparams_CXP9031229')
_ = t._


class SysparamsPlugin(Plugin):
    """
    The LITP sysparams plugin class creates the configuration tasks required to
    configure the system control parameters.
    The plugin creates name value pairs for node kernel parameters
    (sysctl) configuration.
    Only one 'sysparam-node-config' may be configured per node.
    Update and remove reconfiguration actions are supported for this plugin.
    """

    def validate_model(self, plugin_api_context):
        """
         The validation makes sure that only one 'sysparam-node-config'
         may be configured per node. It also ensures that there are no
         duplicate sysparam keys.
        """

        errors = []

        nodes = plugin_api_context.query("node") + \
            plugin_api_context.query("ms")
        for node in nodes:
            if not node.is_for_removal():
                configs = [x for x in node.query("sysparam-node-config")
                           if not x.is_for_removal()]
                if len(configs) > 1:
                    for config in configs:
                        errors.append(ValidationError(
                            item_path=config.get_vpath(),
                            error_message=_("ONLY_ONE_CONFIG_PER_NODE_ERR")
                        ))
                for sp_n_config in configs:
                    sysparamkeys = {}

                    for param in sp_n_config.params:
                        key = param.properties['key']
                        if param.is_for_removal():
                            continue
                        applied_key = param.applied_properties.get('key')
                        if applied_key is not None and applied_key != key:
                            message = _(
                                "KEY_NAME_CANT_BE_UPDATED_ERR"
                            ) % applied_key
                            errors.append(ValidationError(
                                item_path=param.get_vpath(),
                                error_message=message))
                        elif key in sysparamkeys:
                            message = _("DUPLICATE_SYSPARAM_KEY_ERR") % key
                            for path in (param.get_vpath(), sysparamkeys[key]):
                                errors.append(
                                    ValidationError(
                                        item_path=path,
                                        error_message=message))
                        else:
                            sysparamkeys[key] = param.get_vpath()
        return errors

    def create_configuration(self, plugin_api_context):
        """
        The following CLI illustrates how to create a system parameter node
        configuration:

        *Example cli for creating a sysparam rule on a node:*

        .. code-block:: bash

          litp create -t sysparam-node-config \
-p /deployments/local_vm/clusters/cluster1/nodes/node1/configs/mynodesysctl
          litp create -t sysparam \
-p /deployments/local_vm/clusters/cluster1/nodes/node1\
/configs/mynodesysctl/params/sysctl001 \
-o key="kernel.pid_max" value="3276"

        *Example XML for configuring a sysparam on a node*

        .. code-block:: bash

            <?xml version='1.0' encoding='utf-8'?>
            <litp:sysparam-node-config \
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xmlns:litp="http://www.ericsson.com/litp" \
xsi:schemaLocation="http://www.ericsson.com/litp litp-xml-schema/litp.xsd" \
id="mynodesysctl">
              <litp:sysparam-node-config-params-collection id="params">
                <litp:sysparam id="sysctl001">
                  <key>sunrpc.nfs_debug</key>
                  <value>1</value>
                </litp:sysparam>
                <litp:sysparam id="sysctl002">
                  <key>sunrpc.rpc_debug</key>
                  <value>0</value>
                </litp:sysparam>
                <litp:sysparam id="sysctl003">
                  <key>crypto.fips_enabled</key>
                  <value>1</value>
                </litp:sysparam>
              </litp:sysparam-node-config-params-collection>
            </litp:sysparam-node-config>

        For more information, see "Manage Kernel Parameters" \
from :ref:`LITP References <litp-references>`.

        """

        tasks = []

        for item_type in ('node', 'ms'):
            for node in plugin_api_context.query(item_type):
                if node.is_for_removal() or node.is_removed():
                    continue
                for config in node.query("sysparam-node-config"):
                    for param in config.params:
                        if config.is_for_removal():
                            param._model_item.set_for_removal()
                        tasks.extend(create_tasks(config, param, node))
        return tasks


def create_tasks(config, param, node):
    tasks = []
    if param.is_initial():
        tasks.append(create_present_task(config, param, node))
    elif param.is_updated():
        tasks.append(create_update_task(config, param, node))
    elif param.is_for_removal():
        tasks.append(create_remove_task(config, param, node))
    return tasks


def create_present_task(config, param, node):
    return create_task(
        config, param, node,
        'Set system parameter "{key}" to "{value}" on node "{hostname}"',
        "present")


# for some reason they were separate and identical
create_update_task = create_present_task


def create_remove_task(config, param, node):
    return create_task(
        config, param, node,
        'Remove system parameter "{key}" on node "{hostname}"',
        "absent")


def create_task(config, param, node, description_template, ensure):
    key, call_id = get_key_and_call_id(param, node)
    value = param.properties['value']
    task = ConfigTask(
        node,
        param,
        description_template.format(key=key,
                                    hostname=node.hostname,
                                    value=value),
        "sysparams::param",
        call_id,
        key=key,
        value=value,
        ensure=ensure
    )
    task.model_items.add(config)
    return task


def get_key_and_call_id(param, node):
    original_key = param.applied_properties.get('key',
                                                param.properties['key'])
    call_id = "%s_%s_%s" % (
        node.hostname, param.get_vpath(), original_key)
    return original_key, call_id

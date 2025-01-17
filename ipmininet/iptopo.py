"""This module defines topology class that supports adding L3 routers"""
from builtins import str

import functools

from mininet.topo import Topo
from mininet.log import lg

from ipmininet.overlay import Overlay, Subnet
from ipmininet.utils import get_set
from ipmininet.router.config import BasicRouterConfig, OSPFArea, AS,\
    iBGPFullMesh, OpenrDomain


class IPTopo(Topo):
    """A topology that supports L3 routers"""

    OVERLAYS = {cls.__name__: cls
                for cls in (AS, iBGPFullMesh, OpenrDomain, OSPFArea, Subnet)}

    def __init__(self, *args, **kwargs):
        self.overlays = []
        self.phys_interface_capture = {}
        super(IPTopo, self).__init__(*args, **kwargs)

    def build(self, *args, **kwargs):
        for o in self.overlays:
            o.apply(self)
        for o in self.overlays:
            if not o.check_consistency(self):
                lg.error('Consistency checks for', str(o),
                         'overlay have failed!\n')
        super(IPTopo, self).build(*args, **kwargs)

    def post_build(self, net):
        """A method that will be invoced once the topology has been fully built
        and before it is started.

        :param net: The freshly built (Mininet) network"""

    def isNodeType(self, n, x):
        """Return wether node n has a key x set to True

        :param n: node name
        :param x: the key to check"""
        try:
            return self.g.node[n].get(x, False)
        except KeyError:  # node not found
            return False

    def addRouter(self, name, **kwargs):
        """Add a router to the topology

        :param name: the name of the node"""
        return RouterDescription(self.addNode(str(name), isRouter=True, **kwargs), self)

    def addLink(self, node1, node2, port1=None, port2=None,
                key=None, **opts):
        """:param node1: first node to link
           :param node2: second node to link
           :param port1: port of the first node (optional)
           :param port2: port of the second node (optional)
           :param key: a key to identify the link (optional)
           :param opts: link options (optional)
           :return: link info key"""

        # XXX When PR https://github.com/mininet/mininet/pull/895
        # is accepted, we can replace this code by a call to the
        # super() method
        
        if not opts and self.lopts:
            opts = self.lopts
        port1, port2 = self.addPort(node1, node2, port1, port2)
        opts = dict(opts)
        opts.update(node1=node1, node2=node2, port1=port1, port2=port2)
        key = self.g.add_edge(node1, node2, key, opts)
        # Create an abstraction to allow additional calls
        link_description = LinkDescription(self, node1, node2, key, self.linkInfo(node1, node2, key))
        return link_description

    def addDaemon(self, router, daemon, default_cfg_class=BasicRouterConfig,
                  cfg_daemon_list="daemons", **daemon_params):
        """Add the daemon to the list of daemons to start on the router.

        :param router: router name
        :param daemon: daemon class
        :param default_cfg_class: config class to use
            if there is no configuration class defined for the router yet.
        :param cfg_daemon_list: name of the parameter containing
            the list of daemons in your config class constructor.
            For instance, RouterConfig uses 'daemons'
            but BasicRouterConfig uses 'additional_daemons'.
        :param daemon_params: all the parameters to give
            when instantiating the daemon class."""

        config = self.nodeInfo(router).setdefault("config", default_cfg_class)
        try:
            config_params = config[1]
        except (IndexError, TypeError):
            config_params = {cfg_daemon_list: []}
            self.nodeInfo(router)["config"] = (config, config_params)

        daemon_list = config_params.setdefault(cfg_daemon_list, [])
        daemon_list.append((daemon, daemon_params))
    
    def addHub(self, name, **opts):
        """Convenience method: Add hub to graph.
           name: hub name
           opts: hub options
           returns: hub name"""
        if not opts and self.sopts:
            opts = self.sopts
        result = self.addSwitch( name, hub=True, **opts )
        return result

    def isRouter(self, n):
        """Check whether the given node is a router

        :param n: node name"""
        return self.isNodeType(n, 'isRouter')

    def hosts(self, sort=True):
        # The list is already sorted, simply filter out the routers
        return [h for h in super(IPTopo, self).hosts(sort)
                if not self.isRouter(h)]

    def routers(self, sort=True):
        """Return a list of router node names"""
        return [n for n in self.nodes(sort) if self.isRouter(n)]

    def addOverlay(self, overlay):
        """Add a new overlay on this topology"""
        if not isinstance(overlay, Overlay) and issubclass(overlay, Overlay):
            overlay = overlay()
        self.overlays.append(overlay)

    def __getattr__(self, item):
        if item.startswith('add'):
            try:
                return OverlayWrapper(self, self.OVERLAYS[item[3:]])
            except KeyError:
                pass
        raise AttributeError('%s is neither a method of IPTopo'
                             ' nor refers to any known overlay' % item)

    def getNodeInfo(self, n, key, default):
        """Attempt to retrieve the information for the given node/key
        combination. If not found, set to an instance of default and return
        it"""
        return get_set(self.nodeInfo(n), key, default)

    def getLinkInfo(self, l, key, default):
        """Attempt to retrieve the information for the given link/key
        combination. If not found, set to an instance of default and return
        it"""
        return get_set(self.linkInfo(l[0], l[1]), key, default)

    def capture_physical_interface(self, intfname, node):
        """Adds a pre-existing physical interface to the given node."""
        self.phys_interface_capture[intfname] = node


class OverlayWrapper(object):

    def __init__(self, topo, overlay):
        self.topo = topo
        self.overlay = overlay

    def __call__(self, *args, **kwargs):
        return self.topo.addOverlay(self.overlay(*args, **kwargs))


class RouterDescription(str):

    def __new__(cls, value, *args, **kwargs):
        return super(RouterDescription, cls).__new__(cls, value)

    def __init__(self, o, topo):
        self.topo = topo
        super(RouterDescription, self).__init__()

    def addDaemon(self, daemon, default_cfg_class=BasicRouterConfig,
                  cfg_daemon_list="daemons", **daemon_params):
        """Add the daemon to the list of daemons to start on the router.

        :param daemon: daemon class
        :param default_cfg_class: config class to use
            if there is no configuration class defined for the router yet.
        :param cfg_daemon_list: name of the parameter containing
            the list of daemons in your config class constructor.
            For instance, RouterConfig uses 'daemons'
            but BasicRouterConfig uses 'additional_daemons'.
        :param daemon_params: all the parameters to give
            when instantiating the daemon class."""

        self.topo.addDaemon(self, daemon, default_cfg_class=default_cfg_class,
                            cfg_daemon_list=cfg_daemon_list, **daemon_params)


@functools.total_ordering
class LinkDescription(object):

    def __init__(self, topo, src, dst, key, link_attrs):
        self.src = src
        self.dst = dst
        self.key = key
        self.link_attrs = link_attrs
        self.src_intf = IntfDescription(self.src, topo, self,
                                        self.link_attrs.setdefault("params1", {}))
        self.dst_intf = IntfDescription(self.dst, topo, self,
                                        self.link_attrs.setdefault("params2", {}))
        super(LinkDescription, self).__init__()

    def __getitem__(self, item):
        if isinstance(item, int):
            if item == 0:
                return self.src_intf
            elif item == 1:
                return self.dst_intf
            elif item == 3:
                return self.key
            raise IndexError("Links have only two nodes and one key")
        else:
            if item == self.src:
                return self.src_intf
            elif item == self.dst:
                return self.dst_intf
            raise KeyError("Node '%s' is not on this link" % item)

    # The following methods allow this object to behave like an edge key
    # for mininet.topo.MultiGraph

    def __hash__(self):
        return self.key.__hash__()

    def __eq__(self, other):
        return self.key == other

    def __lt__(self, other):
        return self.key.__lt__(other)


class IntfDescription(RouterDescription):

    def __init__(self, o, topo, link, intf_attrs):
        self.link = link
        self.node = o
        self.intf_attrs = intf_attrs
        super(IntfDescription, self).__init__(o, topo)

    def addParams(self, **kwargs):
        self.intf_attrs.update(kwargs)

    def __hash__(self):
        return self.node.__hash__()

    def __eq__(self, other):
        return self.node.__eq__(other)

"""Order a template by dependencies.

Take an unordered list of resources from a template and put them into an
ordered list of resources.
"""


def removeItem(data, item, key=None):
    """Remove a key or array item from a source."""
    if key:
        del data[item]
    else:
        data.remove(item)


def getLoadBalancerDeps(LBs, data):
    """Generate a resource list for LBs and dependencies."""
    loadBalancers = list()
    for lb in LBs:
        for servers in getMatch(data, "servers", key="servers"):
            for server in servers:
                if lb['be_servers'] == server['name']:
                    loadBalancers.append(
                        {lb['name']: {
                            "load_balancer": lb,
                            "servers": server
                        }}
                    )
                    removeItem(data["servers"], server)
    removeItem(data, "load_balancers", key=True)
    return loadBalancers


def getMatch(dataToMatch, match, field=None, key=None):
    """For a given Dict that contains lists, check a field against a match."""
    for k, v in dataToMatch.items():
        if key:
            if k == match:
                yield v
        elif field:
            if k is field and v is match:
                yield v
        else:
            yield "Key or field needed."


def getOrderedList(data):
    """Given a Dictionary, generate a ordered list."""
    orderedList = list()
    # Loop through dependencies first
    dataCopy = data.copy()
    for resource, resources in dataCopy.items():
        items = dict()
        if resource in filter:
            items[resource] = filter[resource](resources, data)
            orderedList.append(items)
    # For everything that remains in data...
    for k, v in data.items():
        items = dict()
        items[k] = v
        orderedList.append(items)
    order = {
        "tags": 0,
        "networks": 1,
        "servers": 2,
        "load_balancers": 3
    }
    orderedList.sort(key=lambda val: order[list(val)[0]])
    return orderedList


filter = {
    "load_balancers": getLoadBalancerDeps
}

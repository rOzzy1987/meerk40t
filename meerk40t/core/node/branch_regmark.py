from meerk40t.core.node.node import Node


class BranchRegmarkNode(Node):
    """
    Branch Regmark Node.
    Bootstrapped type: 'branch reg'
    """

    def __init__(self, **kwargs):
        super(BranchRegmarkNode, self).__init__(**kwargs)
        self._formatter = "{element_type}"

    def default_map(self, default_map=None):
        default_map = super(BranchRegmarkNode, self).default_map(default_map=default_map)
        default_map["element_type"] = "Regmark"
        return default_map

    def drop(self, drag_node):
        if drag_node.type.startswith("elem"):
            self.append_child(drag_node)
            return True
        elif drag_node.type == "group":
            self.append_child(drag_node)
            return True
        return False

    def is_movable(self):
        return False

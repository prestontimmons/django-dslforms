from django.template.loader_tags import BlockNode


def get_node(template, name):
    for node in template.nodelist.get_nodes_by_type(BlockNode):
        if node.name == name:
            return node


def render_node(template, name, context):
    node = get_node(template, name)
    if node:
        return node.render(context).strip()
    return ""

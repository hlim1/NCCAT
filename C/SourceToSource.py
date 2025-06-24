import json
import sys
import re

from pycparser import parse_file, c_ast, c_generator
from pycparser.plyparser import Coord

RE_CHILD_ARRAY = re.compile(r'(.*)\[(.*)\]')
RE_INTERNAL_ATTR = re.compile('__.*__')

class CJsonError(Exception):
    pass

def memodict(fn):
    """ Fast memoization decorator for a function taking a single argument """
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = fn(key)
            return ret
    return memodict().__getitem__


@memodict
def child_attrs_of(klass):
    """
    Given a Node class, get a set of child attrs.
    Memoized to avoid highly repetitive string manipulation

    """
    non_child_attrs = set(klass.attr_names)
    all_attrs = set([i for i in klass.__slots__ if not RE_INTERNAL_ATTR.match(i)])
    return all_attrs - non_child_attrs


def to_dict(node):
    """ Recursively convert an ast into dict representation. """
    klass = node.__class__

    result = {}

    # Metadata
    result['_nodetype'] = klass.__name__

    # Local node attributes
    for attr in klass.attr_names:
        result[attr] = getattr(node, attr)

    # Coord object
    if node.coord:
        result['coord'] = str(node.coord)
    else:
        result['coord'] = None

    # Child attributes
    for child_name, child in node.children():
        # Child strings are either simple (e.g. 'value') or arrays (e.g. 'block_items[1]')
        match = RE_CHILD_ARRAY.match(child_name)
        if match:
            array_name, array_index = match.groups()
            array_index = int(array_index)
            # arrays come in order, so we verify and append.
            result[array_name] = result.get(array_name, [])
            if array_index != len(result[array_name]):
                raise CJsonError('Internal ast error. Array {} out of order. '
                    'Expected index {}, got {}'.format(
                    array_name, len(result[array_name]), array_index))
            result[array_name].append(to_dict(child))
        else:
            result[child_name] = to_dict(child)

    # Any child attributes that were missing need "None" values in the json.
    for child_attr in child_attrs_of(klass):
        if child_attr not in result:
            result[child_attr] = None

    return result

def file_to_dict(filename):
    """ Load C file into dict representation of ast """
    ast = parse_file(filename, use_cpp=True)
    return to_dict(ast)

def _parse_coord(coord_str):
    """ Parse coord string (file:line[:column]) into Coord object. """
    if coord_str is None:
        return None

    vals = coord_str.split(':')
    vals.extend([None] * 3)
    filename, line, column = vals[:3]
    return Coord(filename, line, column)


def _convert_to_obj(value):
    """
    Convert an object in the dict representation into an object.
    Note: Mutually recursive with from_dict.

    """
    value_type = type(value)
    if value_type == dict:
        return from_dict(value)
    elif value_type == list:
        return [_convert_to_obj(item) for item in value]
    else:
        # String
        return value

def from_dict(node_dict):
    """ Recursively build an ast from dict representation """
    class_name = node_dict.pop('_nodetype')

    klass = getattr(c_ast, class_name)

    # Create a new dict containing the key-value pairs which we can pass
    # to node constructors.
    objs = {}
    for key, value in node_dict.items():
        if key == 'coord':
            objs[key] = _parse_coord(value)
        else:
            objs[key] = _convert_to_obj(value)

    # Use keyword parameters, which works thanks to beautifully
    # consistent ast Node initializers.
    return klass(**objs)

def ast_to_c(ast):

    generator = c_generator.CGenerator()
    ast = from_dict(ast)
    return generator.visit(ast)

def astEditor(ast: dict, target_node_id: int, depth: int):
    """This function traverses the ast and seek for the target node 
    by comparing the passed target node id. Then, if found, edits 
    (mutates) the node.

    args:
        ast (dict): ast to scan.
        target_node_id (int): target node id to edit.
        depth (int): tree depth.

    returns:
        (int) tree depth.
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if value:
                        for elem in value:
                            depth = astEditor(elem, target_node_id, depth) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    print (depth, ast)
                    if depth == target_node_id:
                        pass
                        #return depth
                    depth = astEditor(
                            value, target_node_id, depth) + 1
                else:
                    depth += 1
        else:
            depth += 1

    if '_nodetype' in ast and depth == target_node_id:
        pass

    return depth

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Converts pycparser 'ast' object to python 'dict' object.
        ast_dict = file_to_dict(sys.argv[1])
        depth = astEditor(ast_dict, 0, 1,)
        # Converts python 'dict' object to pycparser 'ast' object.
        ast = from_dict(ast_dict)
        print (ast)
        # Converts pycparser 'ast' object to c code and prints it.
        generator = c_generator.CGenerator()
        print(generator.visit(ast))
    else:
        print("Please provide a filename as argument")

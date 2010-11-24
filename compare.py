"""
This is an implementation of the Zhang and Shasha algorithm as
described in [FIXME]

SWAN 2007-11-01: I'm pretty sure this code comes from:
http://www.cs.queensu.ca/TechReports/Reports/1995-372.pdf and
http://www.inf.unibz.it/dis/teaching/ATA/ata7-handout-1x1.pdf
"""

import collections
from editdist import distance as strdist
import tree

INSERT = 0
DELETE = 1
RENAME = 2
IDENTITY = 3

def distance(a, b):
    """Find the edit distance between two trees specified using the test_metricspace.py format"""
    return find_distance_raw(tree.convert_tree(a), tree.convert_tree(b))

def multidim_arr(val, *dims):
    """Initialize a multidimensional array"""
    return [multidim_arr(val, *dims[1:]) for i in xrange(dims[0])] if dims else val

def default_replace_cost_func(a_node_id, b_node_id, a_tree, b_tree):
    """Find cost to replace a_string with b_string"""
    a_string = a_tree.get_label_for_matching(a_node_id)
    b_string = b_tree.get_label_for_matching(b_node_id)
    
    return strdist(a_string, b_string)

def find_distance_raw(a_tree, b_tree, ops=None):
    """Find the edit distance between two trees in the tree.py format. Specify `ops` if
    the cost functions need to be more sophisticated."""
    
    # Default cost functions
    ops = ops or {
        INSERT: lambda *args: 1,
        DELETE: lambda *args: 1,
        RENAME: default_replace_cost_func
    }
    
    # For the most faithful reproduction of the algorithm given in the paper,
    # we must use 1-indexing
    distance = multidim_arr(0.0, len(a_tree)+1, len(b_tree)+1)
    
    # Find leftmost leaves and key roots
    a_left_leaf = {}
    b_left_leaf = {}
    a_tree_key_roots = []
    b_tree_key_roots = []
    
    find_helper_tables(a_tree, a_left_leaf, a_tree_key_roots, a_tree.get_root_id())
    find_helper_tables(b_tree, b_left_leaf, b_tree_key_roots, b_tree.get_root_id())
    
    # Comparison
    for a_key_root in a_tree_key_roots:
        for b_key_root in b_tree_key_roots:
            # Re-initialise forest distance tables
            fD = collections.defaultdict(lambda: collections.defaultdict(lambda: 0.0))
            
            a_null = a_left_leaf[a_key_root]
            b_null = b_left_leaf[b_key_root]
            fD[a_null][b_null] = 0.0
            
            # for all descendents of aKeyroot: i
            for i in xrange(a_null, a_key_root+1):
                label_cost = ops[DELETE](i, 0, a_tree, b_tree)
                fD[i][b_null] = fD[i-1][b_null] + label_cost

            # for all descendents of bKeyroot: j
            for j in xrange(b_null, b_key_root+1):
                label_cost = ops[INSERT](0, j, a_tree, b_tree)
                fD[a_null][j] = fD[a_null][j-1] + label_cost
            
            # for all descendents of aKeyroot: i
            for i in xrange(a_null, a_key_root+1):
                for j in xrange(b_null, b_key_root+1):
                    if a_left_leaf[i] == a_null and b_left_leaf[j] == b_null:
                        fD[i][j] = min(
                            # Option 1: Delete node from a_tree
                            fD[i-1][j] + ops[DELETE](i, 0, a_tree, b_tree),
                            # Option 2: Insert node into b_tree
                            fD[i][j-1] + ops[INSERT](0, j, a_tree, b_tree),
                            # Option 3: Rename
                            fD[i-1][j-1] + ops[RENAME](i, j, a_tree,b_tree)
                        )
                        distance[i][j] = fD[i][j]
                    else:
                        fD[i][j] = min(
                            # Option 1: Delete node from a_tree
                            fD[i-1][j] + ops[DELETE](i, 0, a_tree, b_tree),
                            # Option 2: Insert node into b_tree
                            fD[i][j-1] + ops[INSERT](0, j, a_tree, b_tree),
                            # Option 3: Rename
                            fD[a_left_leaf[i]-1][b_left_leaf[j]-1] + distance[i][j]
                        )
    
    return distance[len(a_tree)][len(b_tree)]

def find_helper_tables(some_tree, leftmost_leaves, keyroots, root_id):
    """Finds leftmost leaves and keyroots for a tree. Node IDs must be derived from the 
    post-ordering of the nodes."""
    
    find_helper_tables_recurse(some_tree, leftmost_leaves, keyroots, root_id)

    # Root node is a keyroot
    keyroots.append(root_id)

    # Boundary
    leftmost_leaves[0] = 0

def find_helper_tables_recurse(some_tree, leftmost_leaves, keyroots, a_node_id):
    # If this is a leaf, then it is the leftmost leaf
    if some_tree.is_leaf(a_node_id):
        leftmost_leaves[a_node_id] = a_node_id
    else:
        seen_leftmost = False
        for child in some_tree.get_children_ids(a_node_id):
            find_helper_tables_recurse(some_tree, leftmost_leaves, keyroots, child)
            if not seen_leftmost:
                leftmost_leaves[a_node_id] = leftmost_leaves[child]
                seen_leftmost = True
            else:
                keyroots.append(child)

__author__ = 'rgriffin'
'''
------------------------------------------
data
Author: Ryan Griffin
email: ryan.griffin@firaxis.com
------------------------------------------

Methods for handling data structures such as dictionaries.
'''


def insertIntoDataStruct(name,data,aDict):
    """
    Inserts data into an existing dictionary key
    :param name: The name of the key
    :param data: The data to insert
    :param aDict: The dictionary being referenced
    :return:
    """
    if not name in aDict:
        aDict[name] = [(data)]
    else:
        aDict[name].append((data))

def traverse(dat, tree_types=(list, tuple)):
    """
    Traverses a data structure
    :param dat: A list or tuple
    :param tree_types:
    :return:
    """
    flat_tree = []
    if isinstance(dat, tree_types):
        for value in dat:
            for subvalue in traverse(value, tree_types):
                flat_tree.append(subvalue)
    else:
        flat_tree.append(dat)

    return flat_tree


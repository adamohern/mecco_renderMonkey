# python

import lx, lxu, lxifc

import monkey
from monkey.symbols import *
from monkey.util import markup, bitwise_rgb, bitwise_hex
# from monkey.util import debug, breakpoint

from os.path import basename

# Text Colors
RED = markup('c', bitwise_rgb(255, 0, 0))
BLUE = markup('c', bitwise_hex('#0e76b7'))
GRAY = markup('c', '4113')

# Font Styles
FONT_DEFAULT = markup('f', 'FONT_DEFAULT')
FONT_NORMAL = markup('f', 'FONT_NORMAL')
FONT_BOLD = markup('f', 'FONT_BOLD')
FONT_ITALIC = markup('f', 'FONT_ITALIC')


class TreeNode(object):

    _primary = None

    def __init__(self, key, value=None, parent=None, node_type=None, value_type=None, selectable=True):
        self._key = key
        self._value = value
        self._parent = parent
        self._node_region = node_type
        self._value_type = value_type
        self._children = []
        self._state = 0
        self._selected = False
        self._selectable = selectable
        self._tooltips = {}

        self._columns = ((COL_NAME, -1), (COL_VALUE, -3))

    @classmethod
    def set_primary(cls, primary=None):
        cls._primary = primary

    @classmethod
    def primary(cls):
        return cls._primary

    def add_child(self, key, value=None, node_type=None, value_type=None, selectable=True):
        self._children.append(TreeNode(key, value, self, node_type, value_type, selectable))
        return self._children[-1]

    def clear_children(self):
        if len(self._children) > 0:
            for child in self._children:
                self._children.remove(child)

    def clear_selection(self):
        if self._primary:
            self.set_primary(None)

        self.set_selected(False)

        for child in self._children:
            child.clear_selection()

    def set_selected(self, val=True):
        if val:
            self.set_primary(self)
        self._selected = val

    def is_selected(self):
        return self._selected

    def state(self):
        return self._state

    def set_state(self, state):
        self._state = state

    def add_state_flag(self, flag):
        self._state = self._state | flag

    def set_tooltip(self, idx, tip):
        self._tooltips[idx] = tip

    def tooltip(self, idx):
        if idx in self._tooltips:
            return self._tooltips[idx]

    def raw_value(self):
        return self._value

    def display_value(self):
        m = ''
        if self._value_type in (list.__name__, dict.__name__, tuple.__name__):
            m = GRAY
        elif self._node_region == REGIONS[1]:
            m = GRAY
        elif self._node_region == REGIONS[5]:
            m = GRAY

        if self._node_region == REGIONS[1]:
            v = self.child_by_key(SCENE_PATH).raw_value()
        else:
            v = str(self._value)

        return m + v

    def display_name(self):
        m = ''
        if self._node_region == REGIONS[1]:
            m = ''
        elif self._node_region in (REGIONS[5], REGIONS[6]):
            m = GRAY
        elif self._node_region == REGIONS[0]:
            m = FONT_BOLD
        elif isinstance(self._key, int):
            m = GRAY

        if self._node_region == REGIONS[1]:
            k = basename(self.child_by_key(SCENE_PATH).raw_value())
        elif isinstance(self._key, int):
            k = str(self._key + 1)
        else:
            k = str(self._key)
            k = k.replace('_', ' ')
            k = k.title() if "." not in k else k

        return m + k

    def key(self):
        return str(self._key)

    def set_key(self, key):
        self._key = key

    def node_region(self):
        return str(self._node_region)

    def set_node_region(self, node_type):
        self._node_region = node_type
        return self._node_region

    def value_type(self):
        return self._value_type

    def set_value_type(self, value_type):
        self._value_type = value_type
        return self._value_type
    
    def selectable(self):
        return self._selectable
    
    def set_selectable(self, selectable=True):
        self._selectable = selectable

    def columns(self):
        return self._columns

    def child_by_key(self, key):
        for child in self._children:
            if key == child.key():
                return child
        return False

    def selected_children(self, recursive=True):
        sel = []
        for child in self._children:
            if child.is_selected():
                sel.append(child)
            if recursive:
                sel += child.selected_children()

        return sel

    def ancestors(self, path=None):
        if self._parent:
            return self._parent.ancestors() + [self]
        else:
            return path if path else []

    def ancestor_keys(self):
        return [ancestor.key() for ancestor in self.ancestors()[1:]]

    def parent(self):
        return self._parent

    def children(self):
        return self._children

    def insert_child(self, index, node):
        self._children.insert(index, node)

    def parent_index(self):
        return self.parent().children().index(self)

    def set_parent_index(self,index):
        self.destroy()
        self.parent().insert_child(index, self)

    def reorder_up(self):
        if self.parent_index() > 0:
            self.set_parent_index(self.parent_index()-1)

    def reorder_down(self):
        if self.parent_index() + 1 < len(
                [i for i in self.parent().children() if i.selectable()]
        ):
            self.set_parent_index(self.parent_index()+1)

    def reorder_top(self):
        self.set_parent_index(0)

    def reorder_bottom(self):
        self.set_parent_index(
            len([i for i in self.parent().children() if i.selectable()]) - 1
        )

    def update_child_keys(self):
        for key, child in enumerate(sorted(self.children(), key=lambda x: x.key())):
            child.set_key(key if isinstance(key, int) else child.key())

    def destroy(self):
        self.clear_selection()
        self.parent().children().remove(self)

    def tier(self):
        return len(self.ancestors())


class BatchManager:

    def __init__(self, batch_file_path=''):
        self._batch_file_path = batch_file_path
        self._tree = TreeNode(TREE_ROOT_TITLE, LIST)

        self.regrow_tree()

    def add_task(self, paths_list, batch_root_node=None):
        if not batch_root_node:
            batch_root_node = self._tree.children()[0]

        if not paths_list:
            return False

        paths_list = paths_list if isinstance(paths_list, list) else [paths_list]

        for path in paths_list:
            task = monkey.defaults.TASK_PARAMS
            task[SCENE_PATH] = path
            self.grow_node([task], batch_root_node, 1)

        if self._batch_file_path:
            self.save_to_file()
        else:
            self.save_temp_file()

        self.regrow_tree()

    def node_file_root(self, tree_node):
        return tree_node.ancestors()[0]

    def set_batch_file(self, file_path=None):
        self._batch_file_path = file_path

    def close_file(self):
        self._tree.clear_selection()
        self._batch_file_path = None
        self.regrow_tree()

    def save_to_file(self, file_path=None):
        if file_path:
            self._batch_file_path = file_path

        elif not self._batch_file_path:
            self._batch_file_path = monkey.io.yaml_save_dialog()

        return monkey.io.write_yaml(self.tree_to_object(), self._batch_file_path)

    def save_temp_file(self):
        file_path = monkey.util.path_alias(':'.join((KIT_ALIAS, QUICK_BATCH_PATH)))
        return self.save_to_file(file_path)

    @staticmethod
    def iterate_anything(obj):
        if isinstance(obj, (list, tuple)):
            return {k: v for k, v in enumerate(obj)}.iteritems()
        if isinstance(obj, dict):
            return obj.iteritems()

    def grow_node(self, branch, parent_node, depth=0):

        if depth == 0:      node_type = REGIONS[1]
        elif depth == 1:    node_type = REGIONS[2]
        elif depth == 2:    node_type = REGIONS[4]
        else:               node_type = REGIONS[6]

        if isinstance(branch, (list, tuple, dict)):
            for key, value in sorted(self.iterate_anything(branch)):

                value_type = type(value).__name__

                if isinstance(value, (list, tuple, dict)):
                    node = parent_node.add_child(key, value_type, node_type, value_type)
                    self.grow_node(value, node, depth + 1)

                else:
                    parent_node.add_child(key, value, node_type, value_type)

        parent_node.add_child(ADD_GENERIC, EMPTY, REGIONS[5], selectable=False)

    def regrow_tree(self):
        batch_file_path = self._batch_file_path if self._batch_file_path else NO_FILE_SELECTED

        self._tree.clear_selection()
        self._tree.clear_children()

        batch_root_node = self._tree.add_child(
            BATCHFILE,
            batch_file_path,
            REGIONS[0]
        )

        batch_root_node.add_state_flag(fTREE_VIEW_ITEM_EXPAND)

        if self._batch_file_path:
            batch = monkey.io.read_yaml(self._batch_file_path)
            self.grow_node(batch, batch_root_node)

        if len(batch_root_node.children()) == 0:
            batch_root_node.add_child(EMPTY_PROMPT, EMPTY, REGIONS[6], selectable=False)

        return self._tree

    def node_data(self, node):
        if node.value_type() in (list.__name__, tuple.__name__):
            data = []
            for child in node.children():
                child_value = self.node_data(child)
                if child_value is not None:
                    data.append(child_value)
            return data

        elif node.value_type() == dict.__name__:
            data = {}
            for child in node.children():
                child_value = self.node_data(child)
                if child_value is not None:
                    data[child.key()] = child_value
            return data

        else:
            if not node.value_type():
                return None

            from pydoc import locate
            _type = locate(node.value_type())

            if _type is None:
                return None

            return _type(node.raw_value())

    def tree_to_object(self):
        batch = []
        for child in self._tree.child_by_key(BATCHFILE).children():
            if child.value_type() is not None:
                batch.append(self.node_data(child))
        return batch

    def batch_file_path(self):
        return self._batch_file_path

    def tree(self):
        return self._tree


_BATCH = BatchManager()


class BatchTreeView(lxifc.TreeView,
                    lxifc.Tree,
                    lxifc.ListenerPort,
                    lxifc.Attributes
                    ):

    _listenerClients = {}

    def __init__(self, node=None, current_index=0):

        if node is None:
            node = _BATCH.tree()

        self.m_currentNode = node
        self.m_currentIndex = current_index

    @classmethod
    def addListenerClient(cls, listener):
        tree_listener_obj = lx.object.TreeListener(listener)
        cls._listenerClients[tree_listener_obj.__peekobj__()] = tree_listener_obj

    @classmethod
    def removeListenerClient(cls, listener):
        tree_listener_object = lx.object.TreeListener(listener)
        if tree_listener_object.__peekobj__() in cls._listenerClients:
            del cls._listenerClients[tree_listener_object.__peekobj__()]

    @classmethod
    def notify_NewShape(cls):
        for client in cls._listenerClients.values():
            if client.test():
                client.NewShape()

    @classmethod
    def notify_NewAttributes(cls):
        for client in cls._listenerClients.values():
            if client.test():
                client.NewAttributes()

    def lport_AddListener(self, obj):
        self.addListenerClient(obj)

    def lport_RemoveListener(self, obj):
        self.removeListenerClient(obj)

    def targetNode(self):
        return self.m_currentNode.children()[self.m_currentIndex]

    def tree_Spawn(self, mode):
        new_tree = BatchTreeView(self.m_currentNode, self.m_currentIndex)
        new_tree_obj = lx.object.Tree(new_tree)

        if mode == lx.symbol.iTREE_PARENT:
            new_tree_obj.ToParent()

        elif mode == lx.symbol.iTREE_CHILD:
            new_tree_obj.ToChild()

        elif mode == lx.symbol.iTREE_ROOT:
            new_tree_obj.ToRoot()

        return new_tree_obj

    def tree_ToParent(self):
        m_parent = self.m_currentNode.parent()

        if m_parent:
            self.m_currentIndex = m_parent.children().index(self.m_currentNode)
            self.m_currentNode = m_parent

    def tree_ToChild(self):
        self.m_currentNode = self.m_currentNode.children()[self.m_currentIndex]

    def tree_ToRoot(self):
        self.m_currentNode = _BATCH.tree()

    def tree_IsRoot(self):
        if self.m_currentNode == _BATCH.tree():
            return True
        else:
            return False

    def tree_ChildIsLeaf(self):
        if len(self.m_currentNode.children()) > 0:
            return False
        else:
            return True

    def tree_Count(self):
        return len(self.m_currentNode.children())

    def tree_Current(self):
        return self.m_currentIndex

    def tree_SetCurrent(self, index):
        self.m_currentIndex = index

    def tree_ItemState(self, guid):
        return self.targetNode().state()

    def tree_SetItemState(self, guid, state):
        self.targetNode().set_state(state)

    def treeview_ColumnCount(self):
        return len(_BATCH.tree().columns())

    def treeview_ColumnByIndex(self, columnIndex):
        return _BATCH.tree().columns()[columnIndex]

    def treeview_ToPrimary(self):
        if self.m_currentNode.primary():
            self.m_currentNode = self.m_currentNode.primary()
            self.tree_ToParent()
            return True
        return False

    def treeview_IsSelected(self):
        return self.targetNode().is_selected()

    def treeview_Select(self, mode):

        if mode == lx.symbol.iTREEVIEW_SELECT_PRIMARY:
            _BATCH.tree().clear_selection()

            if self.targetNode().selectable():
                self.targetNode().set_selected()
            else:
                self.targetNode().parent().set_selected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_ADD and self.targetNode().selectable():
            self.targetNode().set_selected()

        elif mode == lx.symbol.iTREEVIEW_SELECT_REMOVE:
            self.targetNode().set_selected(False)

        elif mode == lx.symbol.iTREEVIEW_SELECT_CLEAR:
            _BATCH.tree().clear_selection()

    def treeview_ToolTip(self, column_index):
        tooltip = self.targetNode().tooltip(column_index)
        if tooltip:
            return tooltip
        lx.notimpl()

    def treeview_IsInputRegion(self, column_index, regionID):
        if regionID == 0:
            return True
        if self.targetNode().node_region() == REGIONS[regionID]:
            return True

        return False

    def attr_Count(self):
        return len(_BATCH.tree().columns())

    def attr_GetString(self, index):
        if index == 0:
            return self.targetNode().display_name()

        elif self.targetNode().display_value():
            return self.targetNode().display_value()

        else:
            return EMPTY


class BatchOpen(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_open_dialog()
        if path:
            _BATCH.set_batch_file(path)
            _BATCH.regrow_tree()
            BatchTreeView.notify_NewShape()


class BatchClose(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        _BATCH.close_file()
        BatchTreeView.notify_NewShape()


class BatchAddTask(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        paths_list = monkey.io.lxo_open_dialog()
        if not isinstance(paths_list, list):
            paths_list = [paths_list]

        if paths_list:
            for path in paths_list:
                _BATCH.add_task(path)
            BatchTreeView.notify_NewShape()


class BatchDeleteSel(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        sel = _BATCH.tree().selected_children()
        _BATCH.tree().clear_selection()

        for node in sel:
            node.destroy()

        _BATCH.save_to_file()

        BatchTreeView.notify_NewShape()


class BatchReorderSel(lxu.command.BasicCommand):
    def __init__(self):
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add('mode', lx.symbol.sTYPE_STRING)
        self.basic_SetFlags(0, lx.symbol.fCMDARG_OPTIONAL)

    def basic_Execute(self, msg, flags):
        mode = self.dyna_String(0).lower() if self.dyna_IsSet(0) else REORDER_ARGS['TOP']

        if mode not in [v for k, v in REORDER_ARGS.iteritems()]:
            lx.out("Wow, no idea to do with \"{}\". Sorry.".format(mode))
            return lx.symbol.e_FAILED

        sel = _BATCH.tree().selected_children()

        for node in sel:
            if mode == REORDER_ARGS['TOP']:
                node.reorder_top()
            elif mode == REORDER_ARGS['BOTTOM']:
                node.reorder_bottom()
            elif mode == REORDER_ARGS['UP']:
                node.reorder_up()
            elif mode == REORDER_ARGS['DOWN']:
                node.reorder_down()

        _BATCH.save_to_file()
        BatchTreeView.notify_NewShape()

        # Unsure why we lose selection, but we do. Have to re-select.
        _BATCH.tree().clear_selection()
        for node in sel:
            node.set_selected()


class BatchRender(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH.batch_file_path():
            return monkey.batch.run(_BATCH.batch_file_path())


class BatchExample(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            lx.eval('{} {{{}}}'.format(CMD_BatchExportTemplate, path))
            _BATCH.set_batch_file(path)
            _BATCH.regrow_tree()
            BatchTreeView.notify_NewShape()


class BatchOpenInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH.batch_file_path():
            lx.eval('file.open {{{}}}'.format(_BATCH.batch_file_path()))


class BatchRevealInFilesystem(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        if _BATCH.batch_file_path():
            lx.eval('file.revealInFileViewer {{{}}}'.format(_BATCH.batch_file_path()))


class BatchNew(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            monkey.io.write_yaml([], path)

            _BATCH.set_batch_file(path)
            _BATCH.regrow_tree()
            BatchTreeView.notify_NewShape()


class BatchSaveAs(lxu.command.BasicCommand):
    def basic_Execute(self, msg, flags):
        path = monkey.io.yaml_save_dialog()
        if path:
            _BATCH.save_to_file(path)
            BatchTreeView.notify_NewShape()


sTREEVIEW_TYPE = " ".join((VPTYPE, IDENT, sSRV_USERNAME, NICE_NAME))

sINMAP = "name[{}] regions[{}]".format(
    sSRV_USERNAME, " ".join(
        ['{}@{}'.format(n, i) for n, i in enumerate(REGIONS)]
    )
)

tags = {lx.symbol.sSRV_USERNAME: sSRV_USERNAME,
        lx.symbol.sTREEVIEW_TYPE: sTREEVIEW_TYPE,
        lx.symbol.sINMAP_DEFINE: sINMAP}

lx.bless(BatchTreeView, SERVERNAME, tags)

lx.bless(BatchOpen, CMD_BatchOpen)
lx.bless(BatchClose, CMD_BatchClose)
lx.bless(BatchAddTask, CMD_BatchAddTask)
lx.bless(BatchDeleteSel, CMD_BatchDeleteSel)
lx.bless(BatchReorderSel, CMD_BatchReorderSel)
lx.bless(BatchRender, CMD_BatchRender)
lx.bless(BatchExample, CMD_BatchExample)
lx.bless(BatchOpenInFilesystem, CMD_BatchOpenInFilesystem)
lx.bless(BatchRevealInFilesystem, CMD_BatchRevealInFilesystem)
lx.bless(BatchNew, CMD_BatchNew)
lx.bless(BatchSaveAs, CMD_BatchSaveAs)

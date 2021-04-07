class Context(object):
    """
    CONTEXT 上下文
    """
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        """

        :param display_name:
        :param parent:
        :param parent_entry_pos:
        """
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None # 符号表
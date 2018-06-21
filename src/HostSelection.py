# pylint: disable=bad-whitespace,bad-continuation,invalid-name,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines

"""OSMDB’s Node Selection Object"""

from Selection import Selection

class NodeSelection(Selection):
    """The NodeSelection object is a node list constructed from a query string.
       Those node selections instances are cached in the database and rebuilt on configuration reload."""

    def __init__(self, name, query, db):
        
        super().__init__(name, query, db)
        self.selectNode(query)
        
    def selectNode(self, query):
        """Select some nodes according to query string."""
        
        self.nodes = self.select(query, self.db.getNodeSelection, self.db.getNodes, self.db.isNodeTag, self.db.addNodeSelection)
        return self.nodes


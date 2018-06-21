# pylint: disable=bad-whitespace,bad-continuation,invalid-name,line-too-long,multiple-statements,trailing-whitespace,trailing-newlines

"""OSMDB’s Selection Object."""

from re import sub as re_sub

def query2parts(query):

    return  re_sub(r'\s+',' ',query).replace('! ','!').split('|')

class Selection:
    """The Selection object is a object list constructed from a query string.
       Those object selection instances are cached in the database and rebuilt on configuration reload."""

    def __init__(self, name, query, db):
        
        self.name    = name
        self.query   = query
        self.db      = db
        self.objects = []

    def select(self, query, getObjectSelection, getObjects, isObjectTag, addObjectSelection):
        """Select some object according to query string."""
        
        if not query: return []
        
        current_objects = getObjectSelection(query)
        if current_objects: return current_objects.split()
        
        for obj in getObjects():
            keep = False
            for part in query2parts(query):

                tokens = part.split('&')
                for token in tokens:

                    if token[0:2] == '!%' and isObjectTag(obj[0], token[2:]):
                        keep = False
                        break
                        
                    elif token[0:2] == '!%' and not isObjectTag(obj[0], token[2:]):
                        keep = True
                        continue
                        
                    elif token[0] == '!'  and obj[0] == token[1:]:
                        keep = False
                        break
                        
                    elif token[0] == '!'  and obj[0] != token[1:]:
                        keep = True
                        continue
                        
                    elif token[0] == '%'  and isObjectTag(obj[0], token[1:]):
                        keep = True
                        continue
                        
                    elif token == obj[0]:
                        keep = True
                        continue
                        
                    else:
                        keep = False
                        break
               
                if keep: self.objects.append(obj[0])

        addObjectSelection(self.name, query, ' '.join(self.objects))
        return self.objects

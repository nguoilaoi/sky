try: 
    from .helper import normalize
    from .helper import get_text_and_tail
except SystemError: 
    from helper import normalize
    from helper import get_text_and_tail

class DomainNodesDict(dict):
    def __init__(self, domain, min_templates = 2, max_templates = 24, template_proportion = 0.7):
        super(DomainNodesDict, self).__init__()
        self.num_urls = 0 
        self.domain = domain
        self.min_templates = min_templates
        self.max_templates = max_templates
        self.template_proportion = template_proportion
        self.untemplated = []

    def get_fingerprints(self, node):
        res = []
        text = normalize(get_text_and_tail(node)).strip() 
        if text: 
            res = [(node.tag, a, node.attrib[a], text) for a in node.attrib] 
            if node.tag == 'a':
                res += [(node.tag, '', '', text)]
            if not res:
                res = [(node.tag, '', '', text)]
        return res

    def add_fp(self, fp, seen):
        if fp not in seen:    
            if fp not in self:
                self[fp] = 0 
            self[fp] += 1
            seen.add(fp)
            
    def add_template_elements(self, tree):
        if self.num_urls < self.max_templates:
            seen = set()
            for node in tree.iter():
                if node.tag == 'meta' and 'property' in node.attrib and 'image' in node.attrib['property'] and 'content' in node.attrib:
                    self.add_fp((node.attrib['property'], node.attrib['content']), seen) 
                elif node.tag in ['img', 'iframe'] and 'src' in node.attrib:
                    self.add_fp((node.tag, node.attrib['src']), seen)
                else:                        
                    for fp in self.get_fingerprints(node):
                        self.add_fp(fp, seen)
            self.num_urls += 1

    def remove_template(self, tree):
        if self.num_urls < self.min_templates:
            return False
        for node in tree.iter():
            if node.tag == 'meta': 
                if 'property' in node.attrib and 'content' in node.attrib: 
                    fp = (node.attrib['property'], node.attrib['content'])
                    if fp in self and self[fp] / self.num_urls > self.template_proportion: 
                        node.set('content', '') 
            elif node.tag in ['img', 'iframe'] and 'src' in node.attrib:
                fp = (node.tag, node.attrib['src'])
                if fp in self and self[fp] / self.num_urls > self.template_proportion: 
                    node.set('src', '')
                    node.set('alt', '')
            else:    
                for fp in self.get_fingerprints(node):
                    if fp in self and self[fp] / self.num_urls > self.template_proportion: 
                        node.text = ''
                        node.tail = ''
        return True 
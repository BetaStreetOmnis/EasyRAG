



class StructureAwareChunker:
    """结构感知分块器，保留文档的层级结构信息进行分块"""
    
    def __init__(self, min_chunk_size=200, max_chunk_size=1000):
        """
        初始化结构感知分块器
        
        参数:
            min_chunk_size (int): 最小块大小（字符数）
            max_chunk_size (int): 最大块大小（字符数）
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
    def chunk_document(self, document):
        """
        保留结构信息的文档分块
        
        参数:
            document (str或dict): 要分块的文档内容
            
        返回:
            List[Dict]: 带有结构信息的文档块列表
        """
        # 1. 解析文档结构
        doc_structure = self._parse_document_structure(document)
        
        # 2. 生成带结构上下文的分块
        structured_chunks = []
        
        for section in doc_structure:
            # 处理每个章节及其子章节
            section_chunks = self._process_section(section)
            structured_chunks.extend(section_chunks)
            
        return structured_chunks
    
    def _parse_document_structure(self, document):
        """
        解析文档的层级结构
        
        参数:
            document (str或dict): 文档内容
            
        返回:
            List[Dict]: 文档结构的层级表示
        """
        # 识别标题、段落、列表等结构元素
        structure = []
        
        if isinstance(document, str):
            # 文本文档解析逻辑
            lines = document.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检测标题（例如：# 标题，## 子标题等）
                header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
                if header_match:
                    level = len(header_match.group(1))
                    title = header_match.group(2)
                    
                    new_section = {
                        'id': f"section_{len(structure)}",
                        'type': 'section',
                        'level': level,
                        'title': title,
                        'number': str(len(structure) + 1),
                        'content': '',
                        'subsections': [],
                        'parent': None
                    }
                    
                    # 处理层级关系
                    if current_section is None:
                        structure.append(new_section)
                    else:
                        if level > current_section.get('level', 1):
                            new_section['parent'] = current_section
                            current_section['subsections'].append(new_section)
                        else:
                            structure.append(new_section)
                    
                    current_section = new_section
                else:
                    # 普通段落内容
                    if current_section:
                        current_section['content'] += line + '\n'
                    else:
                        # 没有标题的内容，创建默认章节
                        default_section = {
                            'id': 'default_section',
                            'type': 'section',
                            'level': 1,
                            'title': '文档内容',
                            'number': '1',
                            'content': line + '\n',
                            'subsections': [],
                            'parent': None
                        }
                        structure.append(default_section)
                        current_section = default_section
        else:
            # 结构化文档（如JSON、XML等）的解析逻辑
            # 这里需要根据具体的文档格式进行定制
            pass
            
        return structure
    
    def _process_section(self, section):
        """
        处理单个章节，保留结构上下文
        
        参数:
            section (Dict): 章节信息
            
        返回:
            List[Dict]: 该章节的结构化块列表
        """
        section_chunks = []
        
        # 获取结构路径
        path = self._get_structure_path(section)
        
        # 分块处理文本内容
        content_chunks = self._chunk_text(section['content'])
        
        for i, chunk in enumerate(content_chunks):
            # 为每个块添加结构路径作为前缀或元数据
            structured_chunk = {
                'text': chunk,
                'structure_path': path,  # 存储结构路径
                'structure_context': self._format_structure_context(path),  # 格式化的上下文
                'is_first_chunk': i == 0,
                'is_last_chunk': i == len(content_chunks) - 1,
                'section_id': section['id']
            }
            section_chunks.append(structured_chunk)
            
        # 递归处理子章节
        for subsection in section.get('subsections', []):
            subsection_chunks = self._process_section(subsection)
            section_chunks.extend(subsection_chunks)
            
        return section_chunks
    
    def _chunk_text(self, text):
        """
        将文本内容分割成适当大小的块
        
        参数:
            text (str): 要分块的文本
            
        返回:
            List[str]: 分块后的文本列表
        """
        chunks = []
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # 如果当前块加上新段落超过最大块大小，保存当前块并开始新块
            if len(current_chunk) + len(para) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果段落本身超过最大块大小，进一步分割
                if len(para) > self.max_chunk_size:
                    # 按句子分割
                    sentences = re.split(r'(?<=[。！？.!?])', para)
                    temp_chunk = ""
                    
                    for sentence in sentences:
                        if not sentence.strip():
                            continue
                            
                        if len(temp_chunk) + len(sentence) > self.max_chunk_size:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = sentence
                        else:
                            temp_chunk += sentence
                    
                    if temp_chunk:
                        current_chunk = temp_chunk
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    
        # 添加最后一个块
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)
            
        return chunks
    
    def _get_structure_path(self, section):
        """
        获取章节的完整结构路径
        
        参数:
            section (Dict): 章节信息
            
        返回:
            List[Dict]: 从根到当前章节的路径
        """
        path = []
        current = section
        while current:
            path_component = {
                'type': current.get('type', 'section'),  # section, list_item, etc.
                'number': current.get('number'),         # 1, 2, (1), etc.
                'title': current.get('title', '')        # 章节标题
            }
            path.insert(0, path_component)
            current = current.get('parent')
        return path
    
    def _format_structure_context(self, path):
        """
        格式化结构上下文为可读文本
        
        参数:
            path (List[Dict]): 结构路径
            
        返回:
            str: 格式化后的结构上下文
        """
        context = []
        for item in path:
            if item['type'] == 'section' and item['title']:
                context.append(f"{item['number'] or ''} {item['title']}")
            elif item['type'] == 'list_item':
                context.append(f"{item['number'] or ''}")
        return " > ".join(context)



# if __name__ == "__main__":
#     # 测试结构感知分块器
#     document = """
    
#     """
#     chunker = StructureAwareChunker()
#     chunks = chunker.chunk_document(document)

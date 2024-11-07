def markdown_to_slack_blocks(markdown_text):
    """
    Convert markdown text to Slack block format.
    Handles basic markdown elements, dividers, and respects Slack's 3000 character limit per block.
    
    Args:
        markdown_text (str): Input markdown text
        
    Returns:
        list: Array of Slack block objects
    """
    import re
    
    SLACK_TEXT_LIMIT = 740
    blocks = []
    current_section = []
    
    def chunk_text(text, limit=SLACK_TEXT_LIMIT):
        """Split text into chunks that respect Slack's character limit."""
        if len(text) <= limit:
            return [text]
            
        chunks = []
        current_chunk = ""
        
        # Split by sentences to maintain context
        sentences = re.split(r'([.!?]+\s+)', text)
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= limit:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def process_inline_formatting(text):
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
        text = re.sub(r'__(.*?)__', r'*\1*', text)
        
        # Italic
        text = re.sub(r'\*(.*?)\*', r'_\1_', text)
        text = re.sub(r'_(.*?)_', r'_\1_', text)
        
        # Code
        text = re.sub(r'`(.*?)`', r'`\1`', text)
        
        return text
    
    def add_text_block(text, type="plain_text"):
        """Add text block(s) respecting character limit."""
        if not text.strip():
            return
            
        # Split text into chunks if it exceeds the limit
        text_chunks = chunk_text(text.strip())
        
        for chunk in text_chunks:
            blocks.append({
                "type": "section",
                "text": {
                    "type": type,
                    "text": chunk
                }
            })
    
    list_in_progress = False
    code_block = False
    code_content = []
    
    lines = markdown_text.strip().split('\n')
    
    for line in lines:
        # Handle horizontal rules (dividers)
        if re.match(r'^\s*([*-_])\s*(?:\1\s*){2,}\s*$', line):
            # Add any pending list items before the divider
            if list_in_progress and current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": '\n'.join(current_section),
                        "verbatim": True  # Prevent "See more" button
                    }
                })
                current_section = []
                list_in_progress = False
            
            blocks.append({"type": "divider"})
            continue
            
        # Handle code blocks
        if line.startswith('```'):
            if code_block:
                # End code block
                if code_content:
                    code_text = ' '.join(code_content)
                    # Split code blocks if they exceed limit
                    for chunk in chunk_text(code_text):
                        blocks.append({
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"```{chunk}```"
                            }
                        })
                code_content = []
                code_block = False
            else:
                code_block = True
            continue
            
        if code_block:
            code_content.append(line)
            continue
            
        # Headers
        if line.startswith('#'):
            header_level = len(re.match(r'^#+', line).group())
            header_text = line[header_level:].strip()
            # Headers don't need chunking as they're typically short
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text[:3000]  # Safeguard for header length
                }
            })
            continue
            
        # Lists
        if re.match(r'^\s*[\-\*\+]\s', line) or re.match(r'^\s*\d+\.\s', line):
            if not list_in_progress:
                list_in_progress = True
                current_section = []
            
            list_item = re.sub(r'^\s*[\-\*\+]\s', '• ', line)
            list_item = re.sub(r'^\s*\d+\.\s', '• ', list_item)
            current_section.append(process_inline_formatting(list_item))
            
            # Check if current list exceeds limit
            if len('\n'.join(current_section)) > SLACK_TEXT_LIMIT:
                # Add current list except last item
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": '\n'.join(current_section[:-1])
                    }
                })
                # Start new list with last item
                current_section = [current_section[-1]]
            continue
            
        # If we were in a list and now we're not, add the list block
        if list_in_progress and not (re.match(r'^\s*[\-\*\+]\s', line) or re.match(r'^\s*\d+\.\s', line)):
            if current_section:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": '\n'.join(current_section)
                    }
                })
            current_section = []
            list_in_progress = False
            
        # Regular paragraph text
        if line.strip() and not list_in_progress:
            add_text_block(process_inline_formatting(line), "mrkdwn")
            
    # Add any remaining list items
    if current_section:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": '\n'.join(current_section)
            }
        })
        
    # Ensure all text blocks have at least 1 character
    for block in blocks:
        if block["type"] == "section" and not block["text"]["text"].strip():
            block["text"]["text"] = " "
            
    return blocks

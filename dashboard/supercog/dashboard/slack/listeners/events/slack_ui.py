import re

def inline_markdown_to_rich_text(line: str):
    # Define inline formatting patterns with capturing groups
    patterns = [
        (r'\*\*\*(.+?)\*\*\*', {"bold": True, "italic": True}), # Bold & Italic
        (r'\_\_\_(.+?)\_\_\_', {"bold": True, "italic": True}), # Bold & Italic
        (r'\_\_\*(.+?)\*\_\_', {"bold": True, "italic": True}), # Bold & Italic
        (r'\*\*\_(.+?)\_\*\*', {"bold": True, "italic": True}), # Bold & Italic
        (r'\*\*(.+?)\*\*', {"bold": True}),                     # Bold
        (r'\_\_(.+?)\_\_', {"bold": True}),                     # Bold
        (r'\*(.+?)\*', {"italic": True}),                       # Italic
        (r'\_(.+?)\_', {"italic": True}),                       # Italic
        (r'\`(.+?)\`', {"code": True}),                         # Inline code
        (r'\~(.+?)\~', {"strike": True}),                       # Strikethrough
        (r'\!?\[(.+?)\]\((.+?)\)', {"link": True})                 # Links
    ]
    
    # Combine all patterns into one unified regex to capture all inline formats
    combined_pattern = '|'.join([f"(?:{pattern})" for pattern, _ in patterns])

    # This pattern will also capture the non-formatted text
    token_pattern = re.compile(rf"({combined_pattern}|[^\*\_\`~\[\]]+)")

    # Match all tokens (either formatted text or plain text)
    tokens = token_pattern.findall(line)
    
    elements = []
    for token in tokens:
        matched = False
        # Check each token for a match with the inline formatting patterns
        for idx, (pattern, style) in enumerate(patterns):
            matched_text = token[idx + 1]  # Capture group for the matched text
            if matched_text:
                matched = True
                if style == {"link": True}:  # Handle links specially
                    link_text = token[idx + 1]
                    link_url = token[idx + 2]
                    elements.append({
                        "type": "link",
                        "text": link_text,
                        "url": link_url
                    })
                else:
                    # For other inline formats (bold, italic, etc.)
                    elements.append({
                        "type": "text",
                        "text": matched_text,
                        "style": style
                    })
                break
        
        if not matched:
            # If it's not a match (plain text), add it as normal text
            elements.append({
                "type": "text",
                "text": token[0]  # Token is plain text (no format)
            })

    return elements

def markdown_to_slack_rich_text(markdown_text: str):
    """
    Convert Markdown text to Slack rich text format.
    
    Parameters:
    markdown_text (str): The Markdown text to be converted.
    
    Returns:
    list: A list of Slack rich text block objects.
    """
    slack_blocks = []
    
    # Split the Markdown text into lines
    lines = markdown_text.split('\n')
    
    # Keep track of code block state
    in_code_block = False
    
    # Iterate through the lines and convert to Slack blocks
    for line in lines:
        # Check for code blocks
        if line.startswith('```'):
            if not in_code_block:
                # Start of a code block
                in_code_block = True
                slack_blocks.append({
                    "type": "rich_text",
                    "elements": [
                        {
                            "type": "rich_text_preformatted",
                            "elements": []
                        }
                    ]
                })
            else:
                # End of a code block
                in_code_block = False
        # If in a code block, add the line as-is
        elif in_code_block:
            slack_blocks[-1]["elements"][0]["elements"].append({
                "type": "text",
                "text": f"{line}\n",
            })
        # Check for headers
        elif line.startswith('#'):
            level = line.count('#')
            text = line[level:].strip()
            if text:
                slack_blocks.append({
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": text,
                        "emoji": True
                    }
                })
        # Check for dividers
        elif line.strip() == '---':
            slack_blocks.append({
                "type": "divider"
            })
        # Check for unordered lists (start with `-` or `*`)
        elif line.lstrip().startswith(('- ', '* ')):
            # Add unordered list item
            list_item = line.lstrip()[1:].strip()  # Remove leading `-` or `*`
            elements = inline_markdown_to_rich_text(list_item)
            if len(slack_blocks) > 0 and slack_blocks[-1].get("type") == "rich_text":
                # Check if there is an existing list, if there is add to it
                if len(slack_blocks[-1]["elements"]) > 0 and slack_blocks[-1]["elements"][-1].get("type") == "rich_text_list" and slack_blocks[-1]["elements"][-1].get("style") == "bullet":
                    slack_blocks[-1]["elements"][-1]["elements"].append({
                        "type": "rich_text_section",
                        "elements": elements
                    })
                else:
                    slack_blocks[-1]["elements"].append({
                        "type": "rich_text_list",
                        "style": "bullet",
                        "elements": [{
                            "type": "rich_text_section",
                            "elements": elements
                        }]
                    })
            else:
                slack_blocks.append({
                    "type": "rich_text",
                    "elements": [{
                        "type": "rich_text_list",
                        "style": "bullet",
                        "elements": [{
                            "type": "rich_text_section",
                            "elements": elements
                        }]
                    }]
                })
        # Check for ordered lists (lines starting with a number followed by a dot)
        elif re.match(r'^\d+\. ', line.lstrip()):
            # Add ordered list item
            list_item = line.lstrip().split(' ', 1)[1].strip()
            elements = inline_markdown_to_rich_text(list_item)
            if len(slack_blocks) > 0 and slack_blocks[-1].get("type") == "rich_text":
                # Check if there is an existing list, if there is add to it
                if len(slack_blocks[-1]["elements"]) > 0 and slack_blocks[-1]["elements"][-1].get("type") == "rich_text_list" and slack_blocks[-1]["elements"][-1].get("style") == "ordered":
                    slack_blocks[-1]["elements"][-1]["elements"].append({
                        "type": "rich_text_section",
                        "elements": elements
                    })
                else:
                    slack_blocks[-1]["elements"].append({
                        "type": "rich_text_list",
                        "style": "ordered",
                        "elements": [{
                            "type": "rich_text_section",
                            "elements": elements
                        }]
                    })
            else:
                slack_blocks.append({
                    "type": "rich_text",
                    "elements": [{
                        "type": "rich_text_list",
                        "style": "ordered",
                        "elements": [{
                            "type": "rich_text_section",
                            "elements": elements
                        }]
                    }]
                })
        # Check for blockquotes (lines starting with `>`)
        elif line.lstrip().startswith('> '):
            # Add blockquote
            quote_text = line.lstrip()[1:].strip()
            elements = inline_markdown_to_rich_text(quote_text)
            # Add a \n to the last element's text
            if len(elements) > 0:
                elements[-1]["text"] += "\n"
            if len(slack_blocks) > 0 and slack_blocks[-1].get("type") == "rich_text":
                # Check if there is an existing block quote, if there is add to it
                if len(slack_blocks[-1]["elements"]) > 0 and slack_blocks[-1]["elements"][-1].get("type") == "rich_text_quote":
                    slack_blocks[-1]["elements"][-1]["elements"].extend(elements)
                else:
                    slack_blocks[-1]["elements"].append({
                        "type": "rich_text_quote",
                        "elements": elements
                    })
            else:
                slack_blocks.append({
                    "type": "rich_text",
                    "elements": [{
                        "type": "rich_text_quote",
                        "elements": elements
                    }]
                })
        # All other lines are treated as rich text
        else:
            # Check if the last block is rich text, if not create a new one
            previous_block_is_rich_text = len(slack_blocks) > 0 and slack_blocks[-1].get("type") == "rich_text"

            if not previous_block_is_rich_text:
                slack_blocks.append({
                    "type": "rich_text",
                    "elements": []
                })

            elements = inline_markdown_to_rich_text(line)

            # Add the constructed elements to the Slack block
            if elements:
                slack_blocks[-1]["elements"].append({
                    "type": "rich_text_section",
                    "elements": elements,
                })
    
    return slack_blocks

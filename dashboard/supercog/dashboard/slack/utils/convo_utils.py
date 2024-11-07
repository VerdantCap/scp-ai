from logging import Logger
from typing import Dict, Optional, NamedTuple
import re
from urllib.parse import urlparse

import requests
from slack_sdk.web.async_client import AsyncWebClient

from supercog.shared.services import config

S3_FILES_BUCKET_NAME = config.get_global("S3_FILES_BUCKET_NAME", required=False)
S3_PUBLIC_BUCKET = config.get_global("S3_PUBLIC_BUCKET", required=False)


class ChannelInfo(NamedTuple):
    channel_id: str
    channel_name: Optional[str]
    is_public: Optional[bool]
    team_id: Optional[str]

class SlackUploadedFile:
    def __init__(self, filename: str, slack_link: str):
        self.filename = filename
        self.slack_link = slack_link

def get_channel_info(payload: dict, team_id: str) -> ChannelInfo:
    """ Extract channel information from a Slack event callback. """
    channel_id = None
    channel_name = None
    is_public = None

    # First try to get channel info from the event directly
    if 'channel' in payload:
        if isinstance(payload['channel'], dict):
            # Some events provide detailed channel info
            channel_id = payload['channel'].get('id')
            channel_name = payload['channel'].get('name')
            # Check channel type - public channels start with 'C'
            if channel_id:
                is_public = channel_id.startswith('C')
        else:
            # Some events just provide channel ID as string
            channel_id = payload['channel']
            is_public = channel_id.startswith('C')
    
    # If not in main event, check item field (used in some event types)
    elif 'item' in payload and isinstance(payload['item'], dict):
        channel_id = payload['item'].get('channel')
        if channel_id:
            is_public = channel_id.startswith('C')
    
    # For conversation_rename events
    if payload.get('type') == 'channel_rename':
        channel_name = payload.get('name')
    
    return ChannelInfo(channel_id or "unknown", channel_name, is_public, team_id=team_id)

async def upload_files_to_slack(
        client: AsyncWebClient,
        logger: Logger,
        uploaded_files: list[SlackUploadedFile],
        markdown_content: str,
        channel_id: str,
        thread_ts: str,
    ) -> str:
    matches: list[tuple[str, str]] = re.findall(fr"<(https?:\/\/(?:{S3_FILES_BUCKET_NAME}|{S3_PUBLIC_BUCKET})[^|]+)\|([^>]+)>", markdown_content) or []

    for url, text in matches:
        filename = urlparse(url).path.split("/")[-1]

        # Find if the file has already been uploaded
        uploaded_file = None
        for file in uploaded_files:
            if file.filename == filename:
                uploaded_file = file

        # If the file has been uploaded, just replace the link
        if uploaded_file:
            return markdown_content.replace(f"<{url}|{text}>", f"<{uploaded_file.slack_link}|{text}>")

        if filename not in map(lambda file: file.filename, uploaded_files):
            try:
                file_download_response = requests.get(url)
                if file_download_response.ok:
                    file_upload_response = await client.files_upload_v2(
                        channel=channel_id,
                        thread_ts=thread_ts,
                        content=file_download_response.content,
                        title=filename,
                        filename=filename
                    )
                    # Replace the link with the text and a message saying "attached below"
                    if file_upload_response["ok"]:
                        file_slack_link = file_upload_response.get("file", {}).get("permalink", "")
                        # Mark the file as upload to prevent duplicates
                        uploaded_files.append(SlackUploadedFile(filename, file_slack_link))
                        return markdown_content.replace(f"<{url}|{text}>", f"<{file_slack_link}|{text}>")
                    else:
                        logger.error("[Slack] Unable to upload file to Slack")
                else:
                    logger.error("[Slack] Unable to download file from s3 to upload to Slack")
            except Exception as e:
                logger.error(f"[Slack] Unable to upload file to Slack: {e}")
                return markdown_content
    
    return markdown_content

msg_accessory = {
    "accessory": {
        "type": "overflow",
        "options": [
            {
                "text": {
                    "type": "plain_text",
                    "text": "show details",
                    "emoji": True
                },
                "value": "value-0"
            },
            {
                "text": {
                    "type": "plain_text",
                    "text": "save prompt",
                    "emoji": True
                },
                "value": "value-1"
            },
        ],
        "action_id": "overflow-action"
    }
}


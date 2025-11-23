# server/core/document_utils.py

import os
def get_content_type_from_extension(filename):
	"""get appropriate content type from file extension"""
	if not filename:
		return 'application/octet-stream'

	ext = os.path.splitext(filename)[1].lower()

	content_type_map = {
		'.pdf': 'application/pdf',
		'.txt': 'text/plain',
		'.rtf': 'text/rtf',
		'.jpg': 'image/jpeg',
		'.jpeg': 'image/jpeg',
		'.png': 'image/png',
		'.gif': 'image/gif',
		'.bmp': 'image/bmp',
		'.tiff': 'image/tiff',
		'.tif': 'image/tiff',
		'.doc': 'application/msword',
		'.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
		'.docs': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
	}

	return content_type_map.get(ext, 'application/octet-stream')
# Central registry for all tools
# Format: slug -> metadata

TOOLS = {
    'json-formatter': {
        'name': 'JSON Formatter',
        'template': 'json_formatter',
        'title': 'JSON Formatter & Validator',
        'description': 'Online tool to validate, format, and beautify JSON data. 100% private, client-side processing.',
        'icon': 'fa-code',
        'category': 'Programming',
        'color': 'blue'
    },
    'regex-tester': {
        'name': 'Regex Tester',
        'template': 'regex_tester',
        'title': 'Regex Tester & Debugger',
        'description': 'Test and debug regular expressions in real-time with highlighted matches.',
        'icon': 'fa-asterisk',
        'category': 'Programming',
        'color': 'green'
    },
    'base64': {
        'name': 'Base64 Converter',
        'template': 'base64_converter',
        'title': 'Base64 Encoder/Decoder',
        'description': 'Fast and secure Base64 conversion for text and binary data.',
        'icon': 'fa-exchange-alt',
        'category': 'Programming',
        'color': 'purple'
    },
    'diff': {
        'name': 'Diff Viewer',
        'template': 'diff_viewer',
        'title': 'Text Diff Checker',
        'description': 'Compare two text snippets side-by-side and visualize differences.',
        'icon': 'fa-columns',
        'category': 'Programming',
        'color': 'rose'
    },
    'url-encoder': {
        'name': 'URL Encoder',
        'template': 'url_encoder',
        'title': 'URL Encoder & Decoder',
        'description': 'Safely encode and decode URLs and parameters.',
        'icon': 'fa-link',
        'category': 'Programming',
        'color': 'cyan'
    },
    'timestamp': {
        'name': 'Unix Timestamp',
        'template': 'timestamp_converter',
        'title': 'Unix Timestamp Converter',
        'description': 'Convert Unix epoch timestamps to human-readable dates and vice-versa.',
        'icon': 'fa-clock',
        'category': 'Data & Research',
        'color': 'gray'
    },
    'hash-gen': {
        'name': 'Hash Generator',
        'template': 'hash_generator',
        'title': 'Hash Generator',
        'description': 'Generate MD5, SHA-1, SHA-256, and SHA-512 hashes locally.',
        'icon': 'fa-fingerprint',
        'category': 'Security & Systems',
        'color': 'red'
    },
    'uuid-gen': {
        'name': 'UUID Generator',
        'template': 'uuid_generator',
        'title': 'UUID Generator',
        'description': 'Bulk generate unique UUID v4 identifiers for your projects.',
        'icon': 'fa-id-badge',
        'category': 'Security & Systems',
        'color': 'slate'
    },
    'sql-refinery': {
        'name': 'SQL Refinery',
        'template': 'sql_refinery',
        'title': 'Professional SQL Formatter',
        'description': 'Format and beautify SQL queries and database dumps.',
        'icon': 'fa-database',
        'category': 'Programming',
        'color': 'indigo'
    },
    'sql-workbench': {
        'name': 'SQL Workbench',
        'template': 'sql_workbench',
        'title': 'Universal SQL Client',
        'description': 'Run SQL queries against local datasets using AlaSQL emulation.',
        'icon': 'fa-server',
        'category': 'Programming',
        'color': 'indigo'
    },
    'cron-gen': {
        'name': 'Cron Generator',
        'template': 'cron_generator',
        'title': 'Cron Schedule Generator',
        'description': 'Easily generate and validate cron expressions.',
        'icon': 'fa-calendar-alt',
        'category': 'Security & Systems',
        'color': 'sky'
    },
    'jwt-parser': {
        'name': 'JWT Parser',
        'template': 'jwt_parser',
        'title': 'JWT Decoder & Inspector',
        'description': 'Decode and inspect JSON Web Token payloads and headers.',
        'icon': 'fa-id-card',
        'category': 'Programming',
        'color': 'pink'
    },
    'latex-editor': {
        'name': 'LaTeX Editor',
        'template': 'latex_editor',
        'title': 'Live LaTeX Math Editor',
        'description': 'Write and preview LaTeX math equations in real-time.',
        'icon': 'fa-square-root-alt',
        'category': 'Data & Research',
        'color': 'neutral'
    },
    'csv-json': {
        'name': 'CSV ⇄ JSON',
        'template': 'json_csv_converter',
        'title': 'CSV & JSON Converter',
        'description': 'Bidirectional conversion between CSV and JSON formats.',
        'icon': 'fa-file-csv',
        'category': 'Data & Research',
        'color': 'emerald'
    },
    'image-to-base64': {
        'name': 'Image to Base64',
        'template': 'image_to_base64',
        'title': 'Image to Base64 Converter',
        'description': 'Convert images to base64 strings for use in CSS/HTML.',
        'icon': 'fa-image',
        'category': 'Programming',
        'color': 'rose'
    },
    'yaml-json': {
        'name': 'YAML ⇄ JSON',
        'template': 'yaml_json_converter',
        'title': 'YAML & JSON Converter',
        'description': 'Convert between YAML and JSON seamlessly.',
        'icon': 'fa-file-code',
        'category': 'Programming',
        'color': 'orange'
    },
    'markdown-preview': {
        'name': 'Markdown Preview',
        'template': 'markdown_previewer',
        'title': 'GFM Markdown Editor',
        'description': 'Live GitHub Flavored Markdown editor and previewer.',
        'icon': 'fa-file-alt',
        'category': 'Programming',
        'color': 'blue'
    },
    'html-entities': {
        'name': 'HTML Entities',
        'template': 'html_entities',
        'title': 'HTML Entity Encoder',
        'description': 'Encode and decode HTML entities securely.',
        'icon': 'fa-code',
        'category': 'Programming',
        'color': 'cyan'
    },
    'api-tester': {
        'name': 'API Tester (Lite)',
        'template': 'api_tester',
        'title': 'Browser API Tester',
        'description': 'Test HTTP endpoints directly from your browser.',
        'icon': 'fa-plug',
        'category': 'Security & Systems',
        'color': 'teal'
    },
    'data-profiler': {
        'name': 'Data Profiler',
        'template': 'data_profiler',
        'title': 'Statistical Data Profiler',
        'description': 'Generate statistical summaries and insights from datasets.',
        'icon': 'fa-chart-pie',
        'category': 'Data & Research',
        'color': 'rose'
    },
    'json-schema': {
        'name': 'JSON Schema',
        'template': 'json_schema_validator',
        'title': 'JSON Schema Validator',
        'description': 'Validate JSON data against schema standards.',
        'icon': 'fa-project-diagram',
        'category': 'Data & Research',
        'color': 'indigo'
    },
    'pdf-merger': {
        'name': 'PDF Merger',
        'template': 'pdf_merger',
        'title': 'Merge PDF Files',
        'description': 'Combine multiple PDF files into a single document.',
        'icon': 'fa-layer-group',
        'category': 'Docs & Images',
        'color': 'red'
    },
    'pdf-text-extractor': {
        'name': 'PDF Text Extractor',
        'template': 'pdf_text_extractor',
        'title': 'Extract text from PDF',
        'description': 'Extract plain text content from any PDF document.',
        'icon': 'fa-file-alt',
        'category': 'Docs & Images',
        'color': 'orange'
    },
    'pdf-editor': {
        'name': 'PDF Editor',
        'template': 'pdf_editor',
        'title': 'Secure PDF Editor',
        'description': 'Annotate, edit, and modify PDF files in your browser.',
        'icon': 'fa-edit',
        'category': 'Docs & Images',
        'color': 'red'
    },
    'markdown-to-pdf': {
        'name': 'Markdown to PDF',
        'template': 'markdown_to_pdf',
        'title': 'Convert Markdown to PDF',
        'description': 'Transform your markdown documents into styled PDF files.',
        'icon': 'fa-file-pdf',
        'category': 'Docs & Images',
        'color': 'slate'
    },
    'image-to-pdf': {
        'name': 'Image to PDF',
        'template': 'image_to_pdf',
        'title': 'Compile Images to PDF',
        'description': 'Convert your photos and images into a PDF album.',
        'icon': 'fa-images',
        'category': 'Docs & Images',
        'color': 'emerald'
    },
    'pdf-to-image': {
        'name': 'PDF to Image Converter',
        'template': 'pdf_to_image',
        'title': 'Convert PDF to Images',
        'description': 'Render PDF pages as high-quality JPG or PNG images.',
        'icon': 'fa-file-image',
        'category': 'Docs & Images',
        'color': 'orange'
    },
    'pdf-splitter': {
        'name': 'PDF Splitter',
        'template': 'pdf_splitter',
        'title': 'Split PDF Documents',
        'description': 'Split large PDFs into individual pages or ranges.',
        'icon': 'fa-cut',
        'category': 'Docs & Images',
        'color': 'rose'
    },
    'exif-viewer': {
        'name': 'Exif Viewer',
        'template': 'exif_viewer',
        'title': 'Photo Metadata Viewer',
        'description': 'View and remove EXIF data and GPS locations from photos.',
        'icon': 'fa-camera',
        'category': 'Docs & Images',
        'color': 'gray'
    },
    'ocr': {
        'name': 'Local OCR',
        'template': 'ocr_tool',
        'title': 'Image to Text (OCR)',
        'description': 'Extract text from images locally using AI-powered OCR.',
        'icon': 'fa-font',
        'category': 'Docs & Images',
        'color': 'sky'
    },
    'audio-transcriber': {
        'name': 'Audio Transcriber',
        'template': 'audio_transcriber',
        'title': 'AI Audio Transcriber',
        'description': 'Convert audio recordings to text locally.',
        'icon': 'fa-microphone-lines',
        'category': 'Data & Research',
        'color': 'indigo'
    },
    'qr-generator': {
        'name': 'QR Generator',
        'template': 'qr_generator',
        'title': 'Styled QR Generator',
        'description': 'Create custom, styled QR codes for any content.',
        'icon': 'fa-qrcode',
        'category': 'Docs & Images',
        'color': 'slate'
    },
    # NEW TOOLS
    'background-remover': {
        'name': 'Background Remover',
        'template': 'background_remover',
        'title': 'AI Background Remover',
        'description': 'Remove image backgrounds locally using AI. No data sent to servers.',
        'icon': 'fa-wand-magic-sparkles',
        'category': 'Docs & Images',
        'color': 'emerald'
    },
    'latex-to-pdf': {
        'name': 'LaTeX to PDF',
        'template': 'latex_to_pdf',
        'title': 'LaTeX Compiler & PDF Generator',
        'description': 'Compile LaTeX documents to high-quality PDF files in your browser.',
        'icon': 'fa-file-pdf',
        'category': 'Docs & Images',
        'color': 'rose'
    }
}

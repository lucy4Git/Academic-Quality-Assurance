"""Document parser package.

Import the factory function to get the right parser for a MIME type:

    from app.parsers.factory import get_parser
    parser = get_parser("application/pdf")
    result = await parser.extract(content, filename)
"""

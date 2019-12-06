"""
Module that contains all search APIs
"""
import flask
from api.api_base import APIBase
from core.database.database import Database


class SearchAPI(APIBase):

    def __init__(self):
        APIBase.__init__(self)

    @APIBase.exceptions_to_errors
    def get(self):
        """
        Perform a search
        """
        args = flask.request.args.to_dict()
        if args is None:
            args = {}

        db_name = args.get('db_name', None)
        page = int(args.get('page', 0))
        limit = int(args.get('limit', 20))

        if 'db_name' in args:
            del args['db_name']

        if 'page' in args:
            del args['page']

        if 'limit' in args:
            del args['limit']

        query_string = '&&'.join(['%s=%s' % (pair) for pair in args.items()])
        db = Database(db_name)
        results, total_rows = db.query(query_string, page, limit, return_total_rows=True)

        return self.output_text({'response': {'results': results, 'total_rows': total_rows}, 'success': True, 'message': ''})

import os
from .api import db, app


def main():
    db.create_all()
    app.run(host='0.0.0.0',
            port=os.environ.get('PORT', 13337),
            threaded=True)


if __name__ == '__main__':
    main()

# Hermanndata

WIP für REST API Backend unserer Daten

# Before production


- Uncomment `def create_user()` in app.py (line 387 ff)
- Implement Log in database
- Implement websocket or comment it
## WIKI
- Relationships & back_populates: https://stackoverflow.com/questions/51335298/concepts-of-backref-and-back-populate-in-sqlalchemy
- Swagger for flask:   https://stackoverflow.com/questions/62066474/python-flask-automatically-generated-swagger-openapi-3-0
-                      https://apispec.readthedocs.io/en/latest/index.html
-                      http://donofden.com/blog/2020/06/14/Python-Flask-automatically-generated-Swagger-3-0-openapi-Document
- Many to many delete orphans:     https://github.com/sqlalchemy/sqlalchemy/wiki/ManyToManyOrphan
-                                  https://stackoverflow.com/questions/68355401/how-to-remove-sqlalchemy-many-to-many-orphans-from-database

- IMAGES:

- WEBSOCKET:   https://www.donskytech.com/python-flask-websockets/?utm_content=cmp-true
-              https://blog.miguelgrinberg.com/post/add-a-websocket-route-to-your-flask-2-x-application
  
  SOCKETIO:     like in https://www.youtube.com/watch?v=FIBgDYA-Fas 
                and in https://stackoverflow.com/questions/32545634/flask-a-restful-api-and-socketio-server


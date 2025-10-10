Aeuqtio is an event driven application to gather expenses, assign them to a User, and at the end of each month split the expenses evenly across a group of useres e.g. a Family. 

Core Use cases:
1. add an expense
2. ammend an expense
3. create a Family/Group
4. Split expenses
5. Create invoice 

Auxillery 
user registration
login and authrization


Tech Stack:
Persten layer: Postgress
ORM Sqlalchemy + alembic 
FastApi
RabbitMQ

Architecture:
Event driven + CQRS

Project managment UV

Deployment:
AWS using github actions



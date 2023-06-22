#  Проект Foodgrgam

### Через Foodgram возможно создание и редактироване рецептов. Можно подписаться на авторов, добавлять понравившиеся рейепты в избранное, создать свою корзину и получить список ингредиентов для удобного заказа или похода в магазин!
Использованные технологии:

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)

### Как пользоваться проектом?
Клонируем репозиторий:
```python
git clone git@github.com:svkurick/foodgram-project-react.git
```
Переходим в директорию проекта и запускаем его:
```python
cd foodgram-project-react
```
Запускаем проект в режиме демона:
```python
sudo docker compose -f docker-compose.production.yml up -d
```
Далее нужно собрать статику проекта и выполнить миграции:
```python
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
Проект настроен на работу на 8000 порту :
```python
nano /etc/nginx/sites-enabled/default
```
```python
location / {
    proxy_pass http://127.0.0.1:8000;
}
```

### Проект с котиками готов к работе!
```python
https://kur1ck.sytes.net/
Админский доступ 
admin
Qwerty123!@#
```

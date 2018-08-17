import os
import asyncio
import psycopg2 
import aiopg #
import os.path
from aiohttp import web #
from aiohttp_session import get_session, new_session, setup #
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import base64
import bcrypt #
from cryptography import fernet #
import aiohttp_jinja2 #
import jinja2
import re
import json

routes = web.RouteTableDef()

dsn = os.environ['DATABASE_URL']
pool = None

@routes.get('/admin')
async def readmin(request):
    raise web.HTTPFound('/admin/login')

@routes.get('/{url:[A-Za-z0-9_\-]*}')
@aiohttp_jinja2.template('index.html')
async def index(request):
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            path = request.path[1:]
            await cur.execute('SELECT name, is_list, url, id, CASE WHEN is_list THEN ARRAY(SELECT ARRAY[name,url] FROM menu_items WHERE menu_items.id = menu.id) ELSE NULL END, CASE WHEN is_list THEN EXISTS(SELECT 1 FROM menu_items WHERE menu_items.id = menu.id AND menu_items.url = %s) ELSE CASE WHEN url = %s then TRUE ELSE FALSE END END FROM menu', (path, path))
            menu_data = await cur.fetchall()
            await cur.execute('SELECT title, data FROM pages WHERE url = %s', (request.match_info.get('url'),))
            page = await cur.fetchone()
            if page:
                return {'menu_data': menu_data, 'page': page}
            else:
                raise web.HTTPNotFound()

@routes.get('/file/{file:.+\.pdf}')
async def pdf(request):
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            await cur.execute('SELECT data FROM pdfs WHERE title = %s', (request.match_info.get('file'),))
            data = await cur.fetchone()
            if data:
                return web.Response(body=bytes(data[0]), content_type='application/pdf')
            else:
                raise web.HTTPNotFound()
        
                
@routes.get('/admin/login')
@aiohttp_jinja2.template('login.html')
async def admin(request):
    if 'online' in await get_session(request): raise web.HTTPFound('/admin/pages')
    return {}
    
@routes.post('/login')
async def login(request):
    try:
        session = await get_session(request)
        if not 'online' in session:
            auth = await request.post()
            async with pool.acquire() as conn:
                async with await conn.cursor() as cur:
                    await cur.execute('SELECT password, is_admin, id FROM users WHERE login = %s', (auth['login'],))
                    pwa = await cur.fetchone()
                    if pwa and bcrypt.checkpw(auth['password'].encode(), bytes(pwa[0])):
                        session = await new_session(request)
                        session['online'] = True
                        session['id'] = pwa[2]
                        session['login'] = auth['login']
                        if pwa[1]:
                            session['admin'] = True
                        return web.json_response({'ok': True, 'result': 'Ви успішно авторизувались'})
                    else:
                        return web.json_response({'ok': False, 'result': 'Неправильний логін чи пароль'})
        else:
            return web.json_response({'ok': True, 'result': 'Ви вже ввійшли в систему'})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})

@routes.get('/admin/logout')
async def logout(request):
    (await get_session(request)).invalidate()
    raise web.HTTPFound('/')

@routes.get('/admin/pages')
@aiohttp_jinja2.template('pages.html')
async def pages(request):
    session = await get_session(request)
    if not 'online' in session: raise web.HTTPFound('/admin/login')
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            if 'admin' in session:
                await cur.execute('SELECT title, url FROM pages')
            else:
                await cur.execute('SELECT title, url FROM pages WHERE editor = %s', (session['id'],))
            return {'pages': True, 'session': session, 'title': 'Панель редактора', 'pages': await cur.fetchall()}
    
@routes.get('/admin/new_page')
@aiohttp_jinja2.template('new_page.html')
async def new_page(request):
    session = await get_session(request)
    if not 'online' in session: raise web.HTTPFound('/admin/login')
    return {'pages': True, 'session': session, 'title': 'Нова сторінка'}

@routes.get('/admin/edit/{url:[A-Za-z0-9_\-]*}')
@aiohttp_jinja2.template('edit_page.html')
async def edit_page(request):
    session = await get_session(request)
    if not 'online' in session: raise web.HTTPFound('/admin/login')
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            if 'admin' in session:
                await cur.execute('SELECT id, title, url, data FROM pages WHERE url = %s', (request.match_info.get('url'),))
            else:
                await cur.execute('SELECT id, title, url, data FROM pages WHERE url = %s, editor = %s', (request.match_info.get('url'), session['id']))
            page = await cur.fetchone()
            if page:
                return {'pages': True, 'session': session, 'title': 'Редагування сторінки', 'page': page}
            else:
                raise web.HTTPNotFound()

@routes.post('/upload_page')
async def up_page(request):
    try:
        session = await get_session(request)
        if not 'online' in session: return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        page = await request.post()
        if not re.match('^[A-Za-z0-9_\-]*$', page['url']):
            return web.json_response({'ok': False, 'result': 'URL не відповідає вимогам'})
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                if 'id' in page:
                    if 'admin' in session and 'editor' in page:
                        await cur.execute('UPDATE pages SET title = %s, url = %s, data = %s, editor = %s WHERE id = %s', (page['title'], page['url'], page['data'], page['editor'], page['id']))
                    elif 'admin' in session:
                        await cur.execute('UPDATE pages SET title = %s, url = %s, data = %s WHERE id = %s', (page['title'], page['url'], page['data'], page['id']))
                    else:
                        await cur.execute('UPDATE pages SET title = %s, url = %s, data = %s WHERE id = %s and editor = %s', (page['title'], page['url'], page['data'], page['id'], session['id']))
                else:
                    await cur.execute('INSERT INTO pages (title, url, data, editor) VALUES (%s, %s, %s, %s)', (page['title'], page['url'], page['data'], session['id']))
                return web.json_response({'ok': True, 'result': 'Сторінка була успішно збережена'})
    except psycopg2.IntegrityError:
        return web.json_response({'ok': False, 'result': 'Існує сторінка з таким URL'})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})
        
@routes.post('/delete_page')
async def del_page(request):
    try:
        session = await get_session(request)
        if not 'online' in session: return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        page = await request.post()
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                if 'admin' in session:
                        await cur.execute('DELETE FROM pages WHERE url = %s', (page['url'],))
                else:
                        await cur.execute('DELETE FROM pages WHERE url = %s AND editor = %s', (page['url'], session['id']))
                return web.json_response({'ok': True, 'result': 'Сторінка була успішно видалена'})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})
        
@routes.post('/upload_pdf')
async def up_pdf(request):
    try:
        session = await get_session(request)
        if not 'online' in session: return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        pdfs = await request.post()
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                files = []
                for pdf_id in pdfs:
                    pdf = pdfs[pdf_id]
                    if pdf.content_type == 'application/pdf':
                        try:
                            await cur.execute('INSERT INTO pdfs (title, data, owner) VALUES (%s, %s, %s)', (pdf.filename, pdf.file.read(), session['id']))
                            files.append(pdf.filename)
                        except:
                            pass
                if len(files) == 0:
                    return web.json_response({'ok': False, 'result': 'Жоден файл не був завантажений'})
                elif len(files) == 1:
                    return web.json_response({'ok': True, 'result': 'Був завантажений файл ' + files[0]})
                else:
                    return web.json_response({'ok': True, 'result': 'Були завантажен такі файли: ' + ', '.join(files)})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})

@routes.get('/admin/my_files')
async def my_files(request):
    try:
        session = await get_session(request)
        if not 'online' in session: return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute('SELECT title FROM pdfs WHERE owner = %s', (session['id'],))
                return web.json_response({'ok': True, 'result': [i[0] for i in (await cur.fetchall())]})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})

@routes.get('/admin/profile')
@aiohttp_jinja2.template('profile.html')
async def profile(request):
    session = await get_session(request)
    if not 'online' in session: raise web.HTTPFound('/admin/login')
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            await cur.execute("SELECT login FROM users WHERE id = %s", (session['id'],))
            login_w = await cur.fetchone()
            login = login_w[0] if login_w else ''
            session['login'] = login
            return {'profile': True, 'session': session, 'title': 'Редагування профілю', 'login': login}

@routes.get('/admin/menu')
@aiohttp_jinja2.template('menu.html')
async def menu(request):
    session = await get_session(request)
    if not 'online' in session: raise web.HTTPFound('/admin/login')
    if not 'admin' in session: raise web.HTTPForbidden()
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            await cur.execute('SELECT name, is_list, url, ARRAY(SELECT ARRAY[name,url] FROM menu_items WHERE menu_items.id = menu.id) FROM menu')
            return {'menu': True, 'menu_data': await cur.fetchall(), 'session': session, 'title': 'Редагування меню'}
    
@routes.post('/save_menu')
async def menu(request):
    try:
        session = await get_session(request)
        if not 'online' in session: return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        if not 'admin' in session: raise web.HTTPForbidden()
        result = json.loads((await request.post())['data'])
        items = []; small_items = []; id_ = 0
        for r in result:
            items.append((id_, r['name'], r['is_list'], r['data'] if not r['is_list'] else None))
            if r['is_list']:
                small_items.extend([(id_, i['name'], i['url']) for i in r['data']])
            id_ += 1
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute("DELETE FROM menu; DELETE FROM menu_items")
                for item in items:
                    await cur.execute("INSERT INTO menu (id, name, is_list, url) VALUES %s", (item,))
                for small_item in small_items:
                    await cur.execute("INSERT INTO menu_items (id, name, url) VALUES %s", (small_item,))
        return web.json_response({'ok': True, 'result': 'Все збережено'})
    # except psycopg2.IntegrityError:
    #     return web.json_response({'ok': False, 'result': 'Перевірте введені дані'})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})
    
@routes.get('/admin/users')
@aiohttp_jinja2.template('users.html')
async def users(request):
    session = await get_session(request)
    if not 'online' in session: raise web.HTTPFound('/admin/login')
    if not 'admin' in session: raise web.HTTPForbidden()
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            await cur.execute("SELECT id, login, is_admin FROM users ORDER BY id")
            return {'session': session, 'users': await cur.fetchall(), 'title': 'Редагування користувачів'}

@routes.post('/reg_user')
async def reg_user(request):
    try:
        session = await get_session(request)
        if not 'online' in session: return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        if not 'admin' in session: raise web.HTTPForbidden()
        reg = await request.post()
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute("INSERT INTO users (login, password, is_admin) VALUES (%s, %s, %s)", (reg['login'], bcrypt.hashpw(reg['password'].encode(), bcrypt.gensalt()), False))
                return web.json_response({'ok': True, 'result': 'Користувач ' + reg['login'] + ' успішно зареєстрований'})
    except psycopg2.IntegrityError:
        return web.json_response({'ok': False, 'result': 'Вже існує користувач з таким логіном'})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})

@routes.post('/edit_user')
async def edit_user(request):
    try:
        session = await get_session(request)
        if not 'online' in session: return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                reg = await request.post()
                id_ = reg['id'] if 'id' in reg and 'admin' in session else session['id']
                is_admin = 'admin' in session and 'is_admin' in reg and reg['is_admin']
                if len(reg['password']) > 0:
                    await cur.execute("UPDATE users SET login = %s, password = %s, is_admin = %s WHERE id = %s", (reg['login'], bcrypt.hashpw(reg['password'].encode(), bcrypt.gensalt()), is_admin, id_))
                else:
                    await cur.execute("UPDATE users SET login = %s, is_admin = %s WHERE id = %s", (reg['login'], is_admin, id_))
                return web.json_response({'ok': True, 'result': 'Користувач ' + reg['login'] + ' успішно відредагований'})
    except psycopg2.IntegrityError:
        return web.json_response({'ok': False, 'result': 'Вже існує користувач з таким логіном'})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})

@routes.post('/delete_user')
async def edit_user(request):
    try:
        if not 'online' in await get_session(request): return web.json_response({'ok': False, 'result': 'Переавторизуйтесь <a href="/admin/login" target="_blank">ТУТ</a>'})
        if not 'admin' in session: raise web.HTTPForbidden()
        async with pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute("DELETE FROM users WHERE id = %s", ((await request.post())['id'],))
                return web.json_response({'ok': True, 'result': 'Користувач успішно видалений'})
    except:
        return web.json_response({'ok': False, 'result': 'Незрозуміла помилка?!'})

async def create_connection(app):
    global pool
    pool = await aiopg.create_pool(dsn)
    async with pool.acquire() as conn:
        async with await conn.cursor() as cur:
            await cur.execute('CREATE TABLE IF NOT EXISTS pages ('
                        'id SERIAL,'
                        'title text NOT NULL,'
                        'url text NOT NULL PRIMARY KEY,'
                        'data text NOT NULL,'
                        'editor integer NOT NULL)')
            await cur.execute('CREATE TABLE IF NOT EXISTS users ('
                        'id SERIAL,'
                        'login text NOT NULL PRIMARY KEY,'
                        'password bytea NOT NULL,'
                        'email text,'
                        'is_admin boolean NOT NULL)')
            await cur.execute('CREATE TABLE IF NOT EXISTS menu ('
                        'id integer NOT NULL PRIMARY KEY,'
                        'name text NOT NULL,' #CHECK (char_length(name) > 0)
                        'is_list boolean NOT NULL,'
                        'url text)')
            await cur.execute('CREATE TABLE IF NOT EXISTS menu_items ('
                         'id integer NOT NULL,'
                         'name text NOT NULL,' #CHECK (char_length(name) > 0)
                         'url text NOT NULL)')
            await cur.execute('CREATE TABLE IF NOT EXISTS pdfs ('
                        'id SERIAL,'
                        'title text NOT NULL PRIMARY KEY,'
                        'data bytea NOT NULL,'
                        'owner integer NOT NULL)')

async def web_app():
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))
    app['static_root_url'] = '/static'
    app.add_routes(routes)
    app.router.add_static('/static/', os.path.join( os.path.dirname(__file__), 'static'), name='static')
    setup(app, EncryptedCookieStorage(base64.urlsafe_b64decode(fernet.Fernet.generate_key())))
    app.on_startup.append(create_connection)
    return app

if __name__ == '__main__':
    app = web_app()
    web.run_app(app)

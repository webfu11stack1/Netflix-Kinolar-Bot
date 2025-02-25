import shutil
import sqlite3
from aiogram import Bot, Dispatcher, types,executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import logging

from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup,KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types.inline_keyboard import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.types import InputTextMessageContent
from telegram import CallbackQuery, InlineQueryResultArticle


conn = sqlite3.connect('netflixkino.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS userid (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE
);
''')
cursor.execute('''CREATE TABLE IF NOT EXISTS channel (id INTEGER PRIMARY KEY, channel_id TEXT, channel_url TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS userid_today (id INTEGER PRIMARY KEY, user_id_tod INTEGER, registration_date DATE)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, admin_id INTEGER , admin_name TEXT)''')

def init_db():
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    # Create the movies table with necessary columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            video_file_id TEXT,
            movie_code INTEGER
            
        )
    ''')
    conn.commit()
    conn.close()

init_db()
cursor.execute("""CREATE TABLE IF NOT EXISTS saved_movies (id INTEGER PRIMARY KEY , user_id INTEGER , movie_code INTEGER )""")
import sqlite3

# Connect to the database
with sqlite3.connect('netflixkino.db') as conn:
    cursor = conn.cursor()

    # Check if the download_count column exists
    cursor.execute("PRAGMA table_info(movies)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'download_count' not in columns:
        cursor.execute("ALTER TABLE movies ADD COLUMN download_count INTEGER DEFAULT 0")
        conn.commit()
    else:
        print("Table yes")

    print("Column 'download_count' added successfully.")



conn.commit()


bot_token = "7920193248:AAEQUdVv6v-cTlVgL_VD6lBhTv8K1_oq6F0"
bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def search_data(query):
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    # Qidiruvni bajarish
    if query:
        cursor.execute(
            '''SELECT name, description, video_file_id, movie_code, download_count
               FROM movies 
               WHERE LOWER(name) LIKE ? OR movie_code LIKE ?''', 
            ('%' + query.lower() + '%', '%' + query + '%')
        )
    else:
        cursor.execute('SELECT name, description, video_file_id, movie_code, download_count FROM movies')

    rows = cursor.fetchall()
    conn.close()

    # Qidiruv natijalarini qayta ishlash
    results = []
    for row in rows:
        name, description, file_id, movie_code,download_count = row

        if file_id:
            results.append({
                "name": name,
                "description": description,
                "file_id": file_id,
                "movie_code": movie_code,
                "download_count":download_count
            })
        else:
            logging.warning(f"Bo'sh file_id topildi: {row}")

    if not results:
        logging.info("Hech qanday natija topilmadi!")

    return results



# Add movie to database
def add_movie_to_db(name, description, video_file_id, movie_code, download_count=0):
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO movies (name, description, video_file_id, movie_code, download_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, video_file_id, movie_code, download_count))
        conn.commit()


# Fetch movies from database
def fetch_movies(query=None):
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    if query:
        cursor.execute("SELECT name, description, video_file_id, movie_code,download_count FROM movies WHERE name OR movie_code LIKE ?", (f"%{query}%",))
    else:
        cursor.execute("SELECT name, description, video_file_id, movie_code,download_count FROM movies")

    rows = cursor.fetchall()
    conn.close()
    return rows


@dp.message_handler(commands=["help"], state="*")
async def panel(message: types.Message, state: FSMContext):
    await message.answer("<b>Botni ishga tushirish - /start\nAdmin bilan bog'lanish - @python_chi</b>",parse_mode="html")
    await state.finish()

#panel



@dp.message_handler(commands=["panel"], state="*")
async def panel(message: types.Message, state: FSMContext):
    mes_id = message.from_user.id
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    cursor.execute("SELECT admin_id FROM admins")
    admin_user_ids = cursor.fetchall()  # Fetch all admin IDs

    admin_user_ids = [admin[0] for admin in admin_user_ids]  # Extract IDs from tuples
    try:
        if mes_id in admin_user_ids or mes_id == 1996936737:
            panel = ReplyKeyboardMarkup(
                keyboard=[
                    ["📊Statistika", "⚪️Xabarlar bo'limi"],
                   
                    ["📑Users","📑Baza"],
                    ["🎥Kino bo'limi"] ,
                     ["👤Admin bo'limi", "📢Kanal bo'limi"]
                   
                ], resize_keyboard=True
            )
            await message.answer("Panel bo'limi!", reply_markup=panel)
            await state.set_state("panel")
        else:
            pass
    except Exception as e:
        await message.answer("Panelga kirishda xatolik yuz berdi.")
        print(f"Error: {e}")
    finally:
        conn.commit()
        conn.close()
        await state.finish()

@dp.message_handler(text="🎥Kino bo'limi",state="*")
async def kinobol(message:types.Message,state:FSMContext):
    kb=ReplyKeyboardMarkup(
        keyboard=[
            ["📽Kino qo'shish","⛔️Kino o'chirish"],
            ["🗄Bosh panel"]
        ],resize_keyboard=True
    )
    await message.answer('kino bolimidasiz!',reply_markup=kb)
    await state.finish()
    await state.set_state("kbbol")


@dp.message_handler(text="📽Kino qo'shish",state="*")
async def start_adding_movie(message: types.Message, state: FSMContext):
    cancel_button = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_add")]]
    )
    await message.answer("Kino nomini kiriting:", reply_markup=cancel_button)
    await state.set_state("add_movie_name")



@dp.message_handler(state="add_movie_name", content_types=types.ContentTypes.TEXT)
async def get_movie_name(message: Message, state: FSMContext):
    movie_name = message.text.strip()
    await state.update_data(name=movie_name)
    await message.answer("Kino ta'rifini kiriting:")
    await state.set_state("add_movie_description")

@dp.message_handler(state="add_movie_description", content_types=types.ContentTypes.TEXT)
async def get_movie_description(message: Message, state: FSMContext):
    movie_description = message.text.strip()
    await state.update_data(description=movie_description)
    await message.answer("Kino uchun kodini")
    await state.set_state("add_movie_code")

@dp.message_handler(state="add_movie_code", content_types=types.ContentTypes.TEXT)
async def get_movie_thumbnail(message: Message, state: FSMContext):
    movie_code = message.text.strip()
    await state.update_data(movie_code=movie_code)
    await message.answer("Kino uchun videoni yuboring:")
    await state.set_state("add_movie_video")

@dp.message_handler(state="add_movie_video", content_types=types.ContentTypes.VIDEO)
async def get_movie_video(message: Message, state: FSMContext):
    video_id = message.video.file_id
    data = await state.get_data()

    # Add movie to database, with default download_count of 0
    add_movie_to_db(
        name=data['name'],
        description=data['description'],
        video_file_id=video_id,
        movie_code=data['movie_code'],
        download_count=0  # Explicitly passing download_count as 0
    )
    await message.answer("Kino muvaffaqiyatli qo'shildi! ✅")
    await state.finish()


from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
import hashlib

@dp.inline_handler()
async def inline_query_handler(query: types.InlineQuery):
    query_text = query.query.strip()  # Foydalanuvchi kiritgan qidiruv matni
    results = await search_data(query_text)  # Qidiruv funksiyasidan natijalar

    inline_results = []
    for result in results:
        if result["file_id"]:  # Faqat fayl ID mavjud bo'lsa
            # Unikal ID yaratish (hashlib orqali)
            unique_id = hashlib.md5(f"{result['movie_code']}{result['name']}".encode()).hexdigest()

            # InlineQueryResultArticle obyekti yaratish
            inline_results.append(
                InlineQueryResultArticle(
                    id=unique_id,
                    title=result["name"],
                    description=result["description"],
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"🎬 <b>{result['name']}</b>\n\n"
                            f"{result['description']}\n\n"
                            f"Kodni kiriting: <code>{result['movie_code']}</code>"
                        ),
                        parse_mode="HTML",
                    ),
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton(
                            "📽 Kinoni ko'rish",
                            url=f"https://t.me/netflix_kinolarbot?start={result['movie_code']}"
                        )
                    )
                )
            )

    # Agar natijalar bo'lmasa, default javob qo'shing
    if not inline_results:
        inline_results.append(
            InlineQueryResultArticle(
                id="0",
                title="Natija topilmadi",
                input_message_content=InputTextMessageContent(
                    "Hech qanday mos keluvchi natija topilmadi. 🔍"
                )
            )
        )

    # Inline queryga javob berish
    await bot.answer_inline_query(
        query.id,
        results=inline_results,
        cache_time=1,  # Tezkor javoblar uchun cache vaqtini minimal qilish
        is_personal=True
    )




@dp.message_handler(text="⛔️Kino o'chirish", state="*")
async def dekkino(message: types.Message, state: FSMContext):
    await message.answer("Kino o'chirish uchun kodini yuboring!")
    await state.set_state("dkino")


@dp.message_handler(state="dkino")
async def dkin(message: types.Message, state: FSMContext):
    dk = message.text
    dkk = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Yes", callback_data="yes"),
             InlineKeyboardButton(text="No", callback_data="no")]
        ], row_width=2
    )
    await state.update_data(dk=dk)  # Store dk in the FSMContext
    await message.answer(f"{dk} kodli kino o'chirilsinmi!", reply_markup=dkk)
    await state.set_state("kodo")


@dp.callback_query_handler(lambda d: d.data == "yes", state="kodo")
async def yesdel(calmes: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dk = data.get("dk")  # Retrieve dk (movie_code) from the state
    
    if dk and dk.isdigit():
        conn = sqlite3.connect("netflixkino.db")
        cursor = conn.cursor()

        # Delete the movie record from the 'movies' table using the movie_code (dk)
        cursor.execute("DELETE FROM movies WHERE movie_code = ?", (dk,))
        conn.commit()
        conn.close()

        # Use calmes.answer() to show an alert
        await calmes.answer(f"{dk} kodli kino o'chirildi!✅", show_alert=True)
    else:
        await calmes.answer("Raqam kiriting!", show_alert=True)

    await state.finish()




@dp.callback_query_handler(lambda d: d.data == "no", state="*")
async def nodel(calmes: types.CallbackQuery, state: FSMContext):
    await calmes.message.answer("⛔️ O'chirish bekor qilindi.")
    await state.finish()



    
@dp.callback_query_handler(lambda d:d.data=="end1",state="next1")
async def end(cal:types.CallbackQuery,state:FSMContext):
    await state.finish()
    await panel(cal.message,state)

@dp.message_handler(text="⚪️Xabarlar bo'limi",state="*")
async def xabarbolim(message:types.Message,state:FSMContext):
    xabarlar = ReplyKeyboardMarkup(
        keyboard=[
            ["⚪️Inline Xabar","🔗Forward xabar"],
            ["👤Userga xabar"],
            ["🖥Code xabar","🗄Bosh panel"]
        ],
        resize_keyboard=True
    )
    await message.answer('Xabarlar bolimidasiz!',reply_markup=xabarlar)
    await state.finish()
    await state.set_state("xabarbolim")

#Code xabar
@dp.message_handler(text="🖥Code xabar",state="*")
async def codemes(cmes:types.Message,state:FSMContext):
    await cmes.answer("Xabaringizi qoldiring!")
    await state.finish()
    await state.set_state("cmes")

@dp.message_handler(state="cmes")
async def ccmes(cmess:types.Message,state:FSMContext):
    cmessage = cmess.text
    yetkazilganlar = 0
    yetkazilmaganlar = 0

    cursor.execute("SELECT DISTINCT user_id FROM userid")
    user_ids = cursor.fetchall()

    for user_id in user_ids:
        try:
            
                await bot.send_message(user_id[0], text=f' ```\n {cmessage} \n```  ',parse_mode="MARKDOWN")
                yetkazilganlar += 1
           
        except Exception as e:
            print(f"Error: {e}")
            yetkazilmaganlar += 1

    await cmess.answer(
        f"<b>Xabar foydalanuvchilarga muvaffaqiyatli yuborildi!</b>✅\n\n"
        f"🚀Yetkazildi : <b>{yetkazilganlar}</b> ta\n"
        f"🛑Yetkazilmadi : <b>{yetkazilmaganlar}</b> ta",
        parse_mode="HTML"
    )
    await state.finish()

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# FSM state for sending a message to a specific user
class AdminStates(StatesGroup):
    waiting_for_user_id = State()  # Admin waiting for the user_id input
    waiting_for_message = State()  # Admin waiting for the message to send

# Admin triggers the action to send a message
@dp.message_handler(text="👤Userga xabar", state="*")
async def handle_send_message_to_user(call: types.Message):
    # Ask admin to input the user_id
    await call.answer("Iltimos, xabar yubormoqchi bo'lgan foydalanuvchining user_id sini kiriting:")
    
    # Set FSM state to waiting for user_id
    await AdminStates.waiting_for_user_id.set()

# Admin types the user_id
@dp.message_handler(state=AdminStates.waiting_for_user_id)
async def receive_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    
    # Store the user_id in FSM context
    await state.update_data(user_id=user_id)

    # Ask admin to type the message to send
    await message.answer(f"Foydalanuvchiga yuboriladigan xabarni yozing:")
    
    # Set FSM state to waiting for the message
    await AdminStates.waiting_for_message.set()



@dp.message_handler(state=AdminStates.waiting_for_message)
async def send_message_to_user(message: types.Message, state: FSMContext):
    # Get user_id and message content from FSM context
    user_data = await state.get_data()
    user_id = user_data.get("user_id")
    admin_message = message.text.strip()

    # Try sending the message to the specified user_id
    try:
        await bot.send_message(user_id, f"👤Admindan xabar:\n``` {admin_message}  ```",parse_mode="Markdown")
        await message.answer("Xabar yuborildi.")
    except Exception as e:
        print(f"Error: {e}")
        await message.answer("Xabar yuborishda xatolik yuz berdi.")

    # Reset FSM state
    await state.finish()




#Forward message
import re
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, MessageToForwardNotFound

@dp.message_handler(text="🔗Forward xabar", state="*")
async def forwardmes(fmessage: types.Message, state: FSMContext):
    await fmessage.answer("Xabarni havola linki yoki raqamini yuboring!")
    await state.set_state("fmes")

@dp.message_handler(state="fmes")
async def fmes(fmes: types.Message, state: FSMContext):
    try:
        f_mes = int(fmes.text)  # Foydalanuvchidan olingan raqam
    except ValueError:
        await fmes.answer("Iltimos, to'g'ri xabar raqamini kiriting!")
        return

    yetkazilganlar = 0
    yetkazilmaganlar = 0
    blok_qilganlar = 0  # Blok qilgan foydalanuvchilar soni

    cursor.execute("SELECT DISTINCT user_id FROM userid")
    user_ids = cursor.fetchall()

    for user_id in user_ids:
        try:
            await bot.forward_message(
                chat_id=user_id[0], 
                from_chat_id='@sjsksnsbsh', 
                message_id=f_mes
            )
            yetkazilganlar += 1
        except BotBlocked:
            blok_qilganlar += 1
        except MessageToForwardNotFound:
            await fmes.answer("Berilgan xabarni topib bo'lmadi.")
            return
        except ChatNotFound:
            yetkazilmaganlar += 1
        except Exception as e:
            print(f"Error: {e}")
            yetkazilmaganlar += 1

    await fmes.answer(
        f"<b>Xabar foydalanuvchilarga muvaffaqiyatli yuborildi!</b>✅\n\n"
        f"🚀 Yetkazildi : <b>{yetkazilganlar}</b> ta\n"
        f"🛑 Yetkazilmadi : <b>{yetkazilmaganlar}</b> ta\n"
        f"❌ Blok qilganlar : <b>{blok_qilganlar}</b> ta",
        parse_mode="HTML"
    )
    
    await state.finish()


    

@dp.message_handler(text="👤Admin bo'limi",state="*")
async def adminsb(message:types.Message,state:FSMContext):
    adminsbolim = ReplyKeyboardMarkup(
        keyboard=[
            ["👤Adminlar"],
            ["➕👤Admin qo'shish","⛔️👤Admin o'chirish"],
             ["🗄Bosh panel"]
        ],
        resize_keyboard=True
    ) 
    await message.answer("<b>Siz admin bo'limidasiz!</b>",reply_markup=adminsbolim,parse_mode="HTML")
    await state.finish()
    await state.set_state("admnbolim")


@dp.message_handler(text="➕👤Admin qo'shish", state="*")
async def admin_add(message: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    await message.answer("Admin qo'shish uchun idsini yuboring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("ad_add")

@dp.message_handler(state="ad_add")
async def admin_id(message: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global admin_idd
    admin_idd = int(message.text)
    await message.answer("Ismini yuboring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("ad_ism")

@dp.message_handler(state="ad_ism")
async def admin_ism(message: types.Message, state: FSMContext):
    global admin_namee
    admin_namee = message.text
    ad_qoshish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Qo'shish", callback_data="qosh"),
             InlineKeyboardButton(text="Rad qilish", callback_data="radqil")]
        ], row_width=2
    )
    await message.answer(f"<b>Id:</b> {admin_idd} \n<b>Ism:</b> {admin_namee} ", reply_markup=ad_qoshish,
                         parse_mode="HTML")
    await state.finish()
    await state.set_state("q")

@dp.callback_query_handler(lambda q: q.data == "qosh", state="*")
async def qoshish(query: types.CallbackQuery, state: FSMContext):
   

    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()


    cursor.execute("INSERT INTO admins (admin_id, admin_name) VALUES (?, ?)", (admin_idd, admin_namee))

    conn.commit()

    await query.message.reply(
        f"<b>Yangi admin qo'shildi!</b>\n\n<b>ID</b>: {admin_idd}\n<b>Ism</b>: {admin_namee}",
        parse_mode="HTML"
    )

    await state.finish()

    conn.close()


#Admin o'chirish

@dp.message_handler(text="⛔️👤Admin o'chirish", state="*")
async def admin_add11(message: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    await message.answer("Admin O'chirish uchun idsini yuboring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("ad_addd")

@dp.message_handler(state="ad_addd")
async def admin_id1d(message: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global admin_idd1
    admin_idd1 = int(message.text)
    await message.answer("Ismini yuboring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("ad_ismm")

@dp.message_handler(state="ad_ismm")
async def admin_ismm(message: types.Message, state: FSMContext):
    global admin_namee1
    admin_namee1 = message.text
    ad_qoshish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="O'chirish", callback_data="ochir"),
             InlineKeyboardButton(text="Rad qilish", callback_data="radqil")]
        ], row_width=2
    )
    await message.answer(f"<b>Id:</b> {admin_idd1} \n<b>Ism:</b> {admin_namee1} ", reply_markup=ad_qoshish,
                         parse_mode="HTML")
    await state.finish()
    await state.set_state("qq")

@dp.callback_query_handler(lambda q: q.data == "ochir", state="*")
async def ocir(query: types.CallbackQuery, state: FSMContext):
   

    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()


    cursor.execute("DELETE FROM admins WHERE admin_id=? AND admin_name=?", (admin_idd1,admin_namee1))
    conn.commit()

    await query.message.reply(
        f"<b>Admin o'chirildi!</b>\n\n<b>ID</b> : {admin_idd1}\n<b>Ism</b> : {admin_namee1}",
        parse_mode="HTML"
    )

    await state.finish()

    conn.close()


#Adminlar
@dp.message_handler(text="👤Adminlar", state="*")
async def admins_list(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, admin_id INTEGER , admin_name TEXT)''')

    cursor.execute('SELECT  admin_id, admin_name FROM admins')
    admins_data = cursor.fetchall()
    response = "Adminlar \n"

    if not admins_data:
        await message.reply("Adminlar ro'yxati bo'sh.")
        await state.finish()
    else:
        for admin_data in admins_data:
            admin_id, admin_name = admin_data[0], admin_data[1]
            response += f"ID: {admin_id} \nIsm: {admin_name} \nProfil: tg://user?id={admin_id}\n"

        await message.reply(response, parse_mode="Markdown")


        await state.finish()

    conn.close()



@dp.callback_query_handler(lambda s:s.data=="radqil",state="*")
async def rad(query:types.CallbackQuery,state:FSMContext):
    await query.message.delete()
    await state.finish()
    

import sqlite3
from datetime import datetime as dt

#Statistika
@dp.message_handler(text="📊Statistika", state="*")
async def statistika(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM userid")
    user_count = cursor.fetchone()[0]

    current_datetime = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    
    await message.reply(f"⌚️Statistika vaqt: <b>{current_datetime}</b>\n\n"
                        f"📊Foydalanuvchilar soni: <b>{user_count} ta</b> 👤 mavjud✅\n", parse_mode="HTML")
    
    await state.finish()


@dp.message_handler(text="📢Kanal bo'limi",state="*")
async def kanalb(message:types.Message,state:FSMContext):
    kanalsbolim = ReplyKeyboardMarkup(
        keyboard=[
            ["📢Kanallar"],
            ["➕Kanal qo'shish","⛔️Kanal o'chirish"],
            ["🗄Bosh panel"]
        ],
        resize_keyboard=True
    ) 
    await message.answer("<b>Siz 📢Kanal bo'limidasiz!</b>",reply_markup=kanalsbolim,parse_mode="HTML")
    await state.finish()
    await state.set_state("kanalbolim")

#kanal qoshish 
    
@dp.message_handler(text="➕Kanal qo'shish",state="*")
async def kanal_add(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    await message.answer("Kanal idsini yuboring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("kanal_id")

@dp.message_handler(state="kanal_id")
async def kanal_id(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global kanal_idd;
    kanal_idd = (message.text)
    if kanal_idd.startswith('-100'):
        await message.answer("Kanal url yuboring !",reply_markup=tugatish)
        await state.finish()
        await state.set_state("kanal_url")
    else:
        await message.answer("Idda xatolik")    
        
        
@dp.message_handler(state="kanal_url")
async def kanal_url(message:types.Message,state:FSMContext):
    global kanal_urll;
    kanal_urll = message.text
    if  kanal_urll.startswith("https:"):
        conn = sqlite3.connect('netflixkino.db')
        cursor = conn.cursor()
    
        cursor.execute("INSERT INTO channel (channel_id, channel_url) VALUES (?, ?)", (kanal_idd, kanal_urll))

        conn.commit()
        await message.answer("Kanal qo'shildi")
        await state.finish()
    else:
        await message.answer("Kanal urlda xatolik!")


@dp.message_handler(text="🗄Bosh panel",state="*")
async def boshpanel(message:types.Message,state:FSMContext):
    await panel(message,state)
    await state.finish()

#Kanallar



@dp.message_handler(text="📢Kanallar",state="*")
async def kanallar(message:types.Message,state:FSMContext):
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    cursor.execute("SELECT channel_url FROM channel")
    channels = cursor.fetchone()
    respons = "Bazadagi ulangan kanallar \n"
    try:

        for chan in channels:
            chan = channels[0]
            
            respons += f"Kanal : @{chan[13:]} \n"

        await message.answer(respons)
        await state.finish()
    except:
        await message.answer("Kanal mavjud emas!")
        await state.finish()
        
@dp.callback_query_handler(lambda c: c.data == "cancel_add",state="*")
async def cancel_addition(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Amal bekor qilindi.")
    await state.finish()

#Kanal o'chirish
@dp.message_handler(text="⛔️Kanal o'chirish",state="*")
async def kanal_del(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    await message.answer("Kanal idsini yuboring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("kanal_del")

@dp.message_handler(state="kanal_del")
async def kanal_idel(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global kanal_iddel;
    kanal_iddel = (message.text)
    if kanal_iddel.startswith('-100'):
        await message.answer("Kanal url yuboring !",reply_markup=tugatish)
        await state.finish()
        await state.set_state("kanal_urld")
    else:
        await message.answer("Idda xatolik")    
        
        
@dp.message_handler(state="kanal_urld")
async def kanal_urldel(message:types.Message,state:FSMContext):
    global kanal_urlldel;
    kanal_urlldel = message.text
    if  kanal_urlldel.startswith("https:"):
        conn = sqlite3.connect('netflixkino.db')
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM channel WHERE channel_id=? AND channel_url=?", (kanal_iddel,kanal_urlldel))
            conn.commit()
            await message.answer("Kanal o'chirildi!")
            await state.finish()
        except:
            await message.answer("Bunday kanal yoki url topilmadi!")
    else:
        await message.answer("Kanal urlda xatolik!")


#Inine Xabar 
        
@dp.message_handler(text="⚪️Inline Xabar",state="*")
async def inline_xabar(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )

    await message.answer("Xabaringiz qoldiring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("send_message")

@dp.message_handler(state="send_message",content_types=types.ContentTypes.TEXT)
async def send_message(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global xabar1
    xabar1 = message.text
    await message.answer("Inline tugma uchun link yuboring!",reply_markup=tugatish)
    await state.finish()
    await state.set_state("link")


@dp.message_handler(state="link")
async def link(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global linkk;
    linkk = message.text
    await message.answer("Inline tugma uchun nom bering ! ",reply_markup=tugatish)
    await state.finish()
    await state.set_state("inline_nom")


@dp.message_handler(state="inline_nom")
async def inline_name(message:types.Message,state:FSMContext):
    global inline_nom
    inline_nom = message.text
    inline_send = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{inline_nom}",url=f"{linkk}")],
            [InlineKeyboardButton(text="Yuborish",callback_data="send"),
             InlineKeyboardButton(text="Rad qilish",callback_data="nosend")]
        ],row_width=2
    )
    await message.answer(f"{xabar1} \n\nUshbu xabarni yuborasizmi?",reply_markup=inline_send)
    await state.finish()
    await state.set_state("yuborish")

@dp.callback_query_handler(lambda d:d.data=="send",state="*")
async def send_inline(query:types.CallbackQuery,state:FSMContext):
    yetkazilganlarr=0
    yetkazilmaganlar=0
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{inline_nom}", url=f"{linkk}")]
        ],
        row_width=2
    )
    cursor.execute("SELECT DISTINCT user_id FROM userid")
    user_ids = cursor.fetchall()

    for user_id in user_ids:
        try:
            await bot.send_message(user_id[0], xabar1,reply_markup=inline)
            yetkazilganlarr=+1
        except Exception as e:
            logging.error(f"Error sending message to user {user_id[0]}: {e}")
            yetkazilmaganlar+=1

    await query.message.answer(
        f"<b>Xabar foydalanuvchilarga muvaffaqiyatli yuborildi!</b>✅\n\n"
        f"🚀Yetkazildi : <b>{yetkazilganlarr}</b> ta\n"
        f"🛑Yetkazilmadi : <b>{yetkazilmaganlar}</b> ta",
        parse_mode="HTML"
    )
    await state.finish()

@dp.callback_query_handler(lambda u:u.data=="nosend",state="*")
async def nosend(call:types.CallbackQuery,state:FSMContext):
    await call.message.delete()
    await state.finish()
    await panel(call.message,state)


#Rasm inline xabar
    
@dp.message_handler(content_types=types.ContentType.PHOTO, state="send_message")
async def send_xabar(msg: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global photot
    photot = msg.photo[-1].file_id
    await msg.answer("<b>✍️Rasmning izohini qoldiring</b>", parse_mode="HTML",reply_markup=tugatish)
    await state.set_state('Rasm_izoh')

@dp.message_handler(state="Rasm_izoh")
async def rasm(msg: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global izohh
    izohh = msg.text

    await msg.answer("Inline tugma uchun link yuboring !",reply_markup=tugatish)
    await state.finish()
    
    await state.set_state("rasm_inline_link")

@dp.message_handler(state="rasm_inline_link")
async def rasm_inline(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global rasm_link
    rasm_link = message.text
    await message.answer("Inline tugma uchun nom kiriting !",reply_markup=tugatish)
    await state.finish()
    await state.set_state("rasminline_nom")

@dp.message_handler(state="rasminline_nom")
async def rasm_nom(message:types.Message,state:FSMContext):
    global rasm_nomi
    rasm_nomi = message.text
    yubor = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{rasm_nomi}",url=f"{rasm_link}")],
            [InlineKeyboardButton(text="Yuborish", callback_data="raketaa"),
             InlineKeyboardButton(text="Rad qilish", callback_data="uchma")]
        ], row_width=2
    )
    await message.answer_photo(photo=photot, caption=f"{izohh} \n\n Ushbu xabarni yuborasizmi? ",reply_markup=yubor)
    await state.finish()
    await state.set_state("jonatish")

@dp.callback_query_handler(lambda c: c.data == "raketaa", state="*")
async def izoh_pho(call: types.CallbackQuery, state: FSMContext):
    bordi = 0
    bormadi = 0
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{rasm_nomi}", url=f"{rasm_link}")]
        ],
        row_width=2
    )

    cursor.execute("SELECT DISTINCT user_id FROM userid")
    user_ids = cursor.fetchall()

    for user_id in user_ids:
        try:
            await bot.send_photo(user_id[0], photo=photot, caption=izohh, reply_markup=inline)
            bordi += 1
        except Exception as e:
            logging.error(f"Error sending message to user {user_id[0]}: {e}")
            bormadi += 1

    await call.message.answer(f"<b>Xabar foydalanuvchilarga muvaffaqiyatli yuborildi!</b>✅\n\n"
                              f"🚀Yetkazildi : <b>{bordi}</b> ta\n🛑Yetkazilmadi : <b>{bormadi}</b> ta",
                              parse_mode="HTML")

    await state.finish()

@dp.callback_query_handler(lambda u:u.data=="uchma",state="*")
async def uchma(call:types.CallbackQuery,state:FSMContext):
    await call.message.delete()
    await state.finish()
    await panel(call.message,state)

#Tugatish
    

#Video xabar inline
    
@dp.message_handler(content_types=types.ContentType.VIDEO, state="send_message")
async def send_xabar_video(msg: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global videop
    videop = msg.video.file_id
    await msg.answer("<b>✍️Videoning izohini qoldiring</b>", parse_mode="HTML",reply_markup=tugatish)
    await state.set_state('Video_izoh')

@dp.message_handler(state="Video_izoh")
async def video(msg: types.Message, state: FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global v_izohh
    v_izohh = msg.text

    await msg.answer("Inline tugma uchun link yuboring !",reply_markup=tugatish)
    await state.finish()
    
    await state.set_state("video_inline_link")

@dp.message_handler(state="video_inline_link")
async def video_inline(message:types.Message,state:FSMContext):
    tugatish = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Tugatish",callback_data="tugat")]
        ],row_width=2
    )
    global video_link
    video_link = message.text
    await message.answer("Inline tugma uchun nom kiriting !",reply_markup=tugatish)
    await state.finish()
    await state.set_state("videoinline_nom")

@dp.message_handler(state="videoinline_nom")
async def rasm_nom(message:types.Message,state:FSMContext):
    global video_nomi
    video_nomi = message.text
    yubor = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{video_nomi}",url=f"{video_link}")],
            [InlineKeyboardButton(text="Yuborish", callback_data="raketaaa"),
             InlineKeyboardButton(text="Rad qilish", callback_data="uchmaaa")]
        ], row_width=2
    )
    await message.answer_video(video=videop, caption=f"{v_izohh} \n\n Ushbu xabarni yuborasizmi? ",reply_markup=yubor)
    await state.finish()
    await state.set_state("jonatish2")

@dp.callback_query_handler(lambda c: c.data == "raketaaa", state="*")
async def izoh_vid(call: types.CallbackQuery, state: FSMContext):
    bordi = 0
    bormadi = 0
    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{video_nomi}", url=f"{video_link}")]
        ],
        row_width=2
    )

    cursor.execute("SELECT DISTINCT user_id FROM userid")
    user_ids = cursor.fetchall()

    for user_id in user_ids:
        try:
            await bot.send_video(user_id[0], video=videop, caption=v_izohh, reply_markup=inline)
            bordi += 1
        except Exception as e:
            logging.error(f"Error sending message to user {user_id[0]}: {e}")
            bormadi += 1

    await call.message.answer(f"<b>Xabar foydalanuvchilarga muvaffaqiyatli yuborildi!</b>✅\n\n"
                              f"🚀Yetkazildi : <b>{bordi}</b> ta\n🛑Yetkazilmadi : <b>{bormadi}</b> ta",
                              parse_mode="HTML")

    await state.finish()

@dp.callback_query_handler(lambda t:t.data=="tugat",state="*")
async def tugat(query:types.CallbackQuery,state:FSMContext):
    await query.message.delete()
    await state.finish()


@dp.callback_query_handler(lambda u:u.data=="uchmaaa",state="*")
async def uchma(call:types.CallbackQuery,state:FSMContext):
    await call.message.delete()
    await state.finish()
    await panel(call.message,state)




@dp.message_handler(text='📑Users', state="*")
async def export_users_command(message: types.Message, state: FSMContext):

    await export_users()
    with open('user_ids.txt', 'rb') as file:
        await message.answer_document(file)
        await state.finish()

@dp.message_handler(text='📑Baza', state="*")
async def export_db_command(message: types.Message, state: FSMContext):
    # Bazaning asl faylini nusxalash
    db_file_path = 'netflixkino.db'  # Bazangizning yo'li
    backup_db_path = 'database_backup.db'  # Nusxasi saqlanadigan fayl nomi

    # Faylni nusxalash
    shutil.copy(db_file_path, backup_db_path)

    # Faylni yuborish
    with open(backup_db_path, 'rb') as file:
        await message.answer_document(file)

    # Holatni yakunlash
    await state.finish()





@dp.message_handler(commands=["start"], state="*")
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name_full = message.from_user.full_name
    movie_name=None

    # Bazaga ulanish va foydalanuvchini tekshirish
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Foydalanuvchi bazada bormi yoki yo'qmi tekshirish
        cursor.execute("SELECT COUNT(*) FROM userid WHERE user_id = ?", (user_id,))
        user_exists = cursor.fetchone()[0]

        if user_exists == 0:  # Foydalanuvchi bazada yo'q bo'lsa
            # Foydalanuvchini bazaga qo'shish
            cursor.execute("INSERT INTO userid (user_id) VALUES (?)", (user_id,))
            conn.commit()

            # Jami foydalanuvchilar sonini olish
            cursor.execute("SELECT COUNT(*) FROM userid")
            user_count = cursor.fetchone()[0]

            # Telegram kanalga xabar yuborish
            channel_id = '-1002461777795'  # Kanalning ID
            message_text = f"<b>Yangi foydalanuvchi:</b>\n1.Ism:<i>{user_name_full}</i>\n2.Profil: tg://user?id={user_id}\n3.Jami Foydalanuvchi: {user_count}"

            try:
                await bot.send_message(channel_id, message_text, parse_mode="HTML")
            except aiogram.utils.exceptions.CantParseEntities as e:
                pass
        else:
            pass
                
        # Agar komanda bilan birga kod berilgan bo'lsa
        if " " in message.text:
            movie_name = message.text.split(" ", 1)[1].strip().lower()
            cursor.execute(
                '''SELECT name, description, video_file_id, movie_code, download_count 
                FROM movies 
                WHERE LOWER(name) LIKE ? OR movie_code LIKE ?''',
                ('%' + movie_name + '%', '%' + movie_name + '%')
            )
            movie_data = cursor.fetchone()

        # Kanal obunasini tekshirish
        cursor.execute("SELECT channel_id, channel_url FROM channel")
        channels = cursor.fetchall()

    # Kanallarni tekshirish
    unsubscribed_channels = []
    for channel_id, _ in channels:
        status = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if status.status == "left":
            unsubscribed_channels.append(channel_id)

    if unsubscribed_channels:
        # Agar obuna bo'lmagan kanallar bo'lsa
        keyboard = InlineKeyboardMarkup(row_width=1)
        for _, channel_url in channels:
            keyboard.add(InlineKeyboardButton(text="➕ Obuna bo'lish", url=channel_url))
        keyboard.add(InlineKeyboardButton(text="Instagram Sahifamiz",url="https://www.instagram.com/netflix_kinolar"))
        keyboard.add(InlineKeyboardButton(text="Tekshirish ✅", url="https://t.me/netflix_kinolarbot?start=True" ))
        
        await message.reply(
            "``` Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:```⬇️",
            reply_markup=keyboard,
            parse_mode='MARKDOWN'
        )
        return  # Davom ettirmaslik

    # Agar obunalar tekshirilgan bo'lsa
    if movie_name and movie_data:
        name, description, video_file_id, movie_code, download_count = movie_data

        # Yuklashlar sonini yangilash (bazaga)
        new_download_count = download_count + 1
        with sqlite3.connect('netflixkino.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE movies SET download_count = ? WHERE movie_code = ?",
                (new_download_count, movie_code)
            )
            conn.commit()

        # Inline tugma
        inline = InlineKeyboardMarkup(
            inline_keyboard=[ 
                [
                    InlineKeyboardButton(
                        text="Do'stlarga yuborish",
                        switch_inline_query=f"{movie_code}"  # movie_code ni yuborish
                    ),
                    InlineKeyboardButton(
                        text="📥 Saqlash", callback_data=f"save_movie:{movie_code}"  # Callbackda movie_codeni berish
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛒 Saqlanganlar", callback_data="kor_kino"
                    )
                    
                ],
                [
                    InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat="")
                ]
            ],
            row_width=2
        )

        # Video yuborish
        await bot.send_video(
            chat_id=message.chat.id,
            video=video_file_id,
            caption=f"<b>{name}</b>\n\n{description}\n👁:<b>{new_download_count}</b>",
            reply_markup=inline,
            parse_mode="HTML"
        )
    else:
        
        # Obunadan o'tganlar uchun asosiy menyu
        kanalim = InlineKeyboardMarkup(
             inline_keyboard=[
                [InlineKeyboardButton(text="🎥 Kinolar | Kodli", url="https://t.me/netflixkinolar")],
                [InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat=""),
                 InlineKeyboardButton(text="🔥 Top filmlar | 10", callback_data="top_movies")],
                [InlineKeyboardButton(
                        text="🛒 Saqlanganlar", callback_data="kor_kino"
                    ),
                    InlineKeyboardButton(
                        text="🎲Random", callback_data="random")
                        ],
                [InlineKeyboardButton("Kino so'rash | Savol yoki Taklif ", callback_data=f"send_suggestion_")]  
            ],row_width=2
        )
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"Assalomu alaykum [{user_name_full}](tg://user?id={user_id})\n``` Xush kelibsiz!😊 ```\n\nBotdan foydalanishingiz mumkin! \n``` Kerakli kino kodini kiriting yoki Qidirish tugmasi orqali kinolarni qidiring!```",
            parse_mode="MARKDOWN",
            reply_markup=kanalim
        )

@dp.callback_query_handler(lambda c: c.data == "random")
async def send_random_movie(callback_query: types.CallbackQuery):
    # Establish database connection and create cursor
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Select a random movie from the database
        cursor.execute("SELECT name, description, video_file_id, movie_code, download_count FROM movies ORDER BY RANDOM() LIMIT 1")
        movie = cursor.fetchone()

        if movie:
            name, description, video_file_id, movie_code, download_count = movie

            # Increment the download count
            new_download_count = download_count + 1
            cursor.execute(
                "UPDATE movies SET download_count = ? WHERE movie_code = ?",
                (new_download_count, movie_code)
            )
            conn.commit()

            # Inline button markup
            inline = InlineKeyboardMarkup(
                inline_keyboard=[ 
                    [
                        InlineKeyboardButton(
                            text="Do'stlarga yuborish",
                            switch_inline_query=f"{movie_code}"  # movie_code ni yuborish
                        ),
                        InlineKeyboardButton(
                            text="📥 Saqlash", callback_data=f"save_movie:{movie_code}"  # Callbackda movie_codeni berish
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🛒 Saqlanganlar", callback_data="kor_kino"
                        )
                    ],
                    [
                        InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat=""),
                        InlineKeyboardButton(text="Keyingisi⏩", callback_data="rand2")
                    ]
                ],
                row_width=2
            )

            # Delete the previous message before sending the new one
            await bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id
            )

            # Send the video with updated download count
            if video_file_id:
                await bot.send_video(
                    chat_id=callback_query.from_user.id,
                    caption=f"🎬 **{name}**\n\n📖 {description}\n👁️: <b>{new_download_count}</b>",
                    video=video_file_id,
                    reply_markup=inline,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=callback_query.from_user.id,
                    text=f"🎬 **{name}**\n\n📖 {description}\n👁️: <b>{new_download_count}</b>",
                    reply_markup=inline,
                    parse_mode="HTML"
                )
        else:
            await bot.send_message(
                chat_id=callback_query.from_user.id,
                text="Hozircha kinolar bazada yo'q."
            )

    # Acknowledge callback query
    await callback_query.answer()



@dp.callback_query_handler(lambda c: c.data == "rand2")
async def send_random_movie(callback_query: types.CallbackQuery):
    # Establish database connection and create cursor
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Select a random movie from the database
        cursor.execute("SELECT name, description, video_file_id, movie_code, download_count FROM movies ORDER BY RANDOM() LIMIT 1")
        movie = cursor.fetchone()

        if movie:
            name, description, video_file_id, movie_code, download_count = movie

            # Increment the download count
            new_download_count = download_count + 1
            cursor.execute(
                "UPDATE movies SET download_count = ? WHERE movie_code = ?",
                (new_download_count, movie_code)
            )
            conn.commit()

            # Inline button markup
            inline = InlineKeyboardMarkup(
                inline_keyboard=[ 
                    [
                        InlineKeyboardButton(
                            text="Do'stlarga yuborish",
                            switch_inline_query=f"{movie_code}"  # movie_code ni yuborish
                        ),
                        InlineKeyboardButton(
                            text="📥 Saqlash", callback_data=f"save_movie:{movie_code}"  # Callbackda movie_codeni berish
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🛒 Saqlanganlar", callback_data="kor_kino"
                        )
                    ],
                    [
                        InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat=""),
                        InlineKeyboardButton(text="Keyingisi⏩", callback_data="rand2")
                    ]
                ],
                row_width=2
            )

            # Delete the previous message before sending the new one
            await bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id
            )

            # Send the video with updated download count
            if video_file_id:
                await bot.send_video(
                    chat_id=callback_query.message.chat.id,
                    video=video_file_id,
                    caption=f"🎬 **{name}**\n\n📖 {description}\n👁️: <b>{new_download_count}</b>",
                    reply_markup=inline,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=callback_query.message.chat.id,
                    text=f"🎬 **{name}**\n\n📖 {description}\n👁️: <b>{new_download_count}</b>",
                    reply_markup=inline,
                    parse_mode="HTML"
                )
        else:
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text="Hozircha kinolar bazada yo'q."
            )

    # Acknowledge callback query
    await callback_query.answer()




import uuid

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import BotBlocked

# Admin's user ID for direct communication (replace with actual admin ID)
ADMIN_USER_ID = 1996936737  # Example, replace with your admin's user ID
CHANNEL_ID = "-1002295487802"  # Replace with your actual channel ID

# FSM state for handling suggestions
class SuggestionStates(StatesGroup):
    waiting_for_suggestion = State()  # Waiting for the user's suggestion

# Handle "Savol yoki Taklif Yuborish" button click
@dp.callback_query_handler(lambda call: call.data=="send_suggestion_")
async def ask_suggestion(call: types.CallbackQuery,state:FSMContext):
    savekb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌Bekor qilish", callback_data="bekorx")]
        ],row_width=2
    )
    
    await call.message.edit_text("Iltimos, savol yoki taklifingizni yozing:",reply_markup=savekb)
    
    await SuggestionStates.waiting_for_suggestion.set()
    

@dp.callback_query_handler(lambda c: c.data == "bekorx",state="*")
async def cancel_x(callback_query: types.CallbackQuery,state:FSMContext):
    
    kanalim = InlineKeyboardMarkup(
             inline_keyboard=[
                [InlineKeyboardButton(text="🎥 Kinolar | Kodli", url="https://t.me/netflixkinolar")],
                [InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat=""),
                 InlineKeyboardButton(text="🔥 Top filmlar | 10", callback_data="top_movies")],
                [InlineKeyboardButton(
                        text="🛒 Saqlanganlar", callback_data="kor_kino"
                    ),
                    InlineKeyboardButton(
                        text="🎲Random", callback_data="random")
                        ],
                [InlineKeyboardButton("Kino so'rash | Savol yoki Taklif ", callback_data=f"send_suggestion_")]  
            ],row_width=2
        )
   
    await callback_query.message.edit_text("Kino kerakmi? \n``` Kerakli kino kodini kiriting yoki Qidirish tugmasi orqali kinolarni qidiring!```",parse_mode="MARKDOWN",reply_markup=kanalim)
    await state.finish()
# Handle the user's suggestion and send it to the admin bot
@dp.message_handler(state=SuggestionStates.waiting_for_suggestion)
async def handle_suggestion(message: types.Message, state: FSMContext):
    botga = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙Bo'tga o'tish", url="https://t.me/netflix_kinolarbot")]
        ],row_width=2
    )
    user_full = message.from_user.full_name
    savekb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙Bosh sahifa", callback_data="cancel")]
        ],row_width=2
    )
    suggestion_text = message.text  # Get the user's suggestion
     # Generate a random suggestion ID
    user_id = message.from_user.id  # Get the user's user_id

    # Send the suggestion to the admin bot
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,  # Send user_id to the channel
            text=f"Foydalanuvchidan xabar\nID:``` {user_id} ```\nXabar:``` {suggestion_text} ```\nProfil\n[{user_full}](tg://user?id={user_id})",parse_mode="Markdown",reply_markup=botga
        )
        await message.answer("Xabaringiz adminga yuborildi. ``` Javobni kuting... ```",parse_mode="Markdown",reply_markup=savekb)
        await state.finish()
    except BotBlocked:
        await message.answer("Foydalanuvchi botni bloklagan.")
    except Exception as e:
        print(f"Error: {e}")
        await message.answer("Xatolik yuz berdi, iltimos qaytadan urinib ko‘ring.")

    await state.finish()

# 
    
async def export_users():
    conn = sqlite3.connect('netflixkino.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM userid')
    user_ids = cursor.fetchall()

    existing_user_ids = set()
    try:
        with open('user_ids.txt', 'r') as existing_file:
            existing_user_ids = set(map(int, existing_file.read().split()))
    except FileNotFoundError:
        pass

    new_user_ids = [str(user_id[0]) for user_id in user_ids if user_id[0] not in existing_user_ids]

    with open('user_ids.txt', 'a') as file:
        file.write('\n'.join(new_user_ids) + '\n')

    conn.close()



import aiogram.utils
@dp.message_handler(lambda message: message.text.isdigit(), state="*")
async def check_movie_code(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    movie_code = msg.text

    # Bazaga ulanish
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Kanal obunalarini tekshirish
        cursor.execute("SELECT channel_id, channel_url FROM channel")
        channels = cursor.fetchall()

    unsubscribed_channels = []
    for channel_id, _ in channels:
        status = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if status.status == "left":
            unsubscribed_channels.append(channel_id)

    if unsubscribed_channels:
        # Obuna bo'lmagan kanallar uchun tugmalarni yaratish
        keyboard = InlineKeyboardMarkup(row_width=1)
        for _, channel_url in channels:
            keyboard.add(InlineKeyboardButton(text="➕ Obuna bo'lish", url=channel_url))
        keyboard.add(InlineKeyboardButton(text="Instagram Sahifamiz",url="https://www.instagram.com/netflix_kinolar"))
        keyboard.add(InlineKeyboardButton(text="Tekshirish ✅", url="https://t.me/netflix_kinolarbot?start=True"))

        await msg.reply(
            "``` Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:```⬇️",
            reply_markup=keyboard,
            parse_mode='MARKDOWN'
        )
        await state.finish()
        return  # Davom ettirmaslik

    # Kino ma'lumotlarini bazadan olish
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, video_file_id, download_count FROM movies WHERE movie_code = ?", (movie_code,))
        movie_data = cursor.fetchone()

    if not movie_data:
        tugmain = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton("Kino so'rash | Savol yoki Taklif ", callback_data=f"send_suggestion_")]
            ],row_width=2
        )
        await msg.answer("❌ Bunday kodli kino hozircha mavjud emas",reply_markup=tugmain)
        return

    name, description, video_file_id, download_count = movie_data

    if not video_file_id:
        await msg.answer("❌ Video fayli topilmadi yoki noto'g'ri ID")
        return

    try:
        # Yuklab olish hisobini yangilash (bazada)
        new_download_count = download_count + 1
        with sqlite3.connect('netflixkino.db') as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE movies SET download_count = ? WHERE movie_code = ?", (new_download_count, movie_code))
            conn.commit()

        # Inline tugmalarni yangilash
        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Do'stlarga yuborish",
                        switch_inline_query=f"{movie_code}"  # movie_code ni yuborish
                    ),
                    InlineKeyboardButton(
                        text="📥 Saqlash", callback_data=f"save_movie:{movie_code}"  # Callbackda movie_codeni berish
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛒 Saqlanganlar", callback_data="kor_kino"
                    )
                    
                ],
                [
                    InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat="")
                ]
            ],
            row_width=2
        )

        # Videoni yuborish
        await bot.send_video(
            chat_id=msg.chat.id,
            video=video_file_id,
            caption=f"{name}\n\n{description}\n👁:<b>{new_download_count}</b>",
            reply_markup=inline,
            parse_mode="HTML"
        )
        
    except aiogram.utils.exceptions.WrongFileIdentifier:
        await msg.answer("❌ Noto'g'ri video fayli yoki ID. Iltimos, ma'lumotlarni yangilang.")





@dp.callback_query_handler(lambda c: c.data == "top_movies")
async def show_top_movies(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    savekb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙Bosh sahifa", callback_data="backs")]
        ],row_width=2
    )

    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Eng ko'p yuklangan 10 ta kinoni olish
        cursor.execute("""
            SELECT movie_code, name, download_count 
            FROM movies 
            ORDER BY download_count DESC 
            LIMIT 10
        """)
        top_movies = cursor.fetchall()

    if not top_movies:
        await callback_query.message.edit_text("Hozircha top filmlar mavjud emas! 🔥",reply_markup=savekb)
        return

    # Top filmlar ro'yxatini yaratish
    movie_list = "\n".join([f"{idx + 1}. {movie[1]} - 👁 {movie[2]}" for idx, movie in enumerate(top_movies)])

    # Inline tugmalarni yaratish
    inline = InlineKeyboardMarkup(row_width=5)
    for idx, movie in enumerate(top_movies):
        inline.add(InlineKeyboardButton(text=str(idx + 1), callback_data=f"movie__{movie[0]}"))
    inline.add(InlineKeyboardButton(text="🔙Bosh sahifa",callback_data="backs"))

    # Xabarni yangilash
    await callback_query.message.edit_text(
        f"🔥 Eng ko'p yuklangan filmlar:\n\n{movie_list}",
        reply_markup=inline
    )


@dp.callback_query_handler(lambda c:c.data=="backs")
async def backs(calmes:types.CallbackQuery):
    
    kanalim = InlineKeyboardMarkup(
             inline_keyboard=[
                [InlineKeyboardButton(text="🎥 Kinolar | Kodli", url="https://t.me/netflixkinolar")],
                [InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat=""),
                 InlineKeyboardButton(text="🔥 Top filmlar | 10", callback_data="top_movies")],
                [InlineKeyboardButton(
                        text="🛒 Saqlanganlar", callback_data="kor_kino"
                    ),
                    InlineKeyboardButton(
                        text="🎲Random", callback_data="random")
                        ],
                [InlineKeyboardButton("Kino so'rash | Savol yoki Taklif ", callback_data=f"send_suggestion_")]  
            ],row_width=2
        )
    await calmes.message.edit_text("Kino kerakmi? \n``` Kerakli kino kodini kiriting yoki Qidirish tugmasi orqali kinolarni qidiring!```",parse_mode="MARKDOWN",reply_markup=kanalim)

@dp.callback_query_handler(lambda c: c.data.startswith("movie__"))
async def send_movie_from_top(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    movie_code = callback_query.data.split("__")[1]  # Movie code ni ajratib olish
    inline = InlineKeyboardMarkup(
            inline_keyboard=[ 
                [
                    InlineKeyboardButton(
                        text="Do'stlarga yuborish",
                        switch_inline_query=f"{movie_code}"  # movie_code ni yuborish
                    ),
                    InlineKeyboardButton(
                        text="📥 Saqlash", callback_data=f"save_movie:{movie_code}"  # Callbackda movie_codeni berish
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛒 Saqlanganlar", callback_data="kor_kino"
                    ),
                    
                ],
                [InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat="")]
            ],
            row_width=2
        )

    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Kino ma'lumotlarini olish
        cursor.execute("SELECT name, description, video_file_id, download_count FROM movies WHERE movie_code = ?", (movie_code,))
        movie_data = cursor.fetchone()

    if not movie_data:
        await callback_query.answer("❌ Kino topilmadi!", show_alert=True)
        return

    name, description, video_file_id, download_count = movie_data

    # Yuklashlar sonini yangilash
    new_download_count = download_count + 1
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE movies SET download_count = ? WHERE movie_code = ?", (new_download_count, movie_code))
        conn.commit()

    # Videoni yuborish
    try:
        await bot.send_video(
            chat_id=callback_query.message.chat.id,
            video=video_file_id,
            caption=f"<b>{name}</b>\n\n{description}\n👁:<b>{new_download_count}</b>",
            reply_markup=inline,
            parse_mode="HTML"
        )
        
    except aiogram.utils.exceptions.WrongFileIdentifier:
        await callback_query.answer("❌ Noto'g'ri video fayli yoki ID!", show_alert=True)



@dp.callback_query_handler(lambda c: c.data.startswith("save_movie:"))
async def save_movie(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Callback data'dan movie_code ni olish
    movie_code = callback_query.data.split(":")[1]  # "save_movie:<movie_code>" dan movie_code ni ajratib olish

    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Kino allaqachon saqlanganligini tekshirish
        cursor.execute(
            "SELECT COUNT(*) FROM saved_movies WHERE user_id = ? AND movie_code = ?",
            (user_id, movie_code)
        )
        is_saved = cursor.fetchone()[0] > 0

        if is_saved:
            # Agar kino allaqachon saqlangan bo'lsa, foydalanuvchini xabardor qilish
            await callback_query.answer("Bu kino allaqachon saqlangan!", show_alert=True)
        else:
            # Saqlanmagan bo'lsa, bazaga qo'shish
            cursor.execute(
                "INSERT INTO saved_movies (user_id, movie_code) VALUES (?, ?)",
                (user_id, movie_code)
            )
            conn.commit()

            await callback_query.answer("✅Kino muvaffaqiyatli saqlandi!", show_alert=True)

# "Saqlanganlar" tugmasi uchun callback handler
@dp.callback_query_handler(lambda c: c.data == "kor_kino")
async def show_saved_movies(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    savekb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙Bosh sahifa", callback_data="cancel")]
        ],row_width=2
    )
    # Fetch saved movies for the user
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT m.name, m.description, m.video_file_id, m.movie_code "
            "FROM saved_movies s "
            "JOIN movies m ON s.movie_code = m.movie_code "
            "WHERE s.user_id = ?",
            (user_id,)
        )
        saved_movies = cursor.fetchall()

    if not saved_movies:
        try:
            await callback_query.message.edit_text("❌ Siz hali kino saqlamadingiz.",reply_markup=savekb)
        except aiogram.utils.exceptions.BadRequest as e:
            if "message to edit" in str(e):
                await callback_query.answer("Xatolik: Xabarni tahrir qilib bo'lmaydi, yangi xabar yuboriladi.")
                await callback_query.message.reply("❌ Siz hali kino saqlamadingiz.",reply_markup=savekb)
        return

    # Prepare the list of movies with numbers
    movie_list = "\n".join(
        [f"{idx + 1}. {name}" for idx, (name, _, _, _) in enumerate(saved_movies)]
    )

    # Prepare inline buttons for selecting movies
    keyboard = InlineKeyboardMarkup(row_width=5)
    for idx, (_, _, _, movie_code) in enumerate(saved_movies):
        keyboard.insert(InlineKeyboardButton(text=str(idx + 1), callback_data=f"select_movie:{movie_code}"))

    # Add a cancel button
    keyboard.add(InlineKeyboardButton(text="🔙Bosh sahifa", callback_data="cancel"))
    keyboard.add(InlineKeyboardButton(text="Tozalash 🗑", callback_data="clear_saved_movies"))

    try:
        # Send or edit the message
        await callback_query.message.edit_text(
            f"🎥 Saqlangan kinolar:\n\n{movie_list}\n\nRaqamni tanlang:",
            reply_markup=keyboard
        )
    except aiogram.utils.exceptions.BadRequest as e:
        if "message to edit" in str(e):
            # Send a new message if editing fails
            await callback_query.message.reply(
                f"🎥 Saqlangan kinolar:\n\n{movie_list}\n\nRaqamni tanlang:",
                reply_markup=keyboard
            )

# Callback handler for selecting a movie by number
@dp.callback_query_handler(lambda c: c.data.startswith("select_movie:"))
async def send_selected_movie(callback_query: types.CallbackQuery):
    movie_code = callback_query.data.split(":")[1]  # Extract movie code
    inline = InlineKeyboardMarkup(
        inline_keyboard=[ 
            [
                InlineKeyboardButton(
                    text="Do'stlarga yuborish",
                    switch_inline_query=f"{movie_code}"  # movie_code ni yuborish
                ),
                InlineKeyboardButton(
                    text="📥 Saqlash", callback_data=f"save_movie:{movie_code}"  # Callbackda movie_codeni berish
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Saqlanganlar", callback_data="kor_kino"
                )
                
            ],
            [
                InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat="")
            ]
        ],
        row_width=2
    )

    # Fetch movie details from the database
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, video_file_id, download_count FROM movies WHERE movie_code = ?", (movie_code,))
        movie_data = cursor.fetchone()

    if not movie_data:
        await callback_query.answer("❌ Kino topilmadi yoki noto'g'ri ID.", show_alert=True)
        return

    name, description, video_file_id, download_count = movie_data

    if not video_file_id:
        await callback_query.answer("❌ Video fayli topilmadi yoki noto'g'ri ID.", show_alert=True)
        return

    description = description or "Tavsif mavjud emas."

    # Update download count (increase by 1)
    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE movies SET download_count = download_count + 1 WHERE movie_code = ?", (movie_code,))
        conn.commit()

    # Send the selected movie
    try:
        await bot.send_video(
            chat_id=callback_query.message.chat.id,
            video=video_file_id,
            caption=f"<b>{name}</b>\n\n{description}\n👁:<b>{download_count + 1}</b>",  # Show updated download count
            reply_markup=inline,
            parse_mode="HTML"
        )
        await callback_query.answer("✅ Kino yuborildi!")
    except aiogram.utils.exceptions.WrongFileIdentifier:
        await callback_query.answer("❌ Noto'g'ri video fayli yoki ID.", show_alert=True)


@dp.callback_query_handler(lambda c: c.data == "clear_saved_movies")
async def clear_saved_movies(callback_query: types.CallbackQuery):
    savekb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙Bosh sahifa", callback_data="cancel")]
        ],row_width=2
    )
    user_id = callback_query.from_user.id

    with sqlite3.connect('netflixkino.db') as conn:
        cursor = conn.cursor()

        # Foydalanuvchining barcha saqlangan kinolarini o'chirish
        cursor.execute("DELETE FROM saved_movies WHERE user_id = ?", (user_id,))
        conn.commit()

    await callback_query.answer("Barcha saqlangan kinolar o'chirildi!", show_alert=True)

    # Foydalanuvchiga xabar yuborish
    await callback_query.message.edit_text(
        "Saqlangan kinolar ro'yxati tozalandi! 🎉",
        reply_markup=savekb
    )

# Cancel button handler
@dp.callback_query_handler(lambda c: c.data == "cancel")
async def cancel_action(callback_query: types.CallbackQuery,state:FSMContext):
    
    kanalim = InlineKeyboardMarkup(
             inline_keyboard=[
                [InlineKeyboardButton(text="🎥 Kinolar | Kodli", url="https://t.me/netflixkinolar")],
                [InlineKeyboardButton(text="🔍Kino qidirish...", switch_inline_query_current_chat=""),
                 InlineKeyboardButton(text="🔥 Top filmlar | 10", callback_data="top_movies")],
                [InlineKeyboardButton(
                        text="🛒 Saqlanganlar", callback_data="kor_kino"
                    ),
                    InlineKeyboardButton(
                        text="🎲Random", callback_data="random")
                        ],
                [InlineKeyboardButton("Kino so'rash | Savol yoki Taklif ", callback_data=f"send_suggestion_")]  
            ],row_width=2
        )
   
    await callback_query.message.edit_text("Kino kerakmi? \n``` Kerakli kino kodini kiriting yoki Qidirish tugmasi orqali kinolarni qidiring!```",parse_mode="MARKDOWN",reply_markup=kanalim)
    await state.finish()

if __name__ == '__main__':
    # dp.middleware.setup(LoggingMiddleware())  
    executor.start_polling(dp, skip_updates=True)
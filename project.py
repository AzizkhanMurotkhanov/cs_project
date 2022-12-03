from aiogram import types, executor, Dispatcher, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime
import json
import re


class Ask_cus(StatesGroup):
    phone_number = State()
    car_type = State()
    customer_name = State()


class Add_day(StatesGroup):
    day = State()
    time = State()


class Ask_tec(StatesGroup):
    name = State()
    phone = State()
    telegram = State()
    id = State()


def buttons(args: list):
    markup = InlineKeyboardMarkup()
    for text in args:
        button = InlineKeyboardButton(text=text, callback_data=text)
        markup.add(button)
    return markup


def update_datafile(filename: str):
    if filename == 'users':
        with open(f'users.json', 'w', encoding='utf8') as file:
            json.dump(users, file)
    elif filename == 'admins':
        with open(f'admins.json', 'w', encoding='utf8') as file:
            json.dump(admins, file)


def get_datafile(file_name: str):
    with open(file_name, 'r', encoding='utf8') as file:
        temp = dict(json.load(file))
    return temp


async def get_reservation(num: int, call: types.callback_query):
    chat_id = str(call.message.chat.id)
    ln = users[chat_id]['language']
    if not num >= len(users):
        id = list(users.keys())[num]
        if all([users[id].get('service', ''), not users[id].get('taken_by', ''), users[id].get('customer_name', '') != text_manipulation(call.message.text).get('Client', '')]):
            text = ''
            for i in range(5):
                text += f'{replies[ln]["Cus_info"][i]}: {list(users[id].values())[i + 1]}\n'
            text += f'{replies[ln]["Cus_info"][5]}: {id}'
            await bot.edit_message_text(text=text, chat_id=chat_id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Tec_res_choices']))
        else:
            await get_reservation(num + 1, call)
    else:
        await bot.edit_message_text(text=replies[ln]['Tec_took_res'][2], chat_id=chat_id, message_id=call.message.message_id)
        await bot.send_message(chat_id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Tec_choices']))


def text_manipulation(text: str):
    temp = {}
    text = text.split('\n')
    if len(text) > 1:
        for row in text:
            temp2 = row.split(': ')
            temp[temp2[0]] = temp2[1]
    return temp


async def check():
    for id in users:
        user_date = users[id].get('date', None)
        if user_date:
            user_date = datetime.datetime.strptime(user_date, '%d %b %Y %H:%M')
            ln = users[id]['language']
            if datetime.datetime.now() - datetime.timedelta(hours=6) > user_date:
                await bot.send_message(id, replies[ln]['Cus_notes'][0])
                users[id] = {**users[id], **{'service': None, 'date': None, 'taken_by': None, 'notified': False}}
                update_datafile('users')
            elif datetime.datetime.now() + datetime.timedelta(hours=24) > user_date and users[id].get('taken_by', None) and not users[id].get('notified', None):
                await bot.send_message(id, replies[ln]['Cus_notes'][1])
                users[id] = {**users[id], **{'notified': True}}
                update_datafile('users')


token = ''
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
replies = get_datafile('replies.json')
users = get_datafile('users.json')
admins = get_datafile('admins.json')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await check()
    text = 'Chooze a language\nВыберите язык'
    await bot.send_message(message.chat.id, text, reply_markup=buttons(replies.keys()))


@dp.callback_query_handler(lambda c: c.data in replies)
async def chose_lang(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    ln = call.data
    await bot.edit_message_text(text=replies[ln]['Questions'][0], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Who']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Who'][0] for i in replies])
async def user_is_customer(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = [replies[i]['Questions'][0] for i in replies].index(call.message.text)
    ln = list(replies.keys())[ln]
    if id in users:
        users[id]['language'] = ln
        await bot.edit_message_text(text=replies[ln]['Questions'][1], chat_id=id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Cus_choices']))
    else:
        users[id] = {}
        users[id]['language'] = ln
        await bot.edit_message_text(text=replies[ln]['Cus_reg'][0], chat_id=id, message_id=call.message.message_id)
        await Ask_cus.customer_name.set()


@dp.message_handler(state=Ask_cus.customer_name)
async def customer_name_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = users[id]['language']
    if any(map(str.isdigit, message.text)):
        await bot.send_message(id, replies[ln]['Cus_reg'][0], reply_to_message_id=message.message_id)
        return
    users[id]['customer_name'] = message.text
    await bot.send_message(id, replies[ln]['Cus_reg'][1])
    await Ask_cus.phone_number.set()


@dp.message_handler(state=Ask_cus.phone_number)
async def phone_number_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = users[id]['language']
    if not all(map(lambda x: x in '+0123456789', message.text)):
        await bot.send_message(id, replies[ln]['Cus_reg'][1], reply_to_message_id=message.message_id)
        return
    users[id]['phone_number'] = message.text
    await bot.send_message(id, replies[ln]['Cus_reg'][2])
    await Ask_cus.car_type.set()


@dp.message_handler(state=Ask_cus.car_type)
async def car_type_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = users[id]['language']
    users[id]['car_type'] = message.text
    update_datafile('users')
    await state.finish()
    await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Cus_choices']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Cus_choices'][0] for i in replies])
async def list_of_services(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    ln = users[str(call.message.chat.id)]['language']
    await bot.edit_message_text(text=replies[ln]['Cus_captions'][0], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Cus_services']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Cus_choices'][1] for i in replies])
async def get_contact_details(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = users[id]['language']
    for tec in admins:
        await bot.send_message(id, f'{replies[ln]["Cus_captions"][2]}: {admins[tec]["name"]}\n{replies[ln]["Cus_captions"][3]}: {admins[tec]["phone"]}\nTelegram: {admins[tec]["telegram"]}')
    await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Cus_choices']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Cus_choices'][2] for i in replies])
async def reservation_details(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = users[id]['language']
    user = users[id]
    if user.get('service', None) and user.get('date', None):
        await bot.edit_message_text(text=f'{replies[ln]["Cus_captions"][4]}: {user["service"]}\n{replies[ln]["Cus_captions"][5]}: {user["date"]}', chat_id=id, message_id=call.message.message_id)
    else:
        await bot.edit_message_text(text=replies[ln]["Cus_captions"][6], chat_id=id, message_id=call.message.message_id)
    await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Cus_choices']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Cus_choices'][3] for i in replies])
async def cancel_reservation(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    ln = users[str(call.message.chat.id)]['language']
    await bot.edit_message_text(text=replies[ln]['Questions'][2], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Sure']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Cus_choices'][4] for i in replies])
async def change_info(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    ln = users[str(call.message.chat.id)]['language']
    await bot.edit_message_text(text=replies[ln]['Cus_reg'][0], chat_id=call.message.chat.id, message_id=call.message.message_id)
    await Ask_cus.customer_name.set()


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Cus_choices'][-1] for i in replies])
async def done(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    await bot.edit_message_text(text=call.data, chat_id=call.message.chat.id, message_id=call.message.message_id)


@dp.callback_query_handler(lambda c: c.data in sum([replies[i]['Sure'] for i in replies], []))
async def is_customer_sure(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = users[id]['language']
    if call.data == replies[ln]['Sure'][0]:
        users[id] = {**users[id], **{'service': None, 'date': None, 'taken_by': None, 'notified': False}}
        update_datafile('users')
    await bot.edit_message_text(text=replies[ln]['Questions'][1], chat_id=id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Cus_choices']))


@dp.callback_query_handler(lambda c: c.data in sum([replies[i]['Cus_services'] for i in replies], []))
async def services(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = users[id]['language']
    users[id] = {**users[id], **{'service': call.data}}
    update_datafile('users')
    await bot.edit_message_text(text=replies[ln]['Cus_captions'][1], chat_id=id, message_id=call.message.message_id, reply_markup=buttons(sum([admins[i]['available'] for i in admins], [])))


@dp.callback_query_handler(lambda c: c.data in sum([admins[i]['available'] for i in admins], []))
async def chose_date(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    if call.message.text in [replies[i]['Cus_captions'][1] for i in replies]:
        ln = users[id]['language']
        users[id] = {**users[id], **{'date': call.data, 'taken_by': None, 'notified': False}}
        update_datafile('users')
        await bot.edit_message_text(text=replies[ln]['Cus_choices'][-1], chat_id=id, message_id=call.message.message_id)
        await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Cus_choices']))
    elif call.message.text in [replies[i]['Tec_captions'][1] for i in replies]:
        ln = admins[id]['language']
        admins[id]['available'].remove(call.data)
        update_datafile('admins')
        await bot.edit_message_text(text=replies[ln]['Tec_choices'][-1], chat_id=id, message_id=call.message.message_id)
        await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Tec_choices']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Who'][1] for i in replies])
async def user_is_technician(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    ln = [replies[i]['Questions'][0] for i in replies].index(call.message.text)
    ln = list(replies.keys())[ln]
    id = str(call.message.chat.id)
    if id in admins:
        admins[id]['language'] = ln
        await bot.edit_message_text(text=replies[ln]['Questions'][1], chat_id=id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Tec_choices']))
    else:
        await bot.edit_message_text(text=replies[ln]['Tec_captions'][0], chat_id=id, message_id=call.message.message_id)
        await bot.send_message(id, replies[ln]['Questions'][0], reply_markup=buttons(replies[ln]['Who']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Tec_choices'][0] for i in replies])
async def take_reservation(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    await get_reservation(0, call)


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Tec_choices'][1] for i in replies])
async def list_of_days(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = admins[id]['language']
    days = admins[id]['available']
    if days:
        temp = [f'{replies[ln]["Tec_days"][0]}:']
        temp += days
        await bot.edit_message_text(text='\n'.join(temp), chat_id=id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Tec_days'][1:]))
    else:
        await bot.edit_message_text(replies[ln]['Tec_captions'][2], chat_id=id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Tec_days'][1:]))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Tec_choices'][2] for i in replies])
async def add_tec(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = admins[id]['language']
    await bot.edit_message_text(replies[ln]['Tec_reg'][0], chat_id=id, message_id=call.message.message_id)
    await Ask_tec.name.set()


@dp.callback_query_handler(lambda c: c.data in sum([replies[i]['Tec_res_choices'] for i in replies], []))
async def res_choice(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = admins[id]['language']
    if call.data == replies[ln]['Tec_res_choices'][0]:
        text = text_manipulation(call.message.text)
        await bot.edit_message_text(text=f'{replies[ln]["Tec_took_res"][0]}: {text["Client"]}\n{text["Phone"]}', chat_id=id, message_id=call.message.message_id)
        await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Tec_choices']))
        users[text['Reservation id']] = {**users[text['Reservation id']], **{'taken_by': admins[id]['name'], 'notified': False}}
        update_datafile('users')
        cus_ln = users[text['Reservation id']]['language']
        await bot.send_message(int(text['Reservation id']), f'{replies[cus_ln]["Tec_took_res"][1]}: {users[text["Reservation id"]]["taken_by"]}')
    elif call.data == replies[ln]['Tec_res_choices'][1]:
        text = text_manipulation(call.message.text)
        temp = list(users.keys()).index(text['Reservation id'])
        await get_reservation(temp + 1, call)
    else:
        await bot.edit_message_text(text=replies[ln]['Questions'][1], chat_id=id, message_id=call.message.message_id, reply_markup=buttons(replies[ln]['Tec_choices']))


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Tec_days'][1] for i in replies])
async def add_day(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = admins[id]['language']
    await bot.edit_message_text(text=replies[ln]['Tec_add_date'][0], chat_id=id, message_id=call.message.message_id)
    await Add_day.day.set()


@dp.callback_query_handler(lambda c: c.data in [replies[i]['Tec_days'][2] for i in replies])
async def remove_day(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    id = str(call.message.chat.id)
    ln = admins[id]['language']
    await bot.edit_message_text(text=replies[ln]['Tec_captions'][1], chat_id=id, message_id=call.message.message_id, reply_markup=buttons(admins[id]['available']))


@dp.message_handler(state=Add_day.day)
async def add_day_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = admins[id]['language']
    regx = re.compile(r'(\d{1,2}).(\d{1,2}|[a-zA-Z]{3,9}).(\d{2,4})')
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    temp = list(regx.findall(message.text)[0])
    if len(temp) == 3:
        if len(temp[2]) == 2:
            temp[2] = '20' + temp[2]
        if temp[1][:3].capitalize() in months:
            day = f'{int(temp[0])} {temp[1][:3].capitalize()} {int(temp[2])}'
            await state.update_data(day=day)
            await bot.send_message(id, replies[ln]['Tec_add_date'][1])
            await Add_day.time.set()
        elif temp[1].isdecimal():
            day = f'{int(temp[0])} {months[int(temp[1]) - 1]} {int(temp[2])}'
            await state.update_data(day=day)
            await bot.send_message(id, replies[ln]['Tec_add_date'][1])
            await Add_day.time.set()
    else:
        await bot.send_message(id, replies[ln]['Tec_add_date'][0], reply_to_message_id=message.message_id)
        return


@dp.message_handler(state=Add_day.time)
async def add_time_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = admins[id]['language']
    regx = re.compile(r'(\d{1,2}).(\d{1,2})')
    text = regx.findall(message.text)[0]
    if len(text) != 2:
        await bot.send_message(id, replies[ln]['Tec_add_date'][1], reply_to_message_id=message.message_id)
        return
    day = await state.get_data()
    admins[id]['available'] = admins[id]['available'] + \
        [f'{day["day"]} {text[0]}:{text[1]}']
    update_datafile('admins')
    await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Tec_choices']))
    await state.finish()


@dp.message_handler(state=Ask_tec.name)
async def tec_name_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = admins[id]['language']
    await state.update_data(name=message.text)
    await bot.send_message(id, replies[ln]['Tec_reg'][1])
    await Ask_tec.phone.set()


@dp.message_handler(state=Ask_tec.phone)
async def tec_phone_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = admins[id]['language']
    if not all(map(lambda x: x in '+0123456789', message.text)):
        await bot.send_message(id, replies[ln]['Tec_reg'][1], reply_to_message_id=message.message_id)
        return
    await state.update_data(phone=message.text)
    await bot.send_message(id, replies[ln]['Tec_reg'][2])
    await Ask_tec.telegram.set()


@dp.message_handler(state=Ask_tec.telegram)
async def tec_tg_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = admins[id]['language']
    if not message.text.startswith('@'):
        await bot.send_message(id, replies[ln]['Tec_reg'][2], reply_to_message_id=message.message_id)
        return
    await state.update_data(telegram=message.text)
    await bot.send_message(id, replies[ln]['Tec_reg'][3])
    await Ask_tec.id.set()


@dp.message_handler(state=Ask_tec.id)
async def tec_id_step(message: types.Message, state: FSMContext):
    id = str(message.chat.id)
    ln = admins[id]['language']
    if not all(map(lambda x: x in '0123456789', message.text)):
        await bot.send_message(id, replies[ln]['Tec_reg'][3], reply_to_message_id=message.message_id)
        return
    await state.update_data(id=message.text)
    user_data = {'language': None, **await state.get_data(), 'available': []}
    id = user_data.pop('id')
    admins[id] = user_data
    update_datafile('admins')
    await bot.send_message(id, replies[ln]['Questions'][1], reply_markup=buttons(replies[ln]['Tec_choices']))
    await state.finish()


executor.start_polling(dp)
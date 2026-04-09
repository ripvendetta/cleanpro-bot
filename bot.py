import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ===== КОНФИГУРАЦИЯ =====
TOKEN = "8661007761:AAH7sA6Zx1Wo_z_23ZcU6q6_D6OClBRoFQ8"  # ВСТАВЬТЕ СЮДА НОВЫЙ ТОКЕН (старый скомпрометирован!)

# ID получателей (кому будут приходить заявки)
RECIPIENTS = [
    5092827651, 6408101605 # Ваш ID (разработчик)
    # 123456789,  # Сюда добавьте ID владельца, если он другой
]

# ===== НАСТРОЙКА =====
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ===== ЦЕНЫ (из сайта) =====
PRICES = {
    "apartment": {"name": "Квартира", "min_price": 1500, "price_per_m2": 250},
    "office": {"name": "Офис", "min_price": 2000, "price_per_m2": 220},
    "renovation": {"name": "После ремонта", "min_price": 3000, "price_per_m2": 350}
}

# ===== КЛАВИАТУРЫ =====
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧽 Заказать уборку")],
        [KeyboardButton(text="💰 Цены и калькулятор")],
        [KeyboardButton(text="📞 Контакты владельца")]
    ],
    resize_keyboard=True
)

service_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Квартира", callback_data="service_apartment")],
        [InlineKeyboardButton(text="🏢 Офис", callback_data="service_office")],
        [InlineKeyboardButton(text="🏗️ После ремонта", callback_data="service_renovation")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ]
)

# ===== СОСТОЯНИЯ ДЛЯ ЗАЯВКИ =====
class OrderForm(StatesGroup):
    choosing_service = State()
    entering_area = State()
    entering_address = State()
    entering_phone = State()

# ===== ФУНКЦИЯ ОТПРАВКИ ЗАЯВКИ ВСЕМ ПОЛУЧАТЕЛЯМ =====
async def send_order_to_recipients(order_text: str):
    """Отправляет заявку всем получателям из списка RECIPIENTS"""
    for recipient_id in RECIPIENTS:
        try:
            await bot.send_message(recipient_id, order_text, parse_mode="HTML")
            logging.info(f"✅ Заявка отправлена пользователю {recipient_id}")
        except Exception as e:
            logging.error(f"❌ Не удалось отправить заявку {recipient_id}: {e}")

# ===== ОБРАБОТЧИК КОМАНДЫ /start =====
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "✨ Добро пожаловать в CleanPro — профессиональный клининг!\n\n"
        "Я помогу вам рассчитать стоимость уборки и оформить заявку.\n\n"
        "Используйте кнопки меню:",
        reply_markup=main_menu_kb
    )

# ===== ЗАКАЗ УБОРКИ =====
@dp.message(F.text == "🧽 Заказать уборку")
async def order_start(message: Message, state: FSMContext):
    await state.set_state(OrderForm.choosing_service)
    await message.answer(
        "Выберите тип уборки:",
        reply_markup=service_kb
    )

# ===== ЦЕНЫ И КАЛЬКУЛЯТОР =====
@dp.message(F.text == "💰 Цены и калькулятор")
async def show_prices(message: Message):
    text = "📊 *Наши цены:*\n\n"
    for key, data in PRICES.items():
        text += f"• *{data['name']}*: от {data['min_price']} ₽\n"
        text += f"  (стоимость за м²: {data['price_per_m2']} ₽)\n\n"
    text += "🧮 *Как рассчитать стоимость:*\n"
    text += "Умножьте площадь помещения на цену за м².\n"
    text += "Если сумма меньше минимальной — действует минимальная цена.\n\n"
    text += "🔹 Пример для квартиры 35 м²:\n"
    text += "35 × 250 = 8750 ₽\n\n"
    text += "Для точного расчёта нажмите «🧽 Заказать уборку»."
    await message.answer(text, parse_mode="Markdown")

# ===== КОНТАКТЫ ВЛАДЕЛЬЦА =====
@dp.message(F.text == "📞 Контакты владельца")
async def show_contacts(message: Message):
    text = (
        "📞 *Связаться с владельцем:*\n\n"
        "Телефон: `+7 999 652 8355`\n"
        "WhatsApp: [написать](https://wa.me/79996528355)\n\n"
        "Или напишите нам в Telegram, и мы ответим вам в ближайшее время!"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# ===== ВЫБОР ТИПА УБОРКИ =====
@dp.callback_query(F.data.startswith("service_"), StateFilter(OrderForm.choosing_service))
async def service_chosen(callback: CallbackQuery, state: FSMContext):
    service_type = callback.data.split("_")[1]
    service_info = PRICES[service_type]
    
    await state.update_data(service_type=service_type, service_name=service_info["name"])
    await state.set_state(OrderForm.entering_area)
    
    await callback.message.edit_text(
        f"✅ Вы выбрали: *{service_info['name']}*\n\n"
        f"💰 Стоимость за м²: {service_info['price_per_m2']} ₽\n"
        f"📉 Минимальная цена: {service_info['min_price']} ₽\n\n"
        f"📏 Введите площадь помещения в *квадратных метрах* (число):",
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== НАЗАД В ГЛАВНОЕ МЕНЮ =====
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "Возврат в главное меню.",
        reply_markup=main_menu_kb
    )
    await callback.answer()

# ===== ВВОД ПЛОЩАДИ =====
@dp.message(OrderForm.entering_area)
async def process_area(message: Message, state: FSMContext):
    try:
        area = float(message.text.replace(",", "."))
        if area <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введите положительное число (площадь в м²). Например: 42.5")
        return
    
    data = await state.get_data()
    service_type = data["service_type"]
    price_per_m2 = PRICES[service_type]["price_per_m2"]
    min_price = PRICES[service_type]["min_price"]
    
    calculated = area * price_per_m2
    final_price = max(calculated, min_price)
    
    await state.update_data(area=area, calculated_price=calculated, final_price=final_price)
    await state.set_state(OrderForm.entering_address)
    
    await message.answer(
        f"📐 Площадь: {area} м²\n"
        f"🧮 Предварительный расчёт: {calculated} ₽\n"
        f"💰 *Итоговая стоимость: {final_price} ₽*\n\n"
        f"📍 Введите адрес для уборки:",
        parse_mode="Markdown"
    )

# ===== ВВОД АДРЕСА =====
@dp.message(OrderForm.entering_address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(OrderForm.entering_phone)
    await message.answer(
        "📞 Введите ваш контактный телефон для связи:\n"
        "Например: +7 999 123 45 67"
    )

# ===== ВВОД ТЕЛЕФОНА И ОТПРАВКА ЗАЯВКИ =====
@dp.message(OrderForm.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not any(ch.isdigit() for ch in phone):
        await message.answer("❌ Пожалуйста, введите корректный номер телефона (с цифрами).")
        return
    
    await state.update_data(phone=phone)
    data = await state.get_data()
    
    # Формируем красивое сообщение с заявкой
    order_text = (
        "🔔 *НОВАЯ ЗАЯВКА НА УБОРКУ!* 🔔\n\n"
        f"🏷️ *Услуга:* {data['service_name']}\n"
        f"📏 *Площадь:* {data['area']} м²\n"
        f"💰 *Итоговая цена:* {data['final_price']} ₽\n"
        f"📍 *Адрес:* {data['address']}\n"
        f"📞 *Телефон клиента:* {data['phone']}\n\n"
        f"🕐 *Время заявки:* {message.date.strftime('%d.%m.%Y %H:%M:%S')}\n"
        f"👤 *ID клиента:* `{message.from_user.id}`\n"
        f"👤 *Username:* @{message.from_user.username if message.from_user.username else 'нет'}\n"
        f"👤 *Имя:* {message.from_user.full_name}"
    )
    
    # Отправляем заявку всем получателям (вам и владельцу)
    await send_order_to_recipients(order_text)
    
    # Подтверждение клиенту
    await message.answer(
        "✅ *Заявка успешно отправлена!*\n\n"
        f"📋 *Детали вашего заказа:*\n"
        f"• Услуга: {data['service_name']}\n"
        f"• Площадь: {data['area']} м²\n"
        f"• Стоимость: {data['final_price']} ₽\n"
        f"• Адрес: {data['address']}\n\n"
        "Спасибо, что выбрали CleanPro!\n"
        "Мы свяжемся с вами в ближайшее время по указанному телефону.",
        parse_mode="Markdown",
        reply_markup=main_menu_kb
    )
    
    # Выводим в терминал для отладки
    logging.info(f"Заявка от {message.from_user.id}: {data['service_name']} - {data['final_price']} ₽")
    
    await state.clear()

# ===== ЗАПУСК БОТА =====
async def main():
    print("🚀 Бот CleanPro запущен...")
    print(f"📨 Заявки будут отправляться получателям: {RECIPIENTS}")
    print("✅ Бот готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

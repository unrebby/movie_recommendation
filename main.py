from decouple import config
from dotenv import load_dotenv
import logging
import os
import peewee
import telebot


from captcha_generator import get_captcha
from database.models import actors, bot_users, films, wish_list
from messages import captcha_messages, welcome


print(logging.__file__)
load_dotenv()

API_TOKEN: str = config("TELEGRAM_BOT_TOKEN")

CAPTCHA_TRYOUTS: int = 5

_LOGGER = logging.basicConfig(
    filename=f"{os.path.dirname(os.path.abspath(__file__))}/bot.log",
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.info("Logger-1 started successfully")

bot = telebot.TeleBot(API_TOKEN)


def captcha_checker(
    message: telebot.types.Message, captcha_txt: str, cnt: int = 0
) -> None:

    _LOGGER.info(f"Captcha {message.text} by {message.from_user.id} / {captcha_txt}")

    bot.send_message(message.chat.id, captcha_messages.CHECK_MESSAGE)

    if message.text.lower() == captcha_txt:
        bot.send_message(message.chat.id, captcha_messages.CAPTCHA_CORRECT)

        bot_users.insert(
            {
                bot_users.telegram_id: message.from_user.id,
                bot_users.chat_id: message.chat.id,
                bot_users.first_name: message.from_user.first_name,
                bot_users.last_name: message.from_user.last_name,
                bot_users.tg_username: message.from_user.username,
            }
        ).execute()

        bot.send_message(message.chat.id, welcome.WELCOME_MESSAGE)

    else:

        if cnt + 1 > CAPTCHA_TRYOUTS:
            bot.send_message(
                message.chat.id,
                captcha_messages.CAPTCHA_LIMIT,
            )
            _LOGGER.info(f"Captcha Limit by {message.from_user.id}")

            return False

        bot.send_message(message.chat.id, captcha_messages.CAPTCHA_BAD)

        return_message = bot.send_message(
            message.chat.id, captcha_messages.CAPTCHA_INFO
        )

        cnt += 1

        bot.register_next_step_handler(
            return_message, captcha_checker, captcha_txt, cnt
        )


def send_captcha(message: telebot.types.Message):
    captcha = get_captcha(5)
    bot.send_photo(message.chat.id, captcha[0])
    return_message = bot.send_message(message.chat.id, captcha_messages.CAPTCHA_INFO)
    bot.register_next_step_handler(return_message, captcha_checker, captcha[1])


@bot.message_handler(commands=["start"])
def send_welcome(message: telebot.types.Message) -> None:
    _LOGGER.info(f"Start by {message.from_user.id}")

    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():

        (
            bot_users.update(
                {
                    bot_users.first_name: message.from_user.first_name,
                    bot_users.last_name: message.from_user.last_name,
                    bot_users.tg_username: message.from_user.username,
                    bot_users.chat_id: message.chat.id,
                }
            )
            .where(bot_users.telegram_id == message.from_user.id)
            .execute()
        )

        bot.send_message(message.chat.id, welcome.WELCOME_MESSAGE)

    else:
        _LOGGER.info(f"Attempting to register {message.from_user.id}")

        bot.send_message(message.chat.id, "Давай зарегестрируем тебя.")

        send_captcha(message)


@bot.message_handler(commands=["help"])
def send_welcome(message: telebot.types.Message) -> None:
    bot.send_message(message.chat.id, welcome.WELCOME_MESSAGE)


@bot.message_handler(commands=["actor"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        arguments = message.text.split(" ")

        if len(arguments) < 3:
            bot.send_message(message.chat.id, "Укажите актёра")


        elif arguments[1].isalpha():
            actor_ = arguments[1] + ' ' + arguments[2]
            bot.send_message(message.chat.id, "Ищу...")
            query: peewee.ModelSelect = actors.select().where(
                actors.actor == actor_ #arguments[1]
            )

            if query:
                reply = f"Вот фильмы, где снимался {actor_}:\n"

                for row in query:
                    reply += f"{row.film_name_id}\n"

                bot.send_message(message.chat.id, reply)

            else:
                bot.send_message(message.chat.id, "Не найдено фильмов с таким актёром.")

        else:
            bot.send_message(message.chat.id, "Некорректно указан актёр!")

    else:
        bot.send_message(message.chat.id, "Нажми /start, чтобы зарегестрироваться!")

@bot.message_handler(commands=["info"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        arguments = message.text.split(" ")

        if len(arguments) < 2:
            bot.send_message(message.chat.id, "Укажите название фильма.")

        elif arguments[1].isalnum():
            film_ = ''
            for i in range(1, len(arguments) - 1):
                film_ += str(arguments[i]) + ' '
            film_ += arguments[len(arguments) - 1]

            bot.send_message(message.chat.id, "Ищу...")

            query: peewee.ModelSelect = films.select().where(
                films.name == film_
            )

            if query:
                reply = f"Вот информация о фильме {film_}:\n"
                for row in query:
                    reply += 'Режиссёр: '
                    reply += f"{row.director}\n"
                    reply += 'Год выпуска: '
                    reply += f"{row.year}\n"
                    reply += 'Язык оригинала: '
                    reply += f"{row.language}\n"
                    reply += 'Продолжительность в минутах: '
                    reply += f"{row.duration}\n"
                    reply += 'Жанр: '
                    reply += f"{row.genre}\n"

                bot.send_message(message.chat.id, reply)

            else:
                bot.send_message(message.chat.id, "Не найдено фильмов с таким названием")

        else:
            bot.send_message(message.chat.id, "Некорректно указан фильм!")

    else:
        bot.send_message(message.chat.id, "Нажми /start, чтобы зарегестрироваться!")


@bot.message_handler(commands=["add"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        arguments = message.text.split(" ")

        if len(arguments) < 2:
            bot.send_message(message.chat.id, "Укажите название фильма.")

        elif arguments[1].isalnum():
            film_ = ''
            for i in range(1, len(arguments) - 1):
                film_ += str(arguments[i]) + ' '
            film_ += arguments[len(arguments) - 1]

            if (
                wish_list.select()
                .where(
                    wish_list.telegram_id == message.from_user.id, wish_list.film_name == film_
                )
                .exists()
            ):
                bot.send_message(message.chat.id, "Фильм уже в избранном")

            else:
                wish_list.insert(
                    {
                        wish_list.telegram_id: message.from_user.id,
                        wish_list.film_name: film_,
                    }
                ).execute()
                bot.send_message(message.chat.id, "Фильм добавлен.")

        else:
            bot.send_message(message.chat.id, "Некорректное название.")

    else:
        bot.send_message(message.chat.id, "Нажми /start, чтобы зарегестрироваться!")


@bot.message_handler(commands=["rating"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        arguments = message.text.split(" ")

        if len(arguments) < 3:
            bot.send_message(message.chat.id, "Некорректный ввод.")

        elif arguments[1].isalnum():
            film_ = ''
            for i in range(1, len(arguments) - 2):
                film_ += str(arguments[i]) + ' '
            film_ += arguments[len(arguments) - 2]
            score_ = float(arguments[len(arguments) - 1])

            films.update(
                {
                    films.rating: (films.rating + score_),
                    films.counter: films.counter + 1,
                }
            ).where(films.name == film_).execute()
            bot.send_message(message.chat.id, "Фильм оценен.")

        else:
            bot.send_message(message.chat.id, "Некорректное название.")

    else:
        bot.send_message(message.chat.id, "Нажми /start, чтобы зарегестрироваться!")


@bot.message_handler(commands=["director"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        arguments = message.text.split(" ")

        if len(arguments) < 3:
            bot.send_message(message.chat.id, "Укажите режиссёра")

        elif arguments[1].isalpha():
            director_ = arguments[1] + ' ' + arguments[2]

            bot.send_message(message.chat.id, "Ищу")
            query: peewee.ModelSelect = films.select().where(
                films.director == director_
            )

            if query:
                reply = f"Вот список фильмов, которые снял {director_}:\n"
                for row in query:
                    reply += f"{row.name}\n"

                bot.send_message(message.chat.id, reply)

            else:
                bot.send_message(
                    message.chat.id, "Не найдено фильмов с таким режиссёром"
                )

        else:
            bot.send_message(message.chat.id, "Некорректно указан режиссёр!")

    else:
        bot.send_message(message.chat.id, "Нажми /start, чтобы зарегестрироваться!")


@bot.message_handler(commands=["favourite"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():

        query: peewee.ModelSelect = wish_list.select().where(
            wish_list.telegram_id == message.from_user.id
        )

        if query:
            reply = f"Вот список фильмов, которые у вас в избранном:\n"
            for row in query:
                print(row.film_name_id)
                reply += f"{row.film_name_id}\n"

            bot.send_message(message.chat.id, reply)

        else:
            bot.send_message(message.chat.id, "Ваш список избранных фильмов пуст!")



@bot.message_handler(commands=["genre"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        arguments = message.text.split(" ")
        if len(arguments) < 2:
            bot.send_message(message.chat.id, "Укажите жанр")

        elif arguments[1].isalpha():
            bot.send_message(message.chat.id, "Ищу...")

            query: peewee.ModelSelect = films.select().where(
                films.genre == arguments[1]
            )

            if query:
                reply = f"Вот список фильмов в жанре {arguments[1]}:\n"
                for row in query:
                    reply += f"{row.name}\n"

                bot.send_message(message.chat.id, reply)

            else:
                bot.send_message(message.chat.id, "Не найдено фильмов с таким жанром")

        else:
            bot.send_message(message.chat.id, "Некорректно указан жанр!")

    else:
        bot.send_message(message.chat.id, "Нажми /start, чтобы зарегестрироваться!")


@bot.message_handler(commands=["top5"])
def send_welcome(message: telebot.types.Message) -> None:
    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        query = films.select().order_by((films.rating / films.counter).desc()).limit(5)

        if query:
            reply = "Топ-5 фильмов с лучшим рейтингом:\n"

            for row in query:
                reply += f'"{row.name}" - {row.rating / row.counter}\n'

            bot.send_message(message.chat.id, reply)


@bot.message_handler(func=lambda message: True)
def echo_message(message: telebot.types.Message) -> None:

    if bot_users.select().where(bot_users.telegram_id == message.from_user.id).exists():
        bot.send_message(
            message.chat.id,
            "Я вас не понимаю :(\n Нажмите /help, чтобы увидеть, что я могу!",
        )

    else:
        bot.send_message(message.chat.id, "Нажми /start, чтобы зарегестрироваться!")


bot.infinity_polling()

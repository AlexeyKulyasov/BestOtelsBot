from telebot import TeleBot

import handlers.callback_query
import handlers.middleware
import handlers.message
from BotController import BotController


class MessageHandler:

    def __init__(self, bot: TeleBot, bot_controller: BotController, debug_mode: bool):
        self.bot = bot
        self.bot_controller = bot_controller
        self.debug_mode = debug_mode

    def start(self):
        handlers.middleware.handle_cancel_command(self.bot, self.bot_controller)

        handlers.callback_query.handle_callback_set_default_value(self.bot, self.bot_controller)
        handlers.callback_query.handle_callback_check_entered_data(self.bot, self.bot_controller)
        handlers.callback_query.handle_callback_select_date(self.bot, self.bot_controller)

        handlers.message.handle_cmd_send_welcome(self.bot)
        handlers.message.handle_cmd_low_price_and_high_price(self.bot, self.bot_controller)
        handlers.message.handle_cmd_best_deal(self.bot, self.bot_controller)
        handlers.message.handle_get_location(self.bot, self.bot_controller, self.debug_mode)
        handlers.message.handle_get_city(self.bot, self.bot_controller)
        handlers.message.handle_get_count_humans(self.bot, self.bot_controller)
        handlers.message.handle_get_range_price(self.bot, self.bot_controller)
        handlers.message.handle_get_range_distance(self.bot, self.bot_controller)
        handlers.message.handle_get_count_hotels(self.bot, self.bot_controller)
        handlers.message.handle_unknown_message(self.bot, self.bot_controller)

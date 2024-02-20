import os
from random import randrange

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from class_vk import VK
import db


"""Кнопки для взаимодействия с ботом"""

keyboard_main = VkKeyboard(one_time=False)
keyboard_main.add_button(label='Найти пару', color=VkKeyboardColor.PRIMARY)
keyboard_main.add_button(label='Добавить в избранное', color=VkKeyboardColor.POSITIVE)
keyboard_main.add_button(label='Добавить в черный список', color=VkKeyboardColor.NEGATIVE)
keyboard_main.add_button(label='Показать список избранных', color=VkKeyboardColor.SECONDARY)


class Bot:

    def __init__(self) -> None:
        self.session = vk_api.VkApi(token=os.getenv('TOKEN_BOT'))
        self.longpoll = VkLongPoll(self.session)
        self.vk_api = VK()
        self.candidate = None
        self.offset = -1
        self.user = None
        
        

    def send_msg(self, user_id: int, message=None, keyboard=None, attachment=None):
        """
        Функция для отправки сообщений ботом, возвращает сообщение, которое отправит бот 
        """

        responce = self.session.method('messages.send', 
                    {'user_id': user_id, 
                        'message': message,  
                        'random_id': randrange(10 ** 7),
                        'keyboard': keyboard,
                        'attachment': attachment,                       
                        })
        return responce 
    

    def func_main(self):
        """
        Функция-вызов остальных функций, для взаимодействия с ботом
        """

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                request = event.text.lower() 
                user_id = event.user_id
                if request == 'привет':                    
                    self.send_first_msg(user_id)                 
                elif request == 'найти пару':
                    self.offset += 1
                    self.send_candidate_info(user_id)  
                elif request == 'добавить в избранное':
                    self.add_favorite(user_id)    
                elif request == 'добавить в черный список':
                    self.add_black_list(user_id)   
                elif request == 'показать список избранных':
                    self.show_favorite(user_id)                                  
                else:
                    self.send_msg(user_id, 'Ошибка! Напиши мне "Привет"')
        

    def send_first_msg(self, user_id: int):
        """
        Метод для отправки сообщения ботов, в ответ на "привет"
        """


        self.user = self.vk_api.get_user_info(user_id)
        db.add_new_user(self.user['owner_id'],
                        self.user['first_name'],
                        self.user['last_name'],
                        self.user['user_link'])
        
        name = self.user['first_name']
        msg = f"""Привет, {name}! Я - бот, который поможет тебе подобрать пару ❤️.
        Нажимая на кнопку "Найти пару", я буду отправлять тебе кандидатов для знакомства. 
        Если тебе понравился человек - нажми "Добавить в избранный список" 📔, 
        но если полагаешь, что звезды не сойдутся - нажми на "Добавить в черный список" 💔. 
        Если захочешь посмотреть на пользователей, которые тебе понравились - нажми "Показать избранное". 
        Удачи!😉 """
        keyboard  = keyboard_main.get_keyboard()
        responce = self.send_msg(user_id, msg, keyboard=keyboard)
        return responce
    

    def send_candidate_info(self, user_id: int):  
        """
        Метод для отправки информации ботом о подходящих кандидатах
        """
        while True: 
            self.candidate = self.vk_api.search_couple(self.user, self.offset)                        
            if db.check_users(self.candidate['owner_id']):
                self.candidate = self.vk_api.search_couple(self.user, self.offset)
                db.add_new_user(**self.candidate)
                msg = (f"Как тебе? {self.candidate['first_name']} "
                       f"{self.candidate['last_name']}. Вот ссылка "
                       f"на профиль - {self.candidate['user_link']}. А вот фотографии: ")
                attachment = self.vk_api.get_photo(self.candidate['owner_id'])                  
                response = self.send_msg(user_id, msg, attachment=attachment)   
            else:
                self.offset += 1
                continue           
            return response
                

    def add_favorite(self, user_id: int):
        """
        Метод для добавления кандидата в список избранных
        """
        db.add_favorite(self.user, self.candidate)
        response = self.send_msg(user_id, f"{self.candidate['first_name']} "
                                          f"{self.candidate['last_name']} теперь в избранном!")
        return response



    def add_black_list(self, user_id: int):
        """
        Метод для добавления кандидата в черный список
        """
        db.add_black_list(self.user, self.candidate)
        response = self.send_msg(user_id, f"{self.candidate['first_name']} "
                                          f"{self.candidate['last_name']} теперь в черном списке!")
        return response



    def show_favorite(self, user_id: int):
        """
        Метод для получения списка Избранных
        """        
        fav_list = db.show_fav_list(self.user)
        message = ''
        count = 1
        if fav_list:
            for fav in fav_list:
                message += f'{count}. {fav[0]} {fav[1]} {fav[2]}\n'
                count += 1
        else:
                message = 'В списке избранных пока никого нет 😔'
        response = self.send_msg(user_id, f"Вот список пользователей, которые тебе "
                                 f"понравились:\n {message}")
        return response



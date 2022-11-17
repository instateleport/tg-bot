import configparser

config = configparser.ConfigParser()

# Add the structure to the file we will create
config.add_section('program_settings')
config.set('program_settings', 'token', '5693735478:AAGmPAb-k5fHVIuqTWo9jSJKkVqfhObMfa0')

config.add_section('prewritten')
config.set('prewritten', 'instructions_4_authors', '1. Добавьте этого бота @имя в свой телеграм-канал администратором. \n'
                                                   '2. нажмите на кнопку ниже и выберите канал, в которого только что '
                                                   'добавили бота./n 3. Отправьте сообщение, которое будет в поле ввода.')

# Write the new structure to the new file
with open("сonfigfile.ini", 'w', encoding='utf-8') as configfile:
    config.write(configfile)

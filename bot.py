import os
import logging
import re
import paramiko
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import psycopg2
from psycopg2 import Error

TOKEN = os.getenv('TOKEN')
RM_HOST = os.getenv('RM_HOST')
RM_PORT = os.getenv('RM_PORT')
RM_USER = os.getenv('RM_USER')
RM_PASSWORD = os.getenv('RM_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_PORT_SSH = os.getenv('DB_PORT_SSH')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_REPL_HOST = os.getenv('DB_REPL_HOST')
DB_REPL_PORT = os.getenv('DB_REPL_PORT')
DB_REPL_USER = os.getenv('DB_REPL_USER')
DB_REPL_PASSWORD = os.getenv('DB_REPL_PASSWORD')
DB_SSH_USER = os.getenv('DB_SSH_USER')
DB_SSH_PASSWORD = os.getenv('DB_SSH_PASSWORD')

logging.basicConfig(filename='/app/logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def find_phone_number_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'find_phone_number'

def find_phone_number(update: Update, context):
    user_input = update.message.text
    phones_regex = re.compile(r'\+?\d\s?\(?-?\d{3}\)?-?\s?\d{3}-?\s?\d{2}-?\s?\d{2}')
    phones_list = phones_regex.findall(user_input)
    if not phones_list:
        update.message.reply_text('Телефонные номера не найдены!')
        return ConversationHandler.END
    update.message.reply_text('Найденные номера: ' + ', '.join(phones_list))
    update.message.reply_text('Желаете внести их в базу данных?')
    context.user_data['phones_list'] = phones_list
    return 'save_phone_numbers'
        
 
def save_phone_numbers(update: Update, context):
    user_input = update.message.text.lower()
    phones_list = context.user_data['phones_list']
    if user_input=='да':
        try:
            connection = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_DATABASE)
            cursor = connection.cursor()
            phones_tuple = [(phone,) for phone in phones_list]
            cursor.executemany('INSERT INTO phones (phone) VALUES (%s)', phones_tuple)
            connection.commit()
            update.message.reply_text('Данные успешно внесены в базу данных')
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
    return ConversationHandler.END
    
def find_email_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных адресов: ')
    return 'find_email'

def find_email(update: Update, context):
    user_input = update.message.text
    mail_regex = re.compile(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+')
    mail_list = mail_regex.findall(user_input)
    if not mail_list:
        update.message.reply_text('Электронные адреса не найдены!')
        return ConversationHandler.END
    update.message.reply_text('Найденные адреса: ' + ', '.join(mail_list))
    update.message.reply_text('Желаете внести их в базу данных?')
    context.user_data['mail_list'] = mail_list
    return 'save_emails' 

def save_emails(update: Update, context):
    user_input = update.message.text.lower()
    mail_list = context.user_data['mail_list']
    if user_input=='да':
        try:
            connection = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_DATABASE)
            cursor = connection.cursor()
            mail_list = [(mail,) for mail in mail_list]
            cursor.executemany('INSERT INTO emails (email) VALUES (%s)', mail_list)
            connection.commit()
            update.message.reply_text('Данные успешно внесены в базу данных')
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
    return ConversationHandler.END

def verify_password_command(update: Update, context):
    update.message.reply_text('Введите пароль для проверки на сложность: ')
    return 'verify_password'

def verify_password(update: Update, context):
    user_input = update.message.text
    password_regex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$')
    if password_regex.match(user_input):
        update.message.reply_text('Пароль сложный!')
    else: 
        update.message.reply_text('Пароль простой!')
    return ConversationHandler.END 
    
def ssh():
    host = RM_HOST
    port = RM_PORT
    username = RM_USER
    password = RM_PASSWORD
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)   
    return client 

def ssh_db():
    host = DB_HOST
    port = DB_PORT_SSH
    username = DB_SSH_USER
    password = DB_SSH_PASSWORD
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)   
    return client

def get_repl_logs(update: Update, context):
    client = ssh_db()
    _, stdout, _ = client.exec_command('tail -n 25 /var/log/postgresql/postgresql.log | grep -i replication')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_emails(update: Update, context):
    try:
        connection = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_DATABASE)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails")
        text = 'Emails from database: \n' + '\n'.join(email for _, email in cursor.fetchall())
        update.message.reply_text(text)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            
def get_phones(update: Update, context):
    try:
        connection = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_DATABASE)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phones")
        text = 'Phones from database: \n' + '\n'.join(phone for _, phone in cursor.fetchall())
        update.message.reply_text(text)
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()

def get_release(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('cat /etc/os-release')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_uname(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('uname -a')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_uptime(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('uptime')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_df(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('df')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_free(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('free -h')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)    
    
def get_mpstat(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('mpstat')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def get_w(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('w')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_auths(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('last -n 10')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_critical(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('journalctl -p crit -n 5')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_ps(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('ps')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_ss(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('ss -l | head -n 20')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    
def get_services(update: Update, context):
    client = ssh()
    _, stdout, _ = client.exec_command('service --status-all')
    data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

def get_apt_list_command(update: Update, context):
    update.message.reply_text('Введите "ALL", чтобы вывести информацию обо всех пакетах, либо введите имя пакета')
    return "get_apt_list"
    
def get_apt_list(update: Update, context):
    user_input = update.message.text
    client = ssh()
    if user_input=="ALL":
        _, stdout, _ = client.exec_command('apt list --installed | head -n 25')
        data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        update.message.reply_text(data)
    else:
        _, stdout, stderr = client.exec_command(f'apt show {user_input}')
        error = str(stderr.read()).replace('\\n', '').replace('\\t', '')[2:-1]
        if error != "WARNING: apt does not have a stable CLI interface. Use with caution in scripts.":
            update.message.reply_text("No packet named like that!")
        else:
            data = str(stdout.read()).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
            update.message.reply_text(data)
    return ConversationHandler.END
    
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    findPhoneNumberHandler = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number',find_phone_number_command)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~ Filters.command, find_phone_number)], 
            'save_phone_numbers': [MessageHandler(Filters.text & ~ Filters.command, save_phone_numbers)] 
        },
        fallbacks=[]
    )
    
    findEmailHandler = ConversationHandler(
        entry_points=[CommandHandler('find_email',find_email_command)],
        states={
            'find_email': [MessageHandler(Filters.text & ~ Filters.command, find_email)], 
            'save_emails': [MessageHandler(Filters.text & ~ Filters.command, save_emails)] 
        },
        fallbacks=[]
    )
    
    passwordVerifyHandler = ConversationHandler(
        entry_points=[CommandHandler('verify_password',verify_password_command)],
        states={'verify_password': [MessageHandler(Filters.text & ~ Filters.command, verify_password)], },
        fallbacks=[]
    )
    
    get_apt_listHandler = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list',get_apt_list_command)],
        states={'get_apt_list': [MessageHandler(Filters.text & ~ Filters.command, get_apt_list)], },
        fallbacks=[]
    )
    
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phones", get_phones))
    dp.add_handler(get_apt_listHandler)
    dp.add_handler(findPhoneNumberHandler)
    dp.add_handler(findEmailHandler)
    dp.add_handler(passwordVerifyHandler)
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

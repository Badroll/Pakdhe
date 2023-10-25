import schedule
import time
import pymysql
import env
import helper
import random
from datetime import datetime

mydb = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
cursor = mydb.cursor()

cursor.execute("SELECT * FROM receiver")
receiver = helper.sqlresGet(cursor)
cursor.close()

print(receiver)

last_processed = None

def broadcast():
    addon_sleep_time = random.randint(1, 10)

    global last_processed

    print("======")
    print("last_processed", last_processed)
    if last_processed == None:
        index = 0
    else:
        index = last_processed +1
    last_processed = index

    if index >= len(receiver):
        #return False
        last_processed = None
        return

    ymdhis = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    user = receiver[index]
    msg = ""
    msg += "*HELLO, " + user["RECEIVER_NAMA"] + "*"
    msg += "\nThis is testing broadcast WhatsApp message"
    msg += "\n_*just ignore everything_"
    msg += "\n\nmessage created at " + ymdhis
    msg += "\n" + str(addon_sleep_time)
    msg += "\n\n~ " + helper.get_setting("WABOT_NAME")

    r = helper.send_wa(user["RECEIVER_WA"], msg)
    print(r)
    time.sleep(30) # sesuai settingan delay dari wablas
    ymdhis = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    update_receiver(user["RECEIVER_ID"], msg, ymdhis, r)
    print("receiver update")
    time.sleep(addon_sleep_time)

    log = ""
    log += "WHATSAPP BROADCAST"
    log += "\n"
    log += "\nHost => "
    log += "\nReceiver => " + user["RECEIVER_NAMA"]
    log += "\nReceiver WA => " + user["RECEIVER_WA"]
    log += "\nMessage : "
    log += "\n" + msg
    helper.send_telegram(log)


def update_receiver(ID, msg, date, response):
    mydb = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
    cursor = mydb.cursor()
    query = """UPDATE receiver SET RECEIVER_MESSAGE = %s, RECEIVER_DATE = %s, RECEIVER_RESPONSE = %s WHERE RECEIVER_ID = %s"""
    values = (msg, date, response, ID)
    cursor.execute(query, values)
    mydb.commit()
    cursor.close()


schedule.every(55).seconds.do(broadcast)

while True:
    schedule.run_pending()
    time.sleep(1)
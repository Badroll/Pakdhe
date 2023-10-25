import schedule
import time
import pymysql
import env
import helper
import random
from datetime import datetime

mydb = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
cursor = mydb.cursor()

cursor.execute("SELECT * FROM receiver WHERE RECEIVER_SENDER = '6285173205090' AND RECEIVER_DATE IS NOT NULL ") #JANGAN LUPA, switch NULL
receiver = helper.sqlresGet(cursor)
cursor.close()

print(receiver)

run_cron = True
last_processed = None

def broadcast():
    global run_cron
    try:
        global last_processed
        #time.sleep(30) # sesuai settingan delay dari wablas

        sleep_time = random.randint(1, 10)
        time.sleep(sleep_time)

        print("======")
        print("last_processed", last_processed)
        if last_processed == None:
            index = 0
        else:
            index = last_processed +1
        last_processed = index

        if index >= len(receiver):
            last_processed = None
            return

        ymdhis = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        user = receiver[index]
        msg = ""
        msg += "*HELLO, " + user["RECEIVER_NAMA"] + "*"
        msg += "\nThis is testing broadcast WhatsApp message"
        msg += "\n_*just ignore everything_"
        msg += "\n\nmessage created at " + ymdhis
        msg += f"\nsleep_time : {sleep_time}"

        r = helper.send_wa_multipleSendText(user["RECEIVER_WA"], msg)
        print(r)
        if r[0]:
            #update_receiver(user["RECEIVER_ID"], msg, ymdhis, r[1])
            helper.db_update("receiver",
                {
                    "RECEIVER_MESSAGE" : msg,
                    "RECEIVER_DATE" : ymdhis,
                    "RECEIVER_RESPONSE" : r[1],
                },
                f"RECEIVER_ID = {user['RECEIVER_ID']}"
            )
            log = ""
            log += "WHATSAPP BROADCAST"
            log += "\n"
            log += "\nHost => "
            log += "\nReceiver => " + user["RECEIVER_NAMA"]
            log += "\nReceiver WA => " + user["RECEIVER_WA"]
            log += "\nMessage : "
            log += "\n" + msg
            log += "\nResponse :"
            log += "\n" + r[1]
            helper.send_telegram(log)
        else:
            # URGENT LOG
            log = ""
            log += "\nWHATSAPP BROADCAST FAILED"
            log + "\n\n" + r[1]
            helper.send_telegram(log, chat_id=env.tele_chat_id_me)
            run_cron = False

    except Exception as e:
        # URGENT LOG
        print("Terjadi kesalahan:", e)
        log = ""
        log += "\nBROADCAST FUNCTION GOT SOME ERROR"
        log += f"\n\n{e}"
        helper.send_telegram(log, chat_id=env.tele_chat_id_me)
        run_cron = False


schedule.every(20).seconds.do(broadcast)

try:
    while run_cron:
        schedule.run_pending()
        time.sleep(1)
    print("CRON STOPPED, run_cron is false")
    schedule.clear()
except KeyboardInterrupt:
    print("CRON STOPPED, forcely")
    schedule.clear()
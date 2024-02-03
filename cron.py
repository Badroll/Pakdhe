prod = 0 == 1

import schedule
import time
import pymysql
import env
import helper
import random
from datetime import datetime

mydb = pymysql.connect(host=env.dbHost, user=env.dbUser, passwd=env.dbPassword, database=env.dbDatabase)
cursor = mydb.cursor()

qry = "SELECT * FROM receiver WHERE RECEIVER_SENDER = '6282131789196' AND RECEIVER_DATE IS NULL"
if not prod:
    qry += " AND RECEIVER_WA IN ('6281215992673', '6281348457600', '6282242023609')"
cursor.execute(qry)
receiver = helper.sqlresGet(cursor)
cursor.close()

run_cron = True
last_processed = None
reported = 0

def broadcast():
    global run_cron
    try:
        global last_processed
        global reported

        sleep_time = random.randint(1, 10)
        time.sleep(sleep_time)

        print("===============================================================")
        print("---------------------------------------------------------------")
        print("last_processed", last_processed)
        if last_processed == None:
            index = 0
        else:
            index = last_processed +1
        last_processed = index

        if index >= len(receiver):
            last_processed = None
            if prod:
                run_cron = False #switch
            return

        ymdhis = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        user = receiver[index]
        msg = ""
        msg += "Mari Kita Bersama Menuju TPS"
        msg += "\nDi Hari *RABU, 14 FEBRUARI 2024*"
        msg += "\n\nUntuk Memilih Saya"
        msg += "\n*R AKH MUNIF HARYONO, SKM,. MKes*"
        msg += "\n\nDi Partai GOLKAR No. Urut *6* Dapil *14* Provinsi Jawa Timur, Madura (Bangkalan, Sampang, Pamekasan, Sumenep)"
        msg += "\n\nUNTUK KEMAKMURAN DAN KESEJAHTERAAN RAKYAT KITA BERSAMA"
        msg += "\n\n_pesan ini dikirimkan pada: " + ymdhis + "_"

        img_url = "http://62.72.51.244:5003/file?key=c0SCV-hRKuH&filename=poster_pakdhe.jpg"
        r = helper.send_wa_multipleSendImage(user["RECEIVER_WA"], msg, img_url, account=2)
        print(r)
        if r[0]:
            helper.db_update("receiver",
                {
                    "RECEIVER_MESSAGE" : msg,
                    "RECEIVER_DATE" : ymdhis,
                    "RECEIVER_RESPONSE" : r[1],
                },
                f"RECEIVER_ID = '{user['RECEIVER_ID']}'"
            )
            reported += 1
            if reported == 1:
                reported = 0
                log = ""
                log += "WHATSAPP BROADCAST"
                log += "\n"
                log += f"\nReceiver ID => {user['RECEIVER_ID']}" 
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
    helper.send_telegram("CRON STOPPED, run_cron is false", chat_id=env.tele_chat_id_me)
    schedule.clear()
except KeyboardInterrupt:
    print("CRON STOPPED, forcely")
    helper.send_telegram("CRON STOPPED, forcely", chat_id=env.tele_chat_id_me)
    schedule.clear()
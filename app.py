from flask import Flask, request, jsonify, send_file, Blueprint
from flask_cors import CORS, cross_origin
import pymysql
import datetime
import os
import json
import helper, env

app = Flask(__name__, template_folder="view", static_folder="lib")
app.config["JSON_SORT_KEYS"] = False
app.secret_key = env.app_secret_key
app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app, resources={r"/*": {"origins": "*"}})
one_time_tokens = {}
route = ""
user_data = None


ruled_access_token = []
ruled_auth_token = []
ruled_role_admin = []
ruled_wablas_server = []
ruled_public_route = []
@app.before_request
def middleware():
    requested_route = request.path
    if requested_route in ruled_access_token:
        token = request.headers.get('access-token')
        if token in one_time_tokens:
            del one_time_tokens[token]
        else:
            return helper.composeReply("ERROR", "Access token invalid")
        
    if requested_route in ruled_auth_token:
        token = request.headers.get('auth-token')
        saved_token = helper.db_raw(f"""
                SELECT * FROM _token WHERE TOKEN_VALUE = {token}
            """)[1]
        if len(saved_token == 0):
            return helper.composeReply("ERROR", "Auth Token invalid")
        saved_token = saved_token[0]
        if datetime.now() > saved_token["TOKEN_EXPIRED"]:
            return helper.composeReply("ERROR", "Auth Token expired")
        global user_data
        user_data = helper.db_raw(f"""
            SELECT * FROM _user WHERE USER_TOKEN = {token}
            """)[1]
        if len(user_data) == 0:
            return helper.composeReply("ERROR", "User invalid")
        user_data = user_data[0]

    if requested_route in ruled_role_admin:
        if not user_data["USER_TYPE"] == "USER_TYPE_ADMIN":
            return helper.composeReply("ERROR", "User has no access")
        
    if requested_route in ruled_wablas_server:
        import socket
        client_ip = request.remote_addr
        print(client_ip)
        try:
            client_domain = socket.gethostbyaddr(client_ip)[0]
            print(client_domain)
        except Exception as e:
            client_domain = ""
        if not "wablas.com" in client_domain:
            return helper.composeReply("ERROR", "Has no access to send webhook")
        
    if requested_route in ruled_public_route:
        api_key = request.args.get("key")
        if not api_key == None and api_key == env.api_key_public_route:
            print("please")
        else:
            return helper.composeReply("ERROR", "API key invalid")
            


route = "/token"
ruled_public_route.append(route)
@app.route(route, methods=['GET'])
def token():
    token = helper.generate_token()
    one_time_tokens[token] = True
    return helper.composeReply("SUCCESS", "Token", token)


route = "/caleg"
#ruled_access_token.append(route)
#ruled_auth_token.append(route)
#ruled_role_admin.append(route)
@app.route(route, methods=['POST'])
def caleg():
    global user_data
    data = helper.db_raw("""
        SELECT * FROM _user WHERE USER_TYPE = 'USER_TYPE_CALEG'
    """)[1]
    return helper.composeReply("SUCCESS", "Data Caleg", data)


route = "/caleg_detail"
#ruled_access_token.append(route)
#ruled_auth_token.append(route)
@app.route(route, methods=['POST'])
def caleg_detail():
    global user_data

    is_testing = request.form.get("is_testing")
    if is_testing == None:
        return helper.composeReply("ERROR", "Parameter incomplete (is_testing)")
    is_testing = True if is_testing == "Y" else False
    if is_testing:
        user_data = helper.db_raw(f"""SELECT * FROM _user as A
            WHERE A.USER_PHONE = {'6282131789196'}
        """)[1]
        user_data = user_data[0]

    pemilih = []
    total_sent = 0
    total_confirm = 0
    table = user_data["USER_CALEG_PEMILIH_TABLE"]
    if True: #table == "pemilih"
        pemilih = helper.db_raw(f"""
            SELECT * FROM {table} as A
            LEFT JOIN hooks as B ON A.PEMILIH_HOOKS_ID = B.HOOKS_ID
            LEFT JOIN receiver as C ON A.PEMILIH_WA = C.RECEIVER_WA
            WHERE A.PEMILIH_NIP IS NULL
        """)[1]
        data = user_data
        for i, row in enumerate(pemilih):
            if not row["RECEIVER_ID"] == None and row["RECEIVER_DATE"] == None:
                total_sent += 1
            if row["PEMILIH_JAWABAN"] == "Y" and not row["PEMILIH_HOOKS_ID"] == None:
                total_confirm += 1

        if is_testing:
            pemilih_testing = []
            for i, row in enumerate(pemilih):
                rulesY = ["ya", "y"]
                if not row["PEMILIH_JAWABAN"] == None and row["PEMILIH_JAWABAN"].strip().lower() in rulesY:
                    pemilih_testing.append(row)


    data["PEMILIH"] = pemilih if not is_testing else pemilih_testing
    data["TOTAL_TERKIRIM"] = total_sent
    data["TOTAL_KONFIRMASI"] = total_confirm

    return helper.composeReply("SUCCESS", "Detail Caleg", data)


route = "/auth_login"
#ruled_access_token.append(route)
#ruled_auth_token.append(route)
@app.route(route, methods=['POST'])
def auth_login():
    phone = request.form.get("phone")
    if phone == None:
        return helper.composeReply("ERROR", "Parameter incomplete (phone)")
    password = request.form.get("password")
    if password == None:
        return helper.composeReply("ERROR", "Parameter incomplete (password)")
    
    cek_user = helper.db_raw(f"""
            SELECT * FROM _user WHERE USER_PHONE = {phone}
        """)[1]
    if len(cek_user) == 0:
        return helper.composeReply("ERROR", f"Maaf, user dengan phone {phone} tidak terdaftar")
    if not helper.check_hash(password + phone, cek_user["USER_PASSWORD"]):
        return helper.composeReply("ERROR", f"Password salah, silahkan ulangi")
    
    token = helper.generate_token()
    helper.db_update("_user",
                        {
                            "USER_TOKEN" : token
                        },
                        f"USER_ID = {cek_user['USER_ID']}"
                    )
    insert_token = helper.db_insert("_token",
                        {
                            "TOKEN_VALUE" : token,
                            "TOKEN_CREATED" : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "TOKEN_EXPIRED" : datetime.now().timedelta(days=1)
                        }                
                    )
    cek_user["USER_TOKEN"] = token
    
    return helper.composeReply("SUCCESS", "Login berhasil", cek_user)



route = "/file"
ruled_public_route.append(route)
@app.route(route, methods = ["GET"])
def file():
    filename = request.args.get('filename')
    if not filename:
        return "N", 400
    
    image_path = f'images/{filename}'
    if image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
        mimetype = 'image/jpeg'
    elif image_path.endswith('.png'):
        mimetype = 'image/png'
    else:
        return helper.composeReply("ERROR", 'Unsupported file type')
    return send_file(image_path, mimetype=mimetype)


route = "/hooks"
#ruled_wablas_server.append(route)
@app.route(route, methods = ["GET", "POST"])
def hooks():
    params = request.get_json()
    try:
        hooks_id = helper.db_insert("hooks", {
                            "HOOKS_RESPONSE" : f"{params}",
                            "HOOKS_RESPONSE_id" : params["id"],
                            "HOOKS_RESPONSE_sender" : params["sender"],
                            "HOOKS_RESPONSE_phone" : params["phone"],
                            "HOOKS_RESPONSE_message" : params["message"],
                        })
        
        log = ""
        log += "HOOKS RECEIVED"
        log += "\n"
        log += "\nwablas :"
        log += f"\n{env.wabot}"
        log += "\n\nparams :"
        log += f"\n{params}"
        helper.send_telegram(log, chat_id=env.tele_chat_id_bdmsth_logger_wablas_hooks)
        
        account = helper.db_raw(f"""
            SELECT * FROM _user WHERE USER_WABOT_WA = {params['sender']}
            """)[1]
        if len(account) == 0:
            return helper.composeReply("SUCCESS", "Webhooks processed, thanks!")
        table = account["USER_CALEG_PEMILIH_TABLE"]
        
        if True: #pemilih == "pemilih"
            pemilih = helper.db_raw(f"""
                            SELECT * FROM {table} WHERE PEMILIH_WA = {params["phone"]}
                            """)[1]
            from_pemilih = True if len(pemilih) > 0 else False

            message = params["message"]
            command = message.strip().lower()
            rulesY = ["y", "ya", "yes"]
            if command in rulesY and not params["isGroup"] and from_pemilih:
                update_pemilih = helper.db_update(f"{table}",
                                {
                                    "PEMILIH_JAWABAN" : "Y",
                                    "PEMILIH_HOOKS_ID" : hooks_id,
                                },
                                f"PEMILIH_WA = {params['phone']}"
                            )
                if not update_pemilih[0]:
                    # URGENT LOG
                    log = ""
                    log += "\nFAILED UPDATE ANSWER FROM PEMILIH"
                    log += f"\n\nhooks => {params}"
                    log += f"\npemilih => {pemilih[0]}"
                    log += f"\n\n{update_pemilih[1]}"
                    helper.send_telegram(log, chat_id=env.tele_chat_id_me)

        return helper.composeReply("SUCCESS", "Webhooks processed, thanks!")

    except Exception as e:
        # URGENT LOG
        log = ""
        log += "\nWEBHOOK GOT ERROR"
        log += f"\n\nhooks => {params}"
        log += f"\n\n{e}"
        helper.send_telegram(log, chat_id=env.tele_chat_id_me)
        
        return helper.composeReply("ERROR", "Internal error occurred, sorry!", statuscode=500)
        


if __name__ == '__main__':
    app.run(host = env.runHost, port = env.runPort, debug = env.runDebug)
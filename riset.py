import helper
helper.db_update("receiver", {
    "RECEIVER_DATE" : None,
    "RECEIVER_MESSAGE" : None,
    "RECEIVER_RESPONSE" : None,
},f"RECEIVER_WA IN ('6281215992673', '6281348457600', '6282242023609')")

print("ok")
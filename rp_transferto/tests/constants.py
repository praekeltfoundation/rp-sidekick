PING_RESPONSE_DICT = {
    "info_txt": "pong",
    "authentication_key": "1327027869",
    "error_code": "0",
    "error_txt": "Transaction successful",
}


MSISDN_INFO_RESPONSE_DICT = {
    "country": "South Africa",
    "countryid": "111",
    "operator": "MNO South Africa",
    "operatorid": "222",
    "connection_status": "100",
    "destination_msisdn": "27820000000",
    "destination_currency": "ZAR",
    "product_list": "2,5,10,15,30,40,50,100,150,300,500,750,1000",
    "retail_price_list": "2.80,6.50,12.70,18.90,37.50,49.90,62.20,124.10,"
    "185.90,371.50,618.90,928.10,1243.90",
    "wholesale_price_list": "2.23,5.20,10.15,15.10,29.94,39.84,49.74,99.22,"
    "148.70,297.14,495.06,742.47,995.08",
    "authentication_key": "123456789",
    "error_code": "0",
    "error_txt": "Transaction successful",
}


RESERVE_ID_RESPONSE_DICT = {
    "status_code": "0",
    "reserved_id": "20123457",
    "error_txt": "Transaction successful",
    "authentication_key": "1217303174266",
    "error_code": "0",
}

TOPUP_RESPONSE_DICT = {
    "transactionid": "77748538",
    "msisdn": "69999999999",
    "destination_msisdn": "60172860300",
    "country": "Malaysia",
    "countryid": "799",
    "operator": "Maxis Malaysia",
    "originating_currency": "USD",
    "destination_currency": "MYR",
    "product_requested": "10",
    "actual_product_sent": "10",
    "wholesale_price": "3.39",
    "service_fee": "0.00",
    "retail_price": "4.30",
    "balance": "8.1",
    "sms_sent": "yes",
    "sms": "Happy birthday ",
    "sender_sms": "yes",
    "sender_text": "",
    "cid1": " My Text ",
    "authentication_key": "1326963417",
    "error_code": "0",
    "error_txt": "Transaction successful",
    "local_info_value": "10.00",
    "local_info_amount": "10.00",
    "local_info_currency": "MYR",
    "return_timestamp": "2013-03-18 00:00:01",
    "return_version": "1.06.08",
    "reference_operator": "",
    "operatorid": "",
    "cid2": "",
    "cid3": "",
}

TOPUP_ERROR_RESPONSE_DICT = {
    "transactionid": "",
    "destination_msisdn": "82000001",
    "authentication_key": "1551943066245252",
    "error_code": "101",
    "error_txt": "Destination MSISDN out of range",
}

GET_COUNTRIES_RESPONSE_DICT = {
    "country": "Afghanistan,Albania,Anguilla,Antigua and Barbuda,Argentina,"
    "Armenia,Aruba",
    "countryid": "661,662,916,668,669,670,671",
    "authentication_key": "1337662098",
    "error_code": "0",
    "error_txt": "Transaction successful",
}


GET_OPERATORS_RESPONSE_DICT = {
    "country": "Indonesia",
    "countryid": "767",
    "operator": "Indosat Starone Indonesia,Telkom Flexi Indonesia,"
    "Indosat IM3 Indonesia,"
    "AAA-TESTING Indone- sia,Esia Bakrie Telecom Indonesia,"
    "Indosat Mentari Indonesia,Telkomsel Simpati Indonesia,"
    "Three Telecom Indonesia,Telkomsel KartuAS Indonesia,Excelcom Indonesia,"
    "Axis Indonesia",
    "operatorid": "1320,1322,1313,1310,1326,1312,1324,1327,1325,215,1411",
    "authentication_key": "1337662386",
    "error_code": "0",
    "error_txt": "Transaction successful",
}


GET_OPERATOR_AIRTIME_PRODUCTS_RESPONSE_DICT = {
    "country": "Indonesia",
    "countryid": "767",
    "operator": "Indosat IM3 Indonesia",
    "operatorid": "1313",
    "destination_currency": "IDR",
    "product_list": "5000,10000,20000,25000,50000,100000",
    "wholesale_price_list": "0.85,1.28,2.98,5.53,11.05",
    "retail_price_list": "1.00,1.50,3.50,6.50,13.00",
    "authentication_key": "1337662386",
    "error_code": "0",
    "error_txt": "Transaction successful",
}

GET_COUNTRY_SERVICES_RESPONSE_DICT = {
    "services": [{"service_id": 7, "service": "bundles"}]
}

GET_PRODUCTS_RESPONSE_DICT = {
    "fixed_value_vouchers": [],
    "fixed_value_recharges": [
        {
            "product_id": 1234,
            "product_name": "Gig 1 - ZAR 100",
            "product_short_desc": "1GB / 30 Days",
            "operator_id": 222,
            "operator": "MNO South Africa",
            "country_id": 111,
            "country": "South Africa",
            "service_id": 111111,
            "service": "bundles",
            "account_currency": "ZAR",
            "wholesale_price": 99.99,
            "retail_price": 222.22,
            "fee": 0,
            "product_currency": "ZAR",
            "product_value": 111,
            "local_currency": "ZAR",
            "local_value": 111,
        },
        {
            "product_id": 1235,
            "product_name": "MyGig 2 - ZAR 555",
            "product_short_desc": "2GB / 30 Days",
            "operator_id": 222,
            "operator": "MNO South Africa",
            "country_id": 111,
            "country": "South Africa",
            "service_id": 0,
            "service": "bundles",
            "account_currency": "ZAR",
            "wholesale_price": 277.77,
            "retail_price": 333.33,
            "fee": 0,
            "product_currency": "ZAR",
            "product_value": 333,
            "local_currency": "ZAR",
            "local_value": 333,
        },
    ],
    "variable_value_payments": [],
    "fixed_value_payments": [],
    "variable_value_vouchers": [],
    "variable_value_recharges": [],
}

POST_TOPUP_DATA_RESPONSE = {
    "transaction_id": "1234567",
    "simulation": 0,
    "status": "0",
    "status_message": "Transaction successful",
    "date": "2018-09-14 10:40:19",
    "account_number": "2782000000",
    "external_id": "12345678",
    "operator_reference": "OPERTRREF009",
    "product_id": "1234",
    "product": "Gig 1 - ZAR 100",
    "product_desc": "1GB / 30 Days",
    "product_currency": "ZAR",
    "product_value": 29,
    "local_currency": "ZAR",
    "local_value": 29,
    "operator_id": "222",
    "operator": "MNO South Africa",
    "country_id": "222",
    "country": "South Africa",
    "account_currency": "ZAR",
    "wholesale_price": 30.77,
    "retail_price": 38.46,
    "fee": 0,
    "sender": {
        "last_name": "",
        "middle_name": "",
        "first_name": "",
        "email": "",
        "mobile": "876000",
        "custom_field_1": "",
        "custom_field_2": "",
        "custom_field_3": "",
    },
    "recipient": {
        "last_name": "",
        "middle_name": "",
        "first_name": "",
        "email": "",
        "mobile": "2782000000",
        "custom_field_1": "",
        "custom_field_2": "",
        "custom_field_3": "",
    },
    "sender_sms_notification": 1,
    "sender_sms_text": "Sender message",
    "recipient_sms_notification": 1,
    "recipient_sms_text": "Recipient SMS",
    "custom_field_1": "",
    "custom_field_2": "",
    "custom_field_3": "",
}

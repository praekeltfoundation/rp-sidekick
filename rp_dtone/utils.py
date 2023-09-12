from .models import Transaction


def send_airtime(org_id, client, msisdn, value):
    transaction = Transaction.objects.create(org_id=org_id, msisdn=msisdn, value=value)
    transaction.operator_id = client.get_operator_id(msisdn)
    if not transaction.operator_id:
        transaction.status = Transaction.Status.OPERATOR_NOT_FOUND
        transaction.save()
        return False, transaction.uuid

    transaction.product_id = client.get_fixed_value_product(
        transaction.operator_id, value
    )
    if not transaction.product_id:
        transaction.status = Transaction.Status.PRODUCT_NOT_FOUND
        transaction.save()
        return False, transaction.uuid

    response = client.submit_transaction(
        transaction.uuid, msisdn, transaction.product_id
    )
    if response.status_code == 201:
        transaction.status = Transaction.Status.SUCCESS
    else:
        transaction.status = Transaction.Status.ERROR
        transaction.response = response.json()

    transaction.save()
    return transaction.status == Transaction.Status.SUCCESS, transaction.uuid

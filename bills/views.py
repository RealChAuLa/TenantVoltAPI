from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json
import logging
from datetime import datetime, timezone
from TenantVoltAPI.firebase_config import initialize_firebase
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@csrf_exempt
def send_bill_notification(request):
    """
    Find tenant by product_id and send bill notification email

    Expected POST body:
    {
        "product_id": "1112",
        "month": "2025-02",  # Format: YYYY-MM
        "amount": 1250.00,
        "kw_value": 650
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Parse request body
        body_data = request.body
        data = json.loads(body_data.decode('utf-8'))

        # Validate required fields
        required_fields = ['product_id', 'month', 'amount', 'kw_value']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)

        # Extract data
        product_id = data.get('product_id')
        month_code = data.get('month')
        amount = data.get('amount')
        kw_value = data.get('kw_value')

        # Format month for display (convert YYYY-MM to Month YYYY)
        try:
            month_date = datetime.strptime(month_code, "%Y-%m")
            formatted_month = month_date.strftime("%B %Y")  # e.g., "February 2025"
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid month format. Expected YYYY-MM'
            }, status=400)

        # Initialize Firebase
        _, firestore_db = initialize_firebase()

        # Query all house_owners to find the tenant with matching product_id
        house_owners = firestore_db.collection('house_owners').stream()

        tenant_email = None
        tenant_name = None
        owner_name = None
        property_address = None

        for house_owner in house_owners:
            owner_data = house_owner.to_dict()

            # Skip if no tenants field or not a list
            if 'tenants' not in owner_data or not isinstance(owner_data['tenants'], list):
                continue

            # Look for tenant with matching product_id
            for tenant in owner_data['tenants']:
                if tenant.get('product_id') == product_id:
                    tenant_email = tenant.get('email')
                    tenant_name = tenant.get('name', 'Valued Tenant')
                    owner_name = f"{owner_data.get('first_name', '')} {owner_data.get('last_name', '')}"
                    property_address = tenant.get('address', owner_data.get('address', 'your rental property'))
                    break

            # If tenant found, break the outer loop too
            if tenant_email:
                break

        # If no tenant found with matching product_id
        if not tenant_email:
            return JsonResponse({
                'success': False,
                'error': f'No tenant found with product_id: {product_id}'
            }, status=404)

        # Prepare email content
        subject = f"Electricity Bill Notification - {formatted_month}"

        email_body = f"""
Hello {tenant_name},

ELECTRICITY BILL NOTIFICATION

This is to inform you that your electricity bill for {formatted_month} is now available:

Property: {property_address}
Total Usage: {kw_value} kWh
Amount Due: ${amount:.2f}

Please make your payment at your earliest convenience to avoid any service interruption.

If you have any questions about this bill, please contact your property manager.

Best Regards,
{owner_name}
TenantVolt System
        """.strip()

        # Send email using Django's email functionality
        sent = send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[tenant_email],
            fail_silently=False,
        )

        if sent:
            # Log the email was sent
            logger.info(f"Bill notification email sent to {tenant_email} for product_id {product_id}")

            # Create record of this bill in Firestore (optional)
            bills_ref = firestore_db.collection('bills').document()
            bills_ref.set({
                'product_id': product_id,
                'tenant_email': tenant_email,
                'month': month_code,
                'amount': amount,
                'kw_value': kw_value,
                'notification_sent': True,
                'notification_date': datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            })

            return JsonResponse({
                'success': True,
                'message': f"Bill notification sent to {tenant_email}",
                'tenant': {
                    'email': tenant_email,
                    'name': tenant_name
                },
                'bill': {
                    'month': month_code,
                    'amount': amount,
                    'kw_value': kw_value
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to send email notification'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error sending bill notification: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)
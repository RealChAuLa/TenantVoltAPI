from datetime import datetime
from zoneinfo import ZoneInfo

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from TenantVoltAPI.firebase_config import initialize_firebase
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@csrf_exempt
def get_pending_orders(request):
    """
    Get all house_owners documents with order_status = "pending"

    Expected Response:
    {
        "success": true,
        "count": 2,
        "orders": [
            {
                "uid": "624PPp7PXnf3zzjBxtFHntSZcOq1",
                "owner": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "chalana2@gmail.com",
                    "mobile_number": "+1234567890",
                    "address": "123 Main St, City, Country"
                },
                "order_info": {
                    "order_status": "pending",
                    "order_date_time": "2025-03-31 21:37:44"
                },
                "tenants": [
                    {
                        "tenant_index": 0,
                        "name": "Alice Smith",
                        "email": "alice.smith@example.com",
                        "address": "456 Elm St, City, Country"
                    },
                    {
                    },....
                ]
            },
            {
                "uid": "EtrTQxBuBlRh7OJgzVdhOy04cD83",
                "owner": {
                    "first_name": "Chalana",
                    "last_name": "Doe",
                }
            }
        ]
    }
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Initialize Firebase
        _, firestore_db = initialize_firebase()

        # Query house_owners where order_status is "Pending"
        pending_orders = firestore_db.collection('house_owners').where('order_status', '==', 'pending').stream()

        # Format the results for UI use
        results = []
        for order in pending_orders:
            # Get the document data
            order_data = order.to_dict()
            uid = order.id

            # Create a structured object for the UI
            ui_order = {
                'uid': uid,
                'owner': {
                    'first_name': order_data.get('first_name', ''),
                    'last_name': order_data.get('last_name', ''),
                    'email': order_data.get('email', ''),
                    'mobile_number': order_data.get('mobile_number', ''),
                    'address': order_data.get('address', '')
                },
                'order_info': {
                    'order_status': order_data.get('order_status', 'pending'),
                    'order_date_time': order_data.get('order_date_time', '')
                },
                'tenants': []
            }

            # Process tenants with editable product_ids
            if 'tenants' in order_data and isinstance(order_data['tenants'], list):
                for i, tenant in enumerate(order_data['tenants']):
                    ui_tenant = {
                        'tenant_index': i,  # For tracking which tenant is updated
                        'name': tenant.get('name', ''),
                        'email': tenant.get('email', ''),
                        'address': tenant.get('address', '')
                    }
                    ui_order['tenants'].append(ui_tenant)

            results.append(ui_order)

        # Return the UI-friendly pending orders
        return JsonResponse({
            'success': True,
            'count': len(results),
            'orders': results,
        })

    except Exception as e:
        logger.error(f"Error getting pending orders: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)
@csrf_exempt
def update_order_status(request):
    """
    Update the order_status to "completed" and tenant product_ids

    Expected request body:
    {
        "uid": "firebase-user-id",
        "tenants": [
            {
                "tenant_index": 0,
                "product_id": "updated-product-id-1"
            },
            {
                "tenant_index": 1,
                "product_id": "updated-product-id-2"
            }
        ]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Initialize Firebase
        _, firestore_db = initialize_firebase()

        # Read request body
        body_data = request.body
        data = json.loads(body_data.decode('utf-8'))

        # Get required fields
        uid = data.get('uid')
        tenant_updates = data.get('tenants', [])

        # Validate inputs
        if not uid:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields',
                'message': 'uid is required'
            }, status=400)

        # Check if user exists
        house_owner_ref = firestore_db.collection('house_owners').document(uid)
        house_owner_doc = house_owner_ref.get()

        if not house_owner_doc.exists:
            return JsonResponse({
                'success': False,
                'error': 'Not found',
                'message': f'No house owner found with UID: {uid}'
            }, status=404)

        # Get current document data
        current_data = house_owner_doc.to_dict()

        # Prepare update data
        update_data = {'completed_at': datetime.now(ZoneInfo("Asia/Colombo")).strftime("%Y-%m-%d %H:%M:%S"),
                       'order_status': 'completed'}

        # Process tenant updates if tenants exist in the document
        if tenant_updates and 'tenants' in current_data and isinstance(current_data['tenants'], list):
            tenants = current_data['tenants']

            # Update each tenant's product_id
            for update in tenant_updates:
                tenant_index = update.get('tenant_index')
                product_id = update.get('product_id')

                # Validate index and product_id
                if tenant_index is not None and product_id is not None:
                    # Check if the index is valid
                    if 0 <= tenant_index < len(tenants):
                        # Update the product_id
                        tenants[tenant_index]['product_id'] = product_id

            # Add updated tenants to the update data
            update_data['tenants'] = tenants

        # Update the document in Firestore
        house_owner_ref.update(update_data)

        # Return success response with updated data
        return JsonResponse({
            'success': True,
            'message': 'Order updated successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error updating order: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def get_completed_orders(request):
    """
    Get all house_owners documents with order_status = "completed"

    Expected Response:
    {
        "success": true,
        "count": 2,
        "orders": [
            {
                "uid": "624PPp7PXnf3zzjBxtFHntSZcOq1",
                "owner": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "chalana2@gmail.com",
                    "mobile_number": "+1234567890",
                    "address": "123 Main St, City, Country"
                },
                "order_info": {
                    "order_status": "completed",
                    "order_date_time": "2025-03-31 21:37:44"
                },
                "tenants": [
                    {
                        "tenant_index": 0,
                        "name": "Alice Smith",
                        "email": "alice.smith@example.com",
                        "address": "456 Elm St, City, Country"
                    },
                    {
                    },....
                ]
            },
            {
                "uid": "EtrTQxBuBlRh7OJgzVdhOy04cD83",
                "owner": {
                    "first_name": "Chalana",
                    "last_name": "Doe",
                }
            }
        ]
    }
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Initialize Firebase
        _, firestore_db = initialize_firebase()

        # Query house_owners where order_status is "completed"
        completed_orders = firestore_db.collection('house_owners').where('order_status', '==', 'completed').stream()

        # Format the results for UI use
        results = []
        for order in completed_orders:
            # Get the document data
            order_data = order.to_dict()
            uid = order.id

            # Create a structured object for the UI
            ui_order = {
                'uid': uid,
                'owner': {
                    'first_name': order_data.get('first_name', ''),
                    'last_name': order_data.get('last_name', ''),
                    'email': order_data.get('email', ''),
                    'mobile_number': order_data.get('mobile_number', ''),
                    'address': order_data.get('address', '')
                },
                'order_info': {
                    'order_status': order_data.get('order_status', ''),
                    'order_date_time': order_data.get('order_date_time', '')
                },
                'tenants': []
            }

            # Process tenants with editable product_ids
            if 'tenants' in order_data and isinstance(order_data['tenants'], list):
                for i, tenant in enumerate(order_data['tenants']):
                    ui_tenant = {
                        'tenant_index': i,  # For tracking which tenant is updated
                        'name': tenant.get('name', ''),
                        'email': tenant.get('email', ''),
                        'address': tenant.get('address', '')
                    }
                    ui_order['tenants'].append(ui_tenant)

            results.append(ui_order)

        # Return the UI-friendly completed orders
        return JsonResponse({
            'success': True,
            'count': len(results),
            'orders': results,
        })

    except Exception as e:
        logger.error(f"Error getting completed orders: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)

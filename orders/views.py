from datetime import datetime

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
    Get all house_owners documents with order_status = "Pending"
    Returns a list of house owners with their UIDs and other details
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Initialize Firebase
        _, firestore_db = initialize_firebase()

        # Query house_owners where order_status is "Pending"
        pending_orders = firestore_db.collection('house_owners').where('order_status', '==', 'pending').stream()

        # Format the results
        results = []
        for order in pending_orders:
            # Get the document data
            order_data = order.to_dict()

            # Add the UID to the data
            order_data['uid'] = order.id

            # Add to results
            results.append(order_data)

        # Return the pending orders
        return JsonResponse({
            'success': True,
            'count': len(results),
            'orders': results
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
    Update the order_status for a house_owner

    Expected request body:
    {
        "uid": "firebase-user-id",
        "order_status": "Completed" (or any other status)
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
        new_status = data.get('order_status')

        # Validate inputs
        if not uid or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields',
                'message': 'Both uid and order_status are required'
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

        # Update the order status
        house_owner_ref.update({
            'order_status': new_status
        })

        # Get the updated document
        updated_doc = house_owner_ref.get().to_dict()

        # Return success response
        return JsonResponse({
            'success': True,
            'message': f'Order status updated to {new_status}',
            'uid': uid,
            'updated_data': updated_doc
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }, status=500)
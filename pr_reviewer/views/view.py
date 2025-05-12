from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path 
import base64
import binascii

from pr_reviewer.views.bitbucket_view import get_pr_detail, on_filter

@csrf_exempt
@require_POST
def api_view_pull_request(request):
    username = None
    password = None

    # --- 1. Decode Basic Auth Credentials ---
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return JsonResponse({'detail': 'Missing or invalid Authorization header'}, status=401)

    try:
        encoded_credentials = auth_header.split(' ')[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
    except Exception:
        return JsonResponse({'detail': 'Invalid Authorization header format'}, status=400)

    # --- 2. Parse Request Body ---
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    # --- 3. Extract Fields ---
    min_approval = data.get('min_approval')
    min_default_reviewer_approval = data.get('min_default_reviewer_approval')

    workspace = data.get('workspace')
    report_in = data.get('report_in')
    status = data.get('status')
    target_branch = data.get('target_branch')
    enforced_rule = data.get('enforced_rule')
    page_size = data.get('page_size')
    requested_from = data.get('request_from')
    requested_to = data.get('request_to')
    merged_from = data.get('merged_from')
    merged_to = data.get('merged_to')

    # Append time range if dates are present
    if requested_from:
        requested_from += " 00:00:00"
    if requested_to:
        requested_to += " 23:59:59"
    if merged_from:
        merged_from += " 00:00:00"
    if merged_to:
        merged_to += " 23:59:59"

    # --- 4. Required Fields Validation ---
    if not workspace:
        return JsonResponse({'error': 'Workspace field is required!'}, status=400)
    if not report_in:
        return JsonResponse({'error': 'Report In field is required!'}, status=400)
    if not status:
        return JsonResponse({'error': 'Status field is required!'}, status=400)
    if not page_size:
        return JsonResponse({'error': 'Page Size field is required!'}, status=400)
    if not enforced_rule:
        return JsonResponse({'error': 'Enforced Rule field is required!'}, status=400)

    # --- 5. Main Logic ---
    try:
        get_detail_response = get_pr_detail(workspace, report_in, status, page_size, username, password)
        filtered_result = on_filter(
            get_detail_response,
            workspace,
            status,
            target_branch,
            enforced_rule,
            requested_from,
            requested_to,
            merged_from,
            merged_to,
            report_in,
            min_approval,
            min_default_reviewer_approval,
            username,
            password
        )
        return JsonResponse({'data': filtered_result}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


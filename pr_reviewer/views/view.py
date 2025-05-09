
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path 

from pr_reviewer.views.bitbucket_view import get_pr_detail, on_filter

@csrf_exempt
@require_POST
def api_view_pull_request(request):
    try:
        data = json.loads(request.body)

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

        # Append time range to dates if provided
        if requested_from:
            requested_from += " 00:00:00"
        if requested_to:
            requested_to += " 23:59:59"
        if merged_from:
            merged_from += " 00:00:00"
        if merged_to:
            merged_to += " 23:59:59"

        # Required fields validation
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

        # Main logic
        get_detail_response = get_pr_detail(workspace, report_in, status, page_size)
        filtered_result = on_filter(
            get_detail_response,
            status,
            target_branch,
            enforced_rule,
            requested_from,
            requested_to,
            merged_from,
            merged_to,
            report_in
        )

        print("get detail response")
        return JsonResponse({'data': filtered_result}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / 'config.json' 

@csrf_exempt
@require_POST
def config_workspace(request):
    data = json.loads(request.body)
    workspace = data.get('workspace')
    action = data.get('action')

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    if action == 'create':
        if workspace not in config["workspace_list"]:
            config["workspace_list"].append(workspace)
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"{workspace} added to workspace_list.")
        else:
            print(f"{workspace} already exists.")

    elif action == 'delete':
        if workspace in config["workspace_list"]:
            config["workspace_list"].remove(workspace)
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"{workspace} removed from workspace_list.")
        else:
            print(f"{workspace} does not exist.")

    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)

    return JsonResponse({'result': 'success'}, status=200)

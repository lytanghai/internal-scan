from django.shortcuts import render
from django.http import JsonResponse
import requests
import json
from pr_reviewer.util.date import format_date_time
from datetime import datetime, timedelta
from pathlib import Path 
from requests.auth import HTTPBasicAuth
from django.views.decorators.csrf import csrf_exempt
import base64
import binascii

def index(request):
    return render(request, 'index.html')

def get_default_reviewer(workspace, repo_slug, username, password):
    default_reviewers = []

    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/default-reviewers"

    username = username.strip().strip('"')
    password = password.strip().strip('"')
    response = requests.get(url, auth=HTTPBasicAuth(username, password))
    if response.status_code == 200:
        response_data = response.json()
        
        for value in response_data.get('values', []):
            display_name = value.get("display_name", "No Display Name")
            default_reviewers.append(display_name)
    
    return default_reviewers

@csrf_exempt
def get_repository(request, workspace):
    # 1. Extract credentials from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return JsonResponse({'detail': 'Missing or invalid Authorization header'}, status=401)
    try:
        encoded_credentials = auth_header.split(' ')[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
    except Exception:
        return JsonResponse({'detail': 'Invalid Authorization header format'}, status=400)

    if workspace == 'default':
        pass 

    # 2. Make Bitbucket API call with provided credentials
    print(f"workspace {workspace}" )
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"
    username = username.strip().strip('""')
    password = password.strip().strip('""')
    response = requests.get(url, auth=HTTPBasicAuth(username, password))

    if response.status_code == 200:
        data = response.json()
        repository_names = [repo['name'].lower().replace(" ", "-") for repo in data['values']]
        return JsonResponse({'repositories': repository_names})
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return JsonResponse({'repositories': []}, status=500)


def get_pr_detail(workspace, repo_slug, status, page_size, username, password):
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests?pagelen={page_size}&state={status}"
    username = username.strip().strip('"')
    password = password.strip().strip('"')
    response = requests.get(url, auth=HTTPBasicAuth(username, password))
    if response.status_code == 200:
        return response.json()
    else:
        return []

def check_enforce_rule(id, default_reviewers, workspace,report_slug, total_approvals, total_default_reviewer_approvals, username, password):
    result = False
    default_approvals = 0
    total_approvals = 0

    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{report_slug}/pullrequests/{id}"

    username = username.strip().strip('"')
    password = password.strip().strip('"')
    response = requests.get(url, auth=HTTPBasicAuth(username, password))
    print(f"📡 Calling to fetch pull request detail by ID: {url}")

    if response.status_code == 200:
        data = response.json()
        participants = data.get("participants", [])

        for participant in participants:
            reviewer_name = participant["user"]["display_name"]
            is_approve = participant.get("approved", False)

            if is_approve:
                total_approvals += 1
                if reviewer_name in default_reviewers:
                    default_approvals += 1
                    print(f"✅ Default reviewer '{reviewer_name}' approved the PR.")
                else:
                    print(f"✅ Non-default reviewer '{reviewer_name}' approved the PR.")

        if total_approvals >= total_approvals and default_approvals >= total_default_reviewer_approvals:
            result = True
        else:
            print(f"⚠️ Enforcement rule not met: {total_approvals} approvals "
                      f"({default_approvals} from default reviewers).")
    else:
        print(f"❌ Failed to retrieve PR data. Status code: {response.status_code}")

    return result, total_approvals, default_approvals

def on_filter(get_detail_response, workspace, status, target_branch, enforced_rule, requested_from, requested_to, merged_from, merged_to, repo_slug, min_approval, min_default_reviewer_approval, username, password):
    if isinstance(get_detail_response, str):
        json_data = json.loads(get_detail_response)
    else:
        json_data = get_detail_response

    print("f workspaceworkspace {workspace}")
    default_reviewers = get_default_reviewer(workspace, repo_slug, username,password)

    result = []
    for pr in json_data.get("values", []):
        closed_by = pr["closed_by"]["display_name"] if isinstance(pr.get("closed_by"), dict) else ""
        id = pr.get("id", "")

        print(f'testing {min_approval} {min_default_reviewer_approval}')
        enforced_rule_res, total_approvals, total_default_reviewer_approvals = check_enforce_rule(
            id,
            default_reviewers,
            workspace,
            repo_slug,
            int(min_approval),
            int(min_default_reviewer_approval),
            username,
            password
        )

        if enforced_rule == 'All': 
            pass

        elif enforced_rule == 'True' and not enforced_rule_res:
            continue 
            
        elif enforced_rule == 'False' and enforced_rule_res:
            continue 

        response_state = pr.get("state", "")
        if status.lower() != "all" and status.upper() != response_state.upper():
            continue

        destination_branch = pr.get("destination", {}).get("branch", {}).get("name", "")
        if target_branch and destination_branch != target_branch:
            continue

        created_on = pr.get("created_on", "")
        if created_on:
            created_dt = datetime.fromisoformat(created_on.replace('Z', '+00:00'))

            if requested_from:
                requested_from_dt = datetime.strptime(requested_from, "%Y-%m-%d %H:%M:%S")
                if created_dt.date() < requested_from_dt.date():
                    continue

            if requested_to:
                requested_to_dt = datetime.strptime(requested_to, "%Y-%m-%d %H:%M:%S")
                if created_dt.date() > requested_to_dt.date():
                    continue

        # Apply merged date filter if PR is merged
        if response_state == "MERGED":
            updated_on = pr.get("updated_on", "")
            if updated_on:
                updated_dt = datetime.fromisoformat(updated_on.replace('Z', '+00:00'))

                if merged_from:
                    merged_from_dt = datetime.strptime(merged_from, "%Y-%m-%d %H:%M:%S")
                    if updated_dt.date() < merged_from_dt.date():
                        continue

                if merged_to:
                    merged_to_dt = datetime.strptime(merged_to, "%Y-%m-%d %H:%M:%S")
                    if updated_dt.date() > merged_to_dt.date():
                        continue
        rule_detail = f"{total_approvals} approval \n{total_default_reviewer_approvals} default reviewer"
        pr_info = {
            "id": id,
            "title": pr.get("title", ""),
            "state": response_state,
            "source_branch":pr.get("source", {}).get("branch", {}).get("name", ""),
            "target_branch": pr.get("destination", {}).get("branch", {}).get("name", ""),
            "author": pr.get("author", {}).get("display_name", ""),
            "created_on": pr.get("created_on", ""),
            "closed_by": closed_by,
            "updated_on": pr.get("updated_on", ""),
            "enforced_rule": enforced_rule_res,
            "pr_rule": rule_detail
        }
        result.append(pr_info)
    return result
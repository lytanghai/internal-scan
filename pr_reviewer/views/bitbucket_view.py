from django.shortcuts import render
from django.http import JsonResponse
from internal_scan.config_loader import config
from pr_reviewer.util.cache import set_cache, get_cache
import requests
import json
from pr_reviewer.util.date import format_date_time
from datetime import datetime, timedelta
from pathlib import Path 
from requests.auth import HTTPBasicAuth

# -- get config json ---
def get_config(request):
    config_path = Path(__file__).resolve().parent.parent.parent / 'config.json' 
    data = None
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    if data:
        keys_to_include = ['workspace_list']
        response_data = {key: data[key] for key in keys_to_include if key in data}
    else:
        response_data = {}
    return JsonResponse(response_data)

# -- render html page ---
def index(request):
    return render(request, 'index.html')

def get_default_reviewer():
    default_reviewers = []

    if get_cache('default_reviewer'):
        print('get cache')
        return get_cache('default_reviewer')

    url = f"https://api.bitbucket.org/2.0/repositories/wingdev/resilience-sample/default-reviewers"
    print("calling to get default reviewer")
    response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['app_password']))

    if response.status_code == 200:
        response_data = response.json()
        
        for value in response_data.get('values', []):
            display_name = value.get("display_name", "No Display Name")
            default_reviewers.append(display_name)
    
    set_cache("default_reviewer", default_reviewers)
    return default_reviewers

def get_repository(request, workspace):
    if workspace == 'default':
        pass
    cache_name = "repository_name_" + workspace
    
    cached_data = get_cache(cache_name)
    if cached_data:
        return JsonResponse({'repositories': cached_data})
    
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"
    
    print("calling to get repositoy")
    response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['app_password']))
    
    if response.status_code == 200:
        data = response.json()
        repository_names = [repo['name'].lower().replace(" ", "-") for repo in data['values']]
        set_cache(cache_name, repository_names)
        print("success")
        return JsonResponse({'repositories': repository_names})  # ✅ wrap in dict
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return JsonResponse({'repositories': []}, status=500)  # ✅ return valid JSON even on failure


def get_pr_detail(workspace, repo_slug, status, page_size):
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests?pagelen={page_size}&state={status}"
    response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['app_password']))
    if response.status_code == 200:
        return response.json()
    else:
        return []

def check_enforce_rule(id, default_reviewers, report_slug, total_approvals, total_default_reviewer_approvals):
    result = False
    default_approvals = 0
    total_approvals = 0

    url = f"https://api.bitbucket.org/2.0/repositories/wingdev/{report_slug}/pullrequests/{id}"

    print("calling to get pull request detail")
    response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['app_password']))
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

def on_filter(get_detail_response, status, target_branch, enforced_rule, requested_from, requested_to, merged_from, merged_to, repo_slug):
    print(f"VALUE OF TARGET BRANCH {target_branch}")
    if isinstance(get_detail_response, str):
        json_data = json.loads(get_detail_response)
    else:
        json_data = get_detail_response

    default_reviewers = get_cache('default_reviewer')
    if default_reviewers is None:
        default_reviewers = get_default_reviewer()
    else:
        print("Loaded cache default reviewer from cache!")

    result = []
    min_approval = config['min_approval']
    min_default_reviewer_approval = config['min_default_reviewer_approval']
    for pr in json_data.get("values", []):
        closed_by = pr["closed_by"]["display_name"] if isinstance(pr.get("closed_by"), dict) else ""
        id = pr.get("id", "")

        enforced_rule_res, total_approvals, total_default_reviewer_approvals = check_enforce_rule(
            id,
            default_reviewers,
            repo_slug,
            int(min_approval),
            int(min_default_reviewer_approval)
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
    # global on_result_export
    # on_result_export = result
    print(f"FINAL RESULT: {result}")
    return result
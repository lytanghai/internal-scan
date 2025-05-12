export_exc = []
let workspaces = []

document.getElementById("target_branch").addEventListener("change", function () {
  const targetBranchOther = document.getElementById("target_branch_other");
  targetBranchOther.style.display = this.value === "other" ? "inline-block" : "none";
});

//change to list cookie with value of workspace_lists intead so we don't need this any more
document.addEventListener('DOMContentLoaded', function () {
  const workspaceCookie = getCookie("workspace_list");
  let workspaces = [];

  try {
    workspaces = JSON.parse(workspaceCookie);
  } catch (e) {
    console.error("Invalid or missing workspace_list cookie", e);
    return;
  }

  const select = document.getElementById("workspace");

  workspaces.forEach(workspace => {
    const option = document.createElement("option");
    option.value = workspace;
    option.textContent = workspace;
    select.appendChild(option);
  });

  select.addEventListener('change', function () {
    const selectedWorkspace = select.value;
    console.log('Selected workspace:', selectedWorkspace);

    fetch_repo(selectedWorkspace);
  });

  function fetch_repo(workspace) {

    const username = getCookie('username');
    const password = getCookie('password');
    const basicAuth = btoa(`${username}:${password}`); // base64 encode

    fetch(`/pull_request/api/${workspace}/`, {
      method: "GET",
      headers: {
        "Authorization": `Basic ${basicAuth}`,
        "Content-Type": "application/json"
      }
    })
      .then(response => response.json())
      .then(data => {
        const repos = data.repositories || [];
        const reportSelect = document.getElementById("report");

        reportSelect.innerHTML = "";

        const defaultOption = document.createElement("option");
        defaultOption.textContent = "-- Select Repository --";
        defaultOption.value = "null";
        defaultOption.disabled = true;
        defaultOption.selected = true;
        reportSelect.appendChild(defaultOption);

        repos.forEach(repo => {
          const option = document.createElement("option");
          option.value = repo;
          option.textContent = repo;
          reportSelect.appendChild(option);
        });
      })
      .catch(error => {
        console.error("Failed to fetch repositories:", error);
      });
  }

});

document.getElementById("export_data").addEventListener("click", function () {
  exportToExcel(export_exc, "tanghai.ly");
})
document.getElementById("apply_filter").addEventListener("click", async function () {

  const button = document.getElementById("apply_filter");
  button.disabled = true;

  const fields = {
    workspace: document.getElementById("workspace").value,
    report_in: document.getElementById("report").value,
    status: document.getElementById("status").value,
    target_branch: document.getElementById("target_branch").value,
    enforced_rule: document.getElementById("enforced_rule").value,
    page_size: document.getElementById("page_size").value,
    request_from: document.getElementById("requested_from").value,
    request_to: document.getElementById("requested_to").value,
    merged_from: document.getElementById("merged_from").value,
    merged_to: document.getElementById("merged_to").value,
  };

  // Override target_branch if 'other' is selected
  if (fields.target_branch === "other") {
    const customBranch = document.getElementById("target_branch_other");
    if (customBranch && customBranch.value) {
      fields.target_branch = customBranch.value;
    }
  }

  // Validate required fields
  const requiredFields = ["workspace", "report", "page_size"];
  let isValid = true;
  let firstInvalidField = null;

  requiredFields.forEach(id => {
    const field = document.getElementById(id);
    if (!field || !field.value || field.value === "default" || field.value === 'null') {
      isValid = false;
      field.classList.add("warning-border");
      if (!firstInvalidField) {
        firstInvalidField = field;
      }
    } else {
      field.classList.remove("warning-border");
    }
  });

  if (!isValid) {
    alert("Please fill in all required fields.");
    if (firstInvalidField) firstInvalidField.focus();
    button.disabled = false;
    return;
  }

  const requestBody = {};
  for (const [key, value] of Object.entries(fields)) {
    if (value !== "") {
      requestBody[key] = value;
    }
  }

  showLoader();

  const username = getCookie('username');
  const password = getCookie('password');
  const basicAuth = btoa(`${username}:${password}`);
  requestBody["min_approval"] = getCookieWithDefault("min_approval", 2);
  requestBody["min_default_reviewer_approval"] = getCookieWithDefault("min_default_reviewer_approval", 2);
  fetch('/pull_request/api/filter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      "Authorization": `Basic ${basicAuth}`,
    },
    body: JSON.stringify(requestBody)
  })
    .then(response => response.json())
    .then(data => {
      const resultList = data.data || [];
      displayResultCount(resultList.length);
      console.log("Fetched data:", resultList);

      const tbody = document.querySelector("#pull_tbl tbody");
      if (!tbody) {
        console.error("Table body not found");
        hideLoader();
        button.disabled = false;
        return;
      }

      export_exc = resultList;
      console.log("Fetched export_exc:", export_exc);
      tbody.innerHTML = ""; // Clear table

      resultList.forEach(pr => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${pr.id}</td>
          <td>${pr.title}</td>
          <td>${pr.source_branch}</td>
          <td>${pr.target_branch}</td>
          <td>${pr.state}</td>
          <td>${pr.author || "-"}</td>
          <td>${new Date(pr.created_on).toLocaleString()}</td>
          <td>${pr.closed_by || "-"}</td>
          <td>${new Date(pr.updated_on).toLocaleString()}</td>
          <td>${pr.enforced_rule ? "Yes" : "No"}</td>
          <td style="text-align:left">${pr.pr_rule.replace(/\n/g, "<br>")}</td>
        `;
        tbody.appendChild(row);
      });

      hideLoader();
      button.disabled = false;
    })
    .catch(error => {
      console.error("Fetch error:", error);
      hideLoader();
      button.disabled = false;
    });
});

// Create a new workspace
export_exc = []
let workspaces = []

// document.getElementById("workspace").addEventListener("change", function () {
//   const otherInput = document.getElementById("workspace_other");
//   const createBtn = document.getElementById("create_workspace_btn");

//   if (this.value === "default") {
//     otherInput.style.display = "inline-block";
//     createBtn.style.display = "inline-block";
//   } else {
//     otherInput.style.display = "none";
//     createBtn.style.display = "none";
//   }
// });

//change to add or delete cookie so we don't need this any more
function createWorkspace(workspaceValue, actionValue , onSuccess, onError) {
  if (!workspaceValue.trim()) {
    alert("Please enter a workspace name.");
    if (onError) onError("Workspace name is empty");
    return;
  }
//change to get cookie so we don't need this any more
  fetch('/pull_request/api/workspace/config', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ workspace: workspaceValue, action: actionValue }),
  })
    .then(response => response.json())
    .then(data => {
      console.log("Created workspace:", data);
      if (onSuccess) onSuccess(data);
    })
    .catch(error => {
      console.error("Error creating workspace:", error);
      alert("Failed to create workspace.");
      if (onError) onError(error);
    });
}

document.getElementById("create_workspace_btn").addEventListener("click", function (e) {
  // e.preventDefault();
  const workspaceValue = document.getElementById("workspace_other").value.trim();

  createWorkspace(workspaceValue, 'create' , (data) => {
    alert("Workspace created successfully!");

    const select = document.getElementById("workspace");
    const newOption = document.createElement("option");
    newOption.value = workspaceValue;
    newOption.text = workspaceValue;
    select.appendChild(newOption);
    select.value = workspaceValue;

    document.getElementById("workspace_other").style.display = "none";
    document.getElementById("create_workspace_btn").style.display = "none";
  });
});

if(document.getElementById("delete_workspace_btn") !== null) {
  document.getElementById("delete_workspace_btn").addEventListener("click", function (e) {
    e.preventDefault();
    const workspaceValue = document.getElementById("workspace_other").value.trim();
  
    createWorkspace(workspaceValue, 'delete' , (data) => {
      alert("Workspace delete successfully!");
  
      const select = document.getElementById("workspace");
      const newOption = document.createElement("option");
      newOption.value = workspaceValue;
      newOption.text = workspaceValue;
      select.appendChild(newOption);
      select.value = workspaceValue;
  
      document.getElementById("workspace_other").style.display = "none";
      document.getElementById("create_workspace_btn").style.display = "none";
    });
  });
}

document.getElementById("target_branch").addEventListener("change", function () {
  const targetBranchOther = document.getElementById("target_branch_other");
  targetBranchOther.style.display = this.value === "other" ? "inline-block" : "none";
});

//change to list cookie with value of workspace_lists intead so we don't need this any more
document.addEventListener('DOMContentLoaded', function () {
  fetch("/pull_request/api/config/")
    .then(response => response.json())
    .then(data => {
      console.log('Full data object:', data);
      workspaces = data.workspace_list || [];

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
    })
    .catch(error => {
      console.error("Failed to load config:", error);
    });

    //must input username and password
  function fetch_repo(workspace) {
    fetch(`/pull_request/api/${workspace}/`)
      .then(response => response.json())
      .then(data => {
        const repos = data.repositories || [];
        const reportSelect = document.getElementById("report");

        // Clear previous options
        reportSelect.innerHTML = "";

        // Add a default option
        const defaultOption = document.createElement("option");
        defaultOption.textContent = "-- Select Repository --";
        defaultOption.value = "null"
        defaultOption.disabled = true;
        defaultOption.selected = true;
        reportSelect.appendChild(defaultOption);

        // Add options from the fetched repo list
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
  console.warn("Calling to get filter (POST)");

      //must input username and password

  fetch('/pull_request/api/filter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
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
          <td>${pr.pr_rule.replace(/\n/g, "<br>")}</td>
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
